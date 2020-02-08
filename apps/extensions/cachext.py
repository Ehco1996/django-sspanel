import functools
from django.core.cache import cache

DEFAULT_KEY_TYPES = (str, int, float, bool)


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
        raise ValueError("only str, int, float, bool, django.WSGIRequest can be key")


def make_default_key(f, *args, **kwargs):
    keys = [norm_cache_key(v) for v in args]
    keys += sorted(["{}={}".format(k, norm_cache_key(v)) for k, v in kwargs.items()])
    return "default.{}.{}.{}".format(f.__module__, f.__name__, ".".join(keys))


class cached:
    client = cache

    def __init__(self, func=None, ttl=60 * 5, cache_key=make_default_key):
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
                key = self.cache_key(f, *args, **kwargs)
            else:
                key = self.cache_key

            return key

        wrapper.uncached = f
        wrapper.ttl = self.ttl
        wrapper.make_cache_key = make_cache_key

        return wrapper


class Cache:
    def __init__(self):
        # register cached attr
        self.cached = cached
        self._client = self.cached.client

    def __getattr__(self, name):
        return getattr(self._client, name)
