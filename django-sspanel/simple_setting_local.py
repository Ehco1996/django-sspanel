# DEBUG设置
DEBUG = True


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
# remote debuge mysql 设置
DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sspanel',
        'USER': 'ss',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '3306',

    }
}
'''


# 邮件服务设置：
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SS面板设置：
MB = 1024 * 1024
GB = 1024 * 1024 * 1024
DEFAULT_TRAFFIC = 5 * GB
START_PORT = 10000
# 签到流量设置
MIN_CHECKIN_TRAFFIC = 10 * MB
MAX_CHECKIN_TRAFFIC = 200 * MB

# 是否启用支付宝系统
USE_ALIPAY = False

# 网站title
TITLE = '谜之屋111'
SUBTITLE = '秘密的小屋111'