import os

from configs.default import *

# DEBUG设置
DEBUG = True

MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

if MYSQL_PASSWORD:
    DATABASES["default"].update(
        {"HOST": os.getenv("MYSQL_HOST", "127.0.0.1"), "PASSWORD": MYSQL_PASSWORD}
    )
