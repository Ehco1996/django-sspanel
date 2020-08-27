from redis import Redis

from django.conf import settings

from apps.extensions.alipay import Pay
from apps.extensions.cachext import Redis, RedisCache
from apps.extensions.encoder import Encoder

# register pay instance
pay = Pay()

# register redis client
redis = Redis(settings.REDIS_DB_URI)

# register cache
cache = RedisCache(settings.REDIS_CACHE_URI)

# register encoder
encoder = Encoder()
