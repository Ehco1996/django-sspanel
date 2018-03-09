import base64

# DEBUG设置
DEBUG = True

# 域名设置
ALLOWED_HOSTS = ['*']
# mysql 设置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sspanel',
        'USER': 'root',
        'PASSWORD': 'xx',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# 邮件服务设置：
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# 是否开启邮件功能
USE_SMTP = False


# SS面板设置：
MB = 1024 * 1024
GB = 1024 * 1024 * 1024
DEFAULT_TRAFFIC = 5 * GB
START_PORT = 1024

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

# 是否开启91pay 第三方接口
# 91PAY 、ALIPAY只能开启一项
# 需要授权请联系：
# https://t.me/gh012363  或者QQ群538609570
USE_91PAY = True
# 自己的支付宝账号
ALIPAY_NUM = 'xx'

# 网站title
TITLE = '谜之屋'
SUBTITLE = '秘密的小屋111'

# 用户邀请返利比例
INVITE_PERCENT = 0.2
# 用户能生成的邀请码数量
INVITE_NUM = 5

# 网站邀请界面提示语
INVITEINFO = '邀请码实时更新，如果用完了请关注公众号findyourownway获取'

# 网站域名设置（请正确填写，不然订阅功能会失效：
HOST = 'http://127.0.0.1:8000/'

# 管理员账号
USERNAME = 'ehco'
# 管理员ss端口
PORT = 2345
# 管理员私有token，用于后端接口调用
TOKEN = base64.b64encode(
    bytes('{}+{}'.format(USERNAME, PORT), 'utf8')).decode()
