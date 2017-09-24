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
MB = 1024 * 1024
GB = 1024 * 1024 * 1024
DEFAULT_TRAFFIC = 5 * GB
START_PORT = 10000
# 签到流量设置
MIN_CHECKIN_TRAFFIC = 10 * MB
MAX_CHECKIN_TRAFFIC = 200 * MB

# 是否启用支付宝系统
USE_ALIPAY = True

# 网站title
TITLE = '谜之屋'
SUBTITLE = '秘密的小屋'
# 网站邀请界面提示语
INVITEINFo = '邀请码实时更新，如果用完了进进telegram群问bot要 群链接：https://t.me/Ehcobreakwa11'
