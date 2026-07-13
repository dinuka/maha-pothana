import logging
import time
from typing import Callable

import httpx
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OLLAMA_MODEL_PREFIX = "ollama/"


def _get_redis() -> redis.Redis:
    # Not cached: this module is used from both the FastAPI process and Celery
    # tasks, and Celery's run_async() opens a fresh event loop per task. An
    # async Redis client's connection pool is bound to the loop it was created
    # on, so a module-level singleton would break (or silently no-op through
    # the broad except clauses below) on every task after the first.
    return redis.from_url(settings.redis_url)


def _down_key(model: str) -> str:
    return f"openrouter:model_down:{model}"


async def is_model_down(model: str) -> bool:
    client = _get_redis()
    try:
        return bool(await client.exists(_down_key(model)))
    except Exception as e:
        logger.warning("[openrouter] is_model_down: redis check failed for model=%s: %s", model, e)
        return False
    finally:
        await client.aclose()


async def mark_model_down(model: str) -> None:
    client = _get_redis()
    try:
        await client.set(_down_key(model), "1", ex=settings.openrouter_model_cooldown_seconds)
    except Exception as e:
        logger.warning("[openrouter] mark_model_down: redis set failed for model=%s: %s", model, e)
    finally:
        await client.aclose()


async def call_openrouter(
    models: list[str],
    build_payload: Callable[[str], dict],
    timeout: float,
    validate: Callable[[dict], bool] | None = None,
    attempts: list[dict] | None = None,
) -> tuple[dict | None, str | None, str | None]:
    """Try each model in order, skipping models currently marked down.

    Models prefixed "ollama/" are routed to the local Ollama server
    (settings.ollama_base_url) instead of OpenRouter, with no API key and a
    longer timeout to accommodate slow local/CPU-offloaded inference. They
    are intended as a last-resort fallback after every cloud model fails.

    Returns (response_json, model_used, error). On availability-type failures
    (429, 5xx, timeout, connection errors) the model is marked down for the
    configured cooldown. On systemic failures (401/403/400) the model is left
    alone since the failure likely affects every model equally.

    `validate`, if given, is applied to a successful (200, non-empty choices)
    response; a rejection is treated as a quality issue (not availability) and
    falls through to the next model without marking the current one down.

    `attempts`, if given, is appended to in place with one dict per model
    reached ({"model", "outcome", "error", "elapsedMs"}) so callers can build
    a full per-model trail for observability, not just the winning model.
    """
    api_key = settings.openrouter_api_key
    has_local_model = any(m.startswith(OLLAMA_MODEL_PREFIX) for m in models)
    if not api_key and not has_local_model:
        return None, None, "OpenRouter API key not configured"

    last_error = None
    tried_any = False

    for model in models:
        attempt_start = time.monotonic()

        def record(outcome: str, error: str | None) -> None:
            if attempts is not None:
                attempts.append({
                    "model": model,
                    "outcome": outcome,
                    "error": error,
                    "elapsedMs": int((time.monotonic() - attempt_start) * 1000),
                })

        if await is_model_down(model):
            logger.info("[openrouter] call_openrouter: skipping model=%s (marked down)", model)
            record("skipped_cooldown", None)
            continue

        is_local = model.startswith(OLLAMA_MODEL_PREFIX)
        if is_local:
            base_url = settings.ollama_base_url
            request_model = model[len(OLLAMA_MODEL_PREFIX):]
            headers = {"Content-Type": "application/json"}
            request_timeout = max(timeout, settings.ollama_timeout_seconds)
        else:
            if not api_key:
                logger.info("[openrouter] call_openrouter: skipping model=%s (no API key)", model)
                record("skipped_no_api_key", None)
                continue
            base_url = OPENROUTER_BASE_URL
            request_model = model
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            request_timeout = timeout

        tried_any = True
        logger.info("[openrouter] call_openrouter: trying model=%s", model)

        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=build_payload(request_model),
                )

            if resp.status_code == 429:
                logger.warning("[openrouter] call_openrouter: rate limited on model=%s, marking down", model)
                await mark_model_down(model)
                last_error = "Too many requests. Try again later."
                record("rate_limited", last_error)
                continue

            if resp.status_code >= 500:
                logger.warning("[openrouter] call_openrouter: model=%s server error status=%d, marking down", model, resp.status_code)
                await mark_model_down(model)
                last_error = f"Request failed with status {resp.status_code}"
                record("server_error", last_error)
                continue

            if resp.status_code in (401, 403, 400):
                error_text = resp.text[:500]
                logger.warning("[openrouter] call_openrouter: model=%s systemic error status=%d: %s", model, resp.status_code, error_text)
                last_error = f"Request failed with status {resp.status_code}"
                record("systemic_error", last_error)
                continue

            if resp.status_code != 200:
                logger.warning("[openrouter] call_openrouter: model=%s failed with status=%d: %s", model, resp.status_code, resp.text[:500])
                last_error = f"Request failed with status {resp.status_code}"
                record("http_error", last_error)
                continue

            try:
                data = resp.json()
            except ValueError:
                logger.warning("[openrouter] call_openrouter: model=%s returned non-JSON body", model)
                last_error = "AI returned an unexpected response format"
                record("non_json", last_error)
                continue

            if "error" in data:
                error_msg = data["error"].get("message", "Unknown error")
                logger.warning("[openrouter] call_openrouter: model=%s API error: %s", model, error_msg)
                last_error = error_msg
                record("api_error", last_error)
                continue

            if "choices" not in data or not data["choices"]:
                logger.warning("[openrouter] call_openrouter: model=%s returned empty choices", model)
                last_error = "Empty response from AI"
                record("empty_response", last_error)
                continue

            if validate is not None and not validate(data):
                logger.warning("[openrouter] call_openrouter: model=%s response rejected by validator", model)
                last_error = "AI returned an unexpected response format"
                record("validation_rejected", last_error)
                continue

            record("success", None)
            return data, model, None

        except httpx.TimeoutException:
            logger.warning("[openrouter] call_openrouter: model=%s timed out, marking down", model)
            await mark_model_down(model)
            last_error = "AI service timed out"
            record("timeout", last_error)
            continue
        except Exception as e:
            logger.warning("[openrouter] call_openrouter: model=%s failed: %s, marking down", model, e)
            await mark_model_down(model)
            last_error = str(e)
            record("exception", last_error)
            continue

    if not tried_any:
        return None, None, "All models are currently unavailable"

    return None, None, last_error
