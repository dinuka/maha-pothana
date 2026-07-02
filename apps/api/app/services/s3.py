import io
from datetime import timedelta, datetime, timezone

from minio import Minio
from app.config import settings

client: Minio | None = None

# Signing requests are floored to this window so repeated calls for the same key
# within the window produce an identical presigned URL (same request_date -> same
# signature), letting the browser reuse its HTTP cache instead of re-downloading
# thumbnails on every list_pages call. Must stay well under `expires` so a URL
# signed near the end of a window is still valid after the window rolls over.
PRESIGN_WINDOW_SECONDS = 900


def _floor_to_window(seconds: int) -> datetime:
    now = datetime.now(timezone.utc)
    floored_epoch = int(now.timestamp()) // seconds * seconds
    return datetime.fromtimestamp(floored_epoch, tz=timezone.utc)


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
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return key


async def get_presigned_url(key: str, expires: int = 3600) -> str:
    s3 = get_s3()
    request_date = _floor_to_window(PRESIGN_WINDOW_SECONDS)
    return s3.presigned_get_object(
        settings.minio_bucket,
        key,
        expires=timedelta(seconds=expires),
        request_date=request_date,
        # MinIO sends no Cache-Control by default, so without this override the
        # browser has no freshness signal and may re-fetch the image on every
        # request even when the URL (and thus the underlying object) is unchanged.
        response_headers={"response-cache-control": f"private, max-age={PRESIGN_WINDOW_SECONDS}"},
    )


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
