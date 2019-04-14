import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

SENTRY_DSN = os.environ.get("SENTRY_DSN")

if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[DjangoIntegration()])
