

# mysql 设置
DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sspanel',
        'USER': 'root',
        'PASSWORD': '19960202',
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
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



# SS面板设置：
GB = 1024 * 1024 * 1024
DEFAULT_TRAFFIC = 5 * GB
START_PORT = 10000
