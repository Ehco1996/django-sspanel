import os

# SS面板设置：
MB = 1024 * 1024
GB = 1024 * 1024 * 1024
DEFAULT_TRAFFIC = 5 * GB
START_PORT = 1024

# 域名设置
ALLOWED_HOSTS = ["*"]

# 网站域名设置（请正确填写，不然订阅功能会失效：
SITE_HOST = os.getenv("SITE_HOST", "http://127.0.0.1:8000")
CORS_ALLOWED_ORIGINS = [SITE_HOST]  # django-cors-headers
CSRF_TRUSTED_ORIGINS = [SITE_HOST]  # django built-in
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

# 网站密钥
SECRET_KEY = os.getenv("SECRET_KEY", "aasdasdas")

# 是否开启注册
ALLOW_REGISTER = bool(os.getenv("ALLOW_REGISTER", True))

HIDE_FOOTER = bool(os.getenv("HIDE_FOOTER", False))

# 默认的theme 可选列表在 apps/constants.py 里的THEME_CHOICES里
DEFAULT_THEME = os.getenv("DEFAULT_THEME", "default")


# 默认加密混淆协议
DEFAULT_METHOD = os.getenv("DEFAULT_METHOD", "aes-256-cfb")

# 签到流量设置
MIN_CHECKIN_TRAFFIC = int(os.getenv("MIN_CHECKIN_TRAFFIC", 10 * MB))
MAX_CHECKIN_TRAFFIC = int(os.getenv("MAX_CHECKIN_TRAFFIC", 200 * MB))

# 网站title
SITE_TITLE = os.getenv("SITE_TITLE", "")
SITE_SUBTITLE = os.getenv("SITE_SUBTITLE", "")
SITE_SEO_KEYWORDS = os.getenv("SITE_SEO_KEYWORDS", "")
SITE_SEO_DESCRIPTION = os.getenv("SITE_SEO_DESCRIPTION", "")
SITE_LOGO_URL = os.getenv("SITE_LOGO_URL", "")

# 用户邀请返利比例
INVITE_PERCENT = float(os.getenv("INVITE_PERCENT", 0.2))
# 用户能生成的邀请码数量
INVITE_NUM = int(os.getenv("INVITE_NUM ", 5))

# 网站邀请页提示语
INVITEINFO = os.getenv("INVITEINFO", "邀请码实时更新，如果用完了就没了")

# 部分API接口TOKEN
TOKEN = os.getenv("TOKEN", "youowntoken")

# 是否开启用户到期邮件通知
EXPIRE_EMAIL_NOTICE = bool(os.getenv("EXPIRE_EMAIL_NOTICE", False))

# SHORT_URL_ALPHABET 请随机生成,且不要重复
DEFAULT_ALPHABET = os.getenv("DEFAULT_ALPHABET", "qwertyuiopasdfghjklzxcvbnm")

# FOR SIMPLE UI
SIMPLEUI_ANALYSIS = False
SIMPLEUI_HOME_ACTION = False
SIMPLEUI_HOME_QUICK = True
SIMPLEUI_HOME_INFO = bool(os.getenv("SIMPLEUI_HOME_INFO", False))
SIMPLEUI_DEFAULT_ICON = bool(os.getenv("SIMPLEUI_DEFAULT_ICON", True))
SIMPLEUI_ICON = {
    "代理节点": "fas fa-server",
    "SS节点配置": "fa fa-rocket",
    "中转节点": "fas fa-forward",
    "中转规则": "fas fa-ruler",
    "节点在线记录": "fas fa-signal",
    "用户流量记录": "fas fa-filter",
    "用户在线IP记录": "fas fa-map-marker",
    "用户": "fas fa-users",
    "用户订单": "fas fa-shopping-cart",
    "用户推荐记录": "fab fa-adversal",
    "用户签到记录": "fas fa-user-check",
    "邀请码": "fas fa-user-friends",
    "返利记录": "fas fa-coins",
    "捐赠记录": "fas fa-donate",
    "充值码": "fab fa-alipay",
    "商品": "fas fa-store",
    "用户购买记录": "fas fa-history",
    "系统公告": "fas fa-bullhorn",
    "工单": "fas fa-tasks",
    "邮件发送记录": "fas fa-envelope",
    "用户订阅记录": "fas fa-download",
    "开放API": "fas fa-server",
}

# TG 相关配置
TELEGRAM_BOT_NAME = os.getenv("TELEGRAM_BOT_NAME")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_LOGIN_REDIRECT_URL = f"{SITE_HOST}/login-with-telegram/"
