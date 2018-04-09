import os
from configs.default import *

DATABASES['default'].update(
    {'PASSWORD': os.getenv('MYSQL_PASS')})

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
