import os

from configs.default import *

DEBUG = False

DATABASES['default'].update(
    {'PASSWORD': os.getenv('MYSQL_PASSWORD', 'your_pass'),
     'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'),
     'USER': os.getenv('MYSQL_USER', 'root')
     })


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
