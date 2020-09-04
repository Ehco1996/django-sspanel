import os

from .redis import REDIS_HOST

CELERY_BROKER_DB = os.getenv("CELERY_BROKER_DB", 2)
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{6379}/{CELERY_BROKER_DB}"
)
