import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from app.services.openrouter import call_openrouter


class FakeRedis:
    """In-memory stand-in for redis.asyncio.Redis, tracking key -> value with no real TTL enforcement.
    Tests simulate expiry by calling `expire_now(key)` instead of waiting."""

    def __init__(self):
        self.store: dict[str, str] = {}
        self.set_calls: list[tuple[str, str, int | None]] = []

    async def exists(self, key: str) -> int:
        return 1 if key in self.store else 0

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value
        self.set_calls.append((key, value, ex))

    def expire_now(self, key: str) -> None:
        self.store.pop(key, None)

    async def aclose(self) -> None:
        pass


@pytest.fixture
def fake_redis():
    fake = FakeRedis()
    with patch("app.services.openrouter._get_redis", return_value=fake):
        yield fake


@pytest.fixture(autouse=True)
def patch_api_key():
    with patch("app.services.openrouter.settings.openrouter_api_key", "test-key"):
        yield


def _mock_response(status_code: int, json_body: dict | None = None, text: str = ""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {}
    resp.text = text
    return resp


def _success_body(content: str = "hello") -> dict:
    return {"choices": [{"message": {"content": content}}]}


@pytest.mark.asyncio
async def test_failing_model_marked_down_and_skipped(fake_redis):
    responses = [
        _mock_response(429, text="rate limited"),
        _mock_response(200, _success_body("from model B")),
    ]

    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=responses)):
        data, model, error = await call_openrouter(
            ["model-a", "model-b"], lambda m: {"model": m}, timeout=10
        )

    assert model == "model-b"
    assert data["choices"][0]["message"]["content"] == "from model B"
    assert await fake_redis.exists("openrouter:model_down:model-a") == 1

    # Second call: model-a should be skipped entirely (no HTTP call for it)
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_mock_response(200, _success_body("again")))) as mock_post:
        data2, model2, _ = await call_openrouter(
            ["model-a", "model-b"], lambda m: {"model": m}, timeout=10
        )

    assert model2 == "model-b"
    assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_mark_model_down_sets_configured_cooldown_ttl(fake_redis):
    from app.config import settings

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_mock_response(429, text="rate limited"))):
        await call_openrouter(["model-a"], lambda m: {"model": m}, timeout=10)

    assert fake_redis.set_calls == [("openrouter:model_down:model-a", "1", settings.openrouter_model_cooldown_seconds)]


@pytest.mark.asyncio
async def test_model_retried_after_cooldown_expires(fake_redis):
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_mock_response(500, text="server error"))):
        await call_openrouter(["model-a"], lambda m: {"model": m}, timeout=10)

    assert await fake_redis.exists("openrouter:model_down:model-a") == 1

    fake_redis.expire_now("openrouter:model_down:model-a")

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_mock_response(200, _success_body("recovered")))) as mock_post:
        data, model, error = await call_openrouter(["model-a"], lambda m: {"model": m}, timeout=10)

    assert model == "model-a"
    assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_auth_error_does_not_mark_model_down(fake_redis):
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_mock_response(401, text="unauthorized"))):
        data, model, error = await call_openrouter(["model-a"], lambda m: {"model": m}, timeout=10)

    assert data is None
    assert await fake_redis.exists("openrouter:model_down:model-a") == 0


@pytest.mark.asyncio
async def test_bad_request_does_not_mark_model_down(fake_redis):
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_mock_response(400, text="bad request"))):
        await call_openrouter(["model-a"], lambda m: {"model": m}, timeout=10)

    assert await fake_redis.exists("openrouter:model_down:model-a") == 0


@pytest.mark.asyncio
async def test_all_models_down_fails_fast_without_http_call(fake_redis):
    await fake_redis.set("openrouter:model_down:model-a", "1")
    await fake_redis.set("openrouter:model_down:model-b", "1")

    with patch("httpx.AsyncClient.post", new=AsyncMock()) as mock_post:
        data, model, error = await call_openrouter(
            ["model-a", "model-b"], lambda m: {"model": m}, timeout=10
        )

    assert data is None
    assert model is None
    assert error == "All models are currently unavailable"
    mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_timeout_marks_model_down(fake_redis):
    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=httpx.TimeoutException("timed out"))):
        data, model, error = await call_openrouter(["model-a"], lambda m: {"model": m}, timeout=10)

    assert data is None
    assert await fake_redis.exists("openrouter:model_down:model-a") == 1


def test_get_redis_is_not_cached_across_calls():
    """Each call to a Celery task creates a fresh event loop (see run_async in
    app/tasks/*.py); an async Redis client's pool is bound to the loop that
    created it, so this module must never cache a client across calls. This
    test does not use the fake_redis fixture since it needs to observe the
    real (unpatched) _get_redis implementation."""
    from app.services import openrouter as openrouter_module

    with patch("app.services.openrouter.redis.from_url") as mock_from_url:
        mock_from_url.side_effect = [MagicMock(), MagicMock()]
        first = openrouter_module._get_redis()
        second = openrouter_module._get_redis()

    assert mock_from_url.call_count == 2
    assert first is not second


