# DEBUG设置
DEBUG = True


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
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SS面板设置：
MB = 1024 * 1024
GB = 1024 * 1024 * 1024
DEFAULT_TRAFFIC = 5 * GB

# 默认加密混淆协议
DEFAULT_METHOD = 'aes-128-ctr'
DEFAULT_PROTOCOL = 'auth_chain_a'
DEFAULT_OBFS = 'http_simple'

# 签到流量设置
MIN_CHECKIN_TRAFFIC = 10 * MB
MAX_CHECKIN_TRAFFIC = 200 * MB

# 是否启用支付宝系统
USE_ALIPAY = False
# 支付订单提示信息 修改请保留 {} 用于动态生成金额
ALIPAY_TRADE_INFO = '谜之屋的{}元充值码'

# 网站title
TITLE = '谜之屋'
SUBTITLE = '秘密的小屋111'

# 网站邀请界面提示语
INVITEINFO = '邀请码实时更新，如果用完了请关注公众号findyourownway获取'
