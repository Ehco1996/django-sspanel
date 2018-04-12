# mysql 设置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sspanel',
        'USER': 'root',
        'PASSWORD': 'xx',
        'HOST': '',
        'PORT': '3306',
        'OPTIONS': {
            'autocommit': True,
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
