import os

from configs.default import *


DATABASES['default'].update(
    {'PASSWORD': os.getenv('MYSQL_PASSWORD'),
     'HOST': os.getenv('MYSQL_HOST')
     })


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
