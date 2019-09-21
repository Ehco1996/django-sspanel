# mysql 设置
DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.mysql",
        "NAME": "sspanel",
        "USER": "root",
        "PASSWORD": "",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {
            "autocommit": True,
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}
