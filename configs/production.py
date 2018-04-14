import os

from configs.default import *

DEBUG = False

DATABASES['default'].update(
    {'PASSWORD': os.getenv('MYSQL_PASSWORD'),
     'HOST': os.getenv('MYSQL_HOST')
     })


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
