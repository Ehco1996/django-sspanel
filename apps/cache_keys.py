def apply_decorator(cls):
    def decorator(cls, func):
        def wrapper(*args, **kwargs):
            module_name = cls.__module__
            if module_name.endswith('.cache_keys'):
                module_name = module_name.rsplit('.', 1)[0]

            function_name = func.__name__[len('key_of_'):]

            return '.'.join([module_name, function_name,
                             str(func(*args, **kwargs) or '')])

        return wrapper

    for key, value in cls.__dict__.items():
        if key.startswith('key_of_'):
            setattr(cls, key, staticmethod(decorator(cls, value)))
    return cls


@apply_decorator
class CacheKey:

    def key_of_node_user(node_id):
        return node_id
