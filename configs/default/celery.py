import os

from .redis import REDIS_HOST

CELERY_BROKER_DB = os.getenv("CELERY_BROKER_DB", 2)
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{6379}/{CELERY_BROKER_DB}"
)
# Timeout: 所有任务不得超过两分钟
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 2
# 任务返回后才会从队列拿走
CELERY_ACKS_LATE = True
