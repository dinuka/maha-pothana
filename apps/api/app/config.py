from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


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

    libretranslate_url: str = "http://libretranslate:5000"

    auth_secret: str = "change-me-in-production"
    internal_api_key: str = "change-me"

    nextjs_url: str = "http://nextjs:3000"

    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemma-4-31b-it:free"

    model_config = {"env_prefix": "", "case_sensitive": False, "env_file": "../../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

if settings.openrouter_api_key:
    logger.info("OPENROUTER_API_KEY loaded: %s...", settings.openrouter_api_key[:10])
else:
    logger.warning("OPENROUTER_API_KEY is not set in environment")
