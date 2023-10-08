import functools
import pickle

import redis
from pendulum import DateTime

DEFAULT_KEY_TYPES = (str, int, float, bool, DateTime)


def norm_cache_key(v):
    if isinstance(v, type):
        return v.__name__
    if isinstance(v, bytes):
        return v.decode()
    if hasattr(v, "path_info"):
        return getattr(v, "path_info")
    if v is None or isinstance(v, DEFAULT_KEY_TYPES):
        return str(v)
    else:
        raise ValueError(
            "only str, int, float, bool, django.WSGIRequest,DateTime can be key"
        )


def make_default_key(f, *args, **kwargs):
    keys = [norm_cache_key(v) for v in args]
    keys += sorted(["{}={}".format(k, norm_cache_key(v)) for k, v in kwargs.items()])
    return "default.{}.{}.{}".format(f.__module__, f.__name__, ".".join(keys))


class cached:
    client = None

    def __init__(self, func=None, ttl=60 * 60, cache_key=make_default_key):
        self.ttl = ttl
        self.cache_key = cache_key
        if func is not None:
            func = self.decorator(func)
        self.func = func

    def __call__(self, *args, **kwargs):
        if self.func is not None:
            return self.func(*args, **kwargs)
        f = args[0]
        return self.decorator(f)

    def __getattr__(self, name):
        return getattr(self.func, name)

    def decorator(self, f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            key = wrapper.make_cache_key(*args, **kwargs)
            rv = self.client.get(key)
            if rv is None:
                rv = f(*args, **kwargs)
                if rv is not None:
                    self.client.set(key, rv, wrapper.ttl)
            return rv

        def make_cache_key(*args, **kwargs):
            if callable(self.cache_key):
                return self.cache_key(f, *args, **kwargs)
            else:
                return self.cache_key

        wrapper.uncached = f
        wrapper.ttl = self.ttl
        wrapper.make_cache_key = make_cache_key

        return wrapper


class RedisClient:
    def __init__(self, uri):
        self._pool = redis.ConnectionPool.from_url(uri)
        self._client = redis.Redis(connection_pool=self._pool)

    def get(self, key):
        v = self._client.get(key)
        return v if v is None else pickle.loads(v)

    def get_many(self, keys):
        values = self._client.mget(keys)
        return [v if v is None else pickle.loads(v) for v in values]

    def set(self, key, value, ttl=60 * 5):
        return self._client.set(key, pickle.dumps(value), ex=ttl)

    def set_many(self, mapping, ttl=60 * 5):
        mapping = {k: pickle.dumps(v) for k, v in mapping.items()}
        rv = self._client.mset(mapping)
        for k in mapping:
            self._client.expire(k, ttl)
        return rv

    def delete(self, key):
        return self._client.delete(key)

    def delete_many(self, keys):
        if keys:
            return self._client.delete(*keys)
        return False


class RedisCache:
    def __init__(self, uri):
        # register cached attr
        self._client = RedisClient(uri)
        self.cached = cached
        self.cached.client = self._client

    def __getattr__(self, attr):
        return getattr(self._client, attr)
