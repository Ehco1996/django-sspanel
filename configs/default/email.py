import os

# 是否开启邮件功能
USE_SMTP = bool(os.getenv("USE_SMTP", True))
EMAIL_USE_SSL = bool(os.getenv("EMAIL_USE_SSL", True))
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.163.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)


# FOR mailgun
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_SENDER_DOMAIN = os.getenv("MAILGUN_SENDER_DOMAIN")
if MAILGUN_API_KEY and MAILGUN_SENDER_DOMAIN:
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
