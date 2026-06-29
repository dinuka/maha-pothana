from minio import Minio
from app.config import settings

client: Minio | None = None


def get_s3() -> Minio:
    global client
    if client is None:
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)
    return client


async def upload_file(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    s3 = get_s3()
    s3.put_object(
        settings.minio_bucket,
        key,
        data,
        length=len(data),
        content_type=content_type,
    )
    return key


async def get_presigned_url(key: str, expires: int = 3600) -> str:
    s3 = get_s3()
    return s3.presigned_get_object(settings.minio_bucket, key, expires=expires)


async def delete_file(key: str) -> None:
    s3 = get_s3()
    s3.remove_object(settings.minio_bucket, key)


async def file_exists(key: str) -> bool:
    s3 = get_s3()
    try:
        s3.stat_object(settings.minio_bucket, key)
        return True
    except Exception:
        return False
