# flake8: noqa
import os

from configs.default import *

# NOTE for django debug toolbar
DEBUG = True
INTERNAL_IPS = os.getenv("DEBUG_INTERNAL_IPS", "127.0.0.1,0.0.0.0").split(",")
INSTALLED_APPS.insert(INSTALLED_APPS.index("django_prometheus"), "debug_toolbar")
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
