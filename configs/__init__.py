import os

django_env = os.getenv("DJANGO_ENV", "development")
if django_env == "production":
    from configs.production import *  # noqa
else:
    from configs.development import *  # noqa
