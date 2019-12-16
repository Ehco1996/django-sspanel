import os

# mysql 设置
DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.mysql",
        "NAME": "sspanel",
        "PASSWORD": os.getenv("MYSQL_PASSWORD", "yourpass"),
        "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "USER": os.getenv("MYSQL_USER", "root"),
        "OPTIONS": {
            "autocommit": True,
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}
