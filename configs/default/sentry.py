import os

SENTRY_DSN = os.environ.get("SENTRY_DSN")
SENTRY_RELEASE_TAG = os.environ.get("SENTRY_RELEASE_TAG")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN, release=SENTRY_RELEASE_TAG, integrations=[DjangoIntegration()]
    )
