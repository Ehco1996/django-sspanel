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
