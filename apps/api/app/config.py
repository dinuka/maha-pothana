from typing import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode
from pydantic import field_validator
import logging

logger = logging.getLogger(__name__)


def _split_models(value: str) -> list[str]:
    return [m.strip() for m in value.split(",") if m.strip()]


class Settings(BaseSettings):
    app_name: str = "Maha Pothana API"
    debug: bool = False

    mongodb_url: str = "mongodb://mongodb:27017/maha_pothana"
    mongodb_db_name: str = "maha_pothana"

    redis_url: str = "redis://redis:6379/0"

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "maha-pothana"
    minio_public_url: str = "http://localhost:9000"

    auth_secret: str = "change-me-in-production"
    internal_api_key: str = "change-me"

    nextjs_url: str = "http://nextjs:3000"

    openrouter_api_key: str = ""

    openrouter_extraction_models: Annotated[list[str], NoDecode] = [
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "google/gemma-4-26b-a4b-it:free",
    ]
    openrouter_transliteration_models: Annotated[list[str], NoDecode] = [
        "google/gemma-4-31b-it:free",
        "openai/gpt-oss-120b:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
    ]
    openrouter_translation_models: Annotated[list[str], NoDecode] = [
        "google/gemma-4-31b-it:free",
        "openai/gpt-oss-120b:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
    ]
    openrouter_confidence_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"

    @field_validator(
        "openrouter_extraction_models",
        "openrouter_transliteration_models",
        "openrouter_translation_models",
        mode="before",
    )
    @classmethod
    def _parse_model_list(cls, value: object) -> object:
        if isinstance(value, str):
            return _split_models(value)
        return value

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False, env_file="../../.env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

if settings.openrouter_api_key:
    logger.info("OPENROUTER_API_KEY loaded: %s...", settings.openrouter_api_key[:10])
else:
    logger.warning("OPENROUTER_API_KEY is not set in environment")