@pytest.mark.asyncio
async def test_validator_rejection_falls_through_without_marking_down(fake_redis):
    responses = [
        _mock_response(200, _success_body("bad json")),
        _mock_response(200, _success_body("good json")),
    ]

    def validate(data: dict) -> bool:
        return data["choices"][0]["message"]["content"] == "good json"

    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=responses)):
        data, model, error = await call_openrouter(
            ["model-a", "model-b"], lambda m: {"model": m}, timeout=10, validate=validate
        )

    assert model == "model-b"
    assert await fake_redis.exists("openrouter:model_down:model-a") == 0


@pytest.mark.asyncio
async def test_ollama_model_routed_to_local_base_url_without_auth_header(fake_redis):
    with patch("app.services.openrouter.settings.ollama_base_url", "http://localhost:11434"):
        mock_post = AsyncMock(return_value=_mock_response(200, _success_body("local reply")))
        with patch("httpx.AsyncClient.post", new=mock_post):
            data, model, error = await call_openrouter(
                ["ollama/qwen2.5:7b-instruct-q4_K_M"], lambda m: {"model": m}, timeout=10
            )

    assert model == "ollama/qwen2.5:7b-instruct-q4_K_M"
    assert data["choices"][0]["message"]["content"] == "local reply"

    call_args = mock_post.call_args
    assert call_args.args[0] == "http://localhost:11434/chat/completions"
    assert "Authorization" not in call_args.kwargs["headers"]
    assert call_args.kwargs["json"]["model"] == "qwen2.5:7b-instruct-q4_K_M"


@pytest.mark.asyncio
async def test_ollama_model_works_without_openrouter_api_key(fake_redis):
    with patch("app.services.openrouter.settings.openrouter_api_key", ""):
        with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_mock_response(200, _success_body("ok")))):
            data, model, error = await call_openrouter(
                ["ollama/qwen2.5:7b-instruct-q4_K_M"], lambda m: {"model": m}, timeout=10
            )

    assert data is not None
    assert model == "ollama/qwen2.5:7b-instruct-q4_K_M"


@pytest.mark.asyncio
async def test_cloud_model_skipped_without_api_key_but_local_still_tried(fake_redis):
    with patch("app.services.openrouter.settings.openrouter_api_key", ""):
        mock_post = AsyncMock(return_value=_mock_response(200, _success_body("local only")))
        with patch("httpx.AsyncClient.post", new=mock_post):
            data, model, error = await call_openrouter(
                ["cloud-model", "ollama/qwen2.5:7b-instruct-q4_K_M"], lambda m: {"model": m}, timeout=10
            )

    assert model == "ollama/qwen2.5:7b-instruct-q4_K_M"
    assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_ollama_model_uses_configured_local_timeout_when_longer(fake_redis):
    with patch("app.services.openrouter.settings.ollama_timeout_seconds", 180):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=_mock_response(200, _success_body("ok")))
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            await call_openrouter(["ollama/qwen2.5:7b-instruct-q4_K_M"], lambda m: {"model": m}, timeout=10)

    assert mock_client_cls.call_args.kwargs["timeout"] == 180


@pytest.mark.asyncio
async def test_attempts_records_full_trail_on_fallback(fake_redis):
    responses = [
        _mock_response(429, text="rate limited"),
        _mock_response(200, _success_body("from model B")),
    ]
    attempts: list[dict] = []

    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=responses)):
        data, model, error = await call_openrouter(
            ["model-a", "model-b"], lambda m: {"model": m}, timeout=10, attempts=attempts
        )

    assert model == "model-b"
    assert [a["model"] for a in attempts] == ["model-a", "model-b"]
    assert attempts[0]["outcome"] == "rate_limited"
    assert attempts[0]["error"] == "Too many requests. Try again later."
    assert attempts[1]["outcome"] == "success"
    assert attempts[1]["error"] is None
    assert all(isinstance(a["elapsedMs"], int) for a in attempts)


@pytest.mark.asyncio
async def test_attempts_records_skipped_cooldown_without_http_call(fake_redis):
    await fake_redis.set("openrouter:model_down:model-a", "1")
    attempts: list[dict] = []

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_mock_response(200, _success_body("ok")))):
        await call_openrouter(
            ["model-a", "model-b"], lambda m: {"model": m}, timeout=10, attempts=attempts
        )

    assert attempts[0] == {"model": "model-a", "outcome": "skipped_cooldown", "error": None, "elapsedMs": attempts[0]["elapsedMs"]}
    assert attempts[1]["outcome"] == "success"


@pytest.mark.asyncio
async def test_attempts_stays_empty_list_when_not_requested(fake_redis):
    """attempts=None (the default) must not change behavior or raise."""
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_mock_response(200, _success_body("ok")))):
        data, model, error = await call_openrouter(["model-a"], lambda m: {"model": m}, timeout=10)

    assert model == "model-a"
