import os

from configs.default import *  # noqa

DEBUG = True

# NOTE for django debug toolbar
INTERNAL_IPS = os.getenv("DEBUG_INTERNAL_IPS", "127.0.0.1,0.0.0.0").split(",")
INSTALLED_APPS.insert(INSTALLED_APPS.index("django_prometheus"), "debug_toolbar")
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
