import os


REDIS_CACHE_URI = os.getenv("REDIS_CACHE_URI", "redis://127.0.0.1:6379/1")
REDIS_DB_URI = os.getenv("REDIS_DB_URI", "redis://127.0.0.1:6379/2")
