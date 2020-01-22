# 网站域名设置（请正确填写，不然订阅功能会失效：
HOST = "http://127.0.0.1:8000"

# 网站密钥
SECRET_KEY = "aasdasdas"

# 是否开启注册
ALLOW_REGISTER = True

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
DEFAULT_METHOD = "aes-256-cfb"

# 签到流量设置
MIN_CHECKIN_TRAFFIC = 10 * MB
MAX_CHECKIN_TRAFFIC = 200 * MB

# 网站title
TITLE = "谜之屋"
SUBTITLE = "秘密的小屋"

# 用户邀请返利比例
INVITE_PERCENT = 0.2
# 用户能生成的邀请码数量
INVITE_NUM = 5

# 网站邀请界面提示语
INVITEINFO = "邀请码实时更新，如果用完了就没了"


# 部分API接口TOKEN
TOKEN = "youowntoken"

# 是否开启用户到期邮件通知
EXPIRE_EMAIL_NOTICE = False

# SHORT_URL_ALPHABET 请随机生成,且不要重复
DEFAULT_ALPHABET = "qwertyuiopasdfghjklzxcvbnm"

# FOR SIMPLE UI
SIMPLEUI_HOME_INFO = False
SIMPLEUI_DEFAULT_ICON = False
