import os

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_DB_URI = os.getenv("REDIS_DB_URI", "redis://" + REDIS_HOST + ":6379/0")
REDIS_CACHE_URI = os.getenv("REDIS_CACHE_URI", "redis://" + REDIS_HOST + ":6379/1")
