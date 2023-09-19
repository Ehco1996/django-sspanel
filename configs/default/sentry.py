import os

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

SENTRY_DSN = os.environ.get("SENTRY_DSN")
SENTRY_RELEASE_TAG = os.environ.get("SENTRY_RELEASE_TAG")
SENTRY_TRACES_SAMPLE_RATE = os.environ.get("SENTRY_TRACES_SAMPLE_RATE", 0.1)
SENTRY_ENVIRONMENT = os.environ.get("SENTRY_ENVIRONMENT", "development")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        release=SENTRY_RELEASE_TAG,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        environment=SENTRY_ENVIRONMENT,
        integrations=[
            CeleryIntegration(),
            DjangoIntegration(transaction_style="function_name"),
            RedisIntegration(),
        ],
    )
