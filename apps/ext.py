from django.conf import settings
from redis import Redis

from apps.extensions.alipay import Pay
from apps.extensions.cachext import RedisCache
from apps.extensions.encoder import Encoder
from apps.extensions.lock import LockManager

# register pay instance
pay = Pay()

# register redis client
redis = Redis.from_url(settings.REDIS_DB_URI)

# register cache
cache = RedisCache(settings.REDIS_CACHE_URI)

# register encoder
encoder = Encoder()

# register lock manager
lock = LockManager(redis_client=redis)
