# DEBUG设置
DEBUG = False

# 域名设置 
ALLOWED_HOSTS = [
        'www.ehcozone.club',
        'ehcozone.club',
]

# mysql 设置
DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sspanel',
        'USER': 'root',
        'PASSWORD': 'pass',
        'HOST': '127.0.0.1',
        'PORT': '3306',

    }
}


'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
'''


# 邮件服务设置：
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# 我使用163邮箱作为smtp服务器
EMAIL_USE_TLS = False
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'USER'
EMAIL_HOST_PASSWORD = 'PASS'
DEFAULT_FROM_EMAIL = 'Ehco<ADDRESS>'

# SS面板设置：
GB = 1024 * 1024 * 1024
DEFAULT_TRAFFIC = 5 * GB
START_PORT = 10000
 