import os

RAVEN_CONFIG = {
    'dsn': os.environ.get('SENTRY_DSN'),
}
