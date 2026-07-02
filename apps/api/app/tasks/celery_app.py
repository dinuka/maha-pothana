from celery import Celery
from app.config import settings

celery_app = Celery(
    "maha_pothana",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.split_pages",
        "app.tasks.detect_sections",
        "app.tasks.crop_sections",
        "app.tasks.build_book",
    ],
)

celery_app.conf.task_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.broker_connection_retry_on_startup = True
