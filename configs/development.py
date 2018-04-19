import os

from configs.default import *

# DEBUG设置
DEBUG = True

DATABASES['default'].update(
    {'PASSWORD': os.getenv('MYSQL_PASSWORD',),
     'HOST': os.getenv('MYSQL_HOST','127.0.0.1')
     })

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
