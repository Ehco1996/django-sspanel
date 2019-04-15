# 网站域名设置（请正确填写，不然订阅功能会失效：
HOST = "http://127.0.0.1:8000/"

# 网站密钥
SECRET_KEY = "aasdasdas"

# 是否开启注册
ALLOW_REGISET = True

# 默认的theme
# 可选列表在 apps/constants.py 里的THEME_CHOICES里
DEFAULT_THEME = "default"

# 域名设置
ALLOWED_HOSTS = ["*"]

# SS面板设置：
MB = 1024 * 1024
GB = 1024 * 1024 * 1024
DEFAULT_TRAFFIC = 5 * GB
START_PORT = 1024

# 默认加密混淆协议
DEFAULT_METHOD = "aes-128-ctr"
DEFAULT_PROTOCOL = "auth_chain_a"
DEFAULT_OBFS = "http_simple"

# 签到流量设置
MIN_CHECKIN_TRAFFIC = 10 * MB
MAX_CHECKIN_TRAFFIC = 200 * MB

# 是否启用支付宝系统
USE_ALIPAY = False
# 支付订单提示信息 修改请保留 {} 用于动态生成金额
ALIPAY_TRADE_INFO = "谜之屋的{}元充值码"
# 支付宝回掉接口
ALIPAY_CALLBACK_URL = f'{HOST}/api/callback/alipay'

# 网站title
TITLE = "谜之屋"
SUBTITLE = "秘密的小屋test"

# 用户邀请返利比例
INVITE_PERCENT = 0.2
# 用户能生成的邀请码数量
INVITE_NUM = 5

# 网站邀请界面提示语
INVITEINFO = "邀请码实时更新，如果用完了请关注公众号findyourownway获取"


# 部分API接口TOKEN
TOKEN = "youowntoken"

# 是否开启用户到期邮件通知
EXPIRE_EMAIL_NOTICE = False
