from redis import Redis

from django.conf import settings

from apps.extensions.alipay import Pay
from apps.extensions.cachext import RedisCache
from apps.extensions.encoder import Encoder

# register pay instance
pay = Pay()

# register redis client
redis = Redis.from_url(settings.REDIS_URI)

# register cache
cache = RedisCache(settings.REDIS_URI)

# register encoder
encoder = Encoder()
