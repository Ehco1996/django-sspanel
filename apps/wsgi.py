"""
WSGI config for django_sspanel project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

env = os.getenv('DJANGO_ENV', 'production')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configs.{}".format(env))

application = get_wsgi_application()
