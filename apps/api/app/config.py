from pydantic_settings import BaseSettings


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

    model_config = {"env_prefix": "", "case_sensitive": False, "env_file": "../../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
