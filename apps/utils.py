import time
import random
import hashlib
from functools import wraps
from datetime import datetime, timedelta

from django.core.cache import cache

from apps.constants import DEFUALT_CACHE_TTL


def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                      'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    '''
    创建指定长度的完全不会重复字符串的
    '''
    random.seed(
        hashlib.sha256(
            ("%s%s%s" % (
                random.getstate(),
                time.time(),
                'SCRWEWYOURBITCHES')).encode('utf-8')
        ).digest())
    return ''.join(random.choice(allowed_chars) for i in range(length))


def get_long_random_string():
    return get_random_string(24)


def get_short_random_string():
    return get_random_string(12)


def get_date_list(dela):
    '''
    返回从当前日期开始回溯指定天数的日期列表
    '''
    t = datetime.today()
    date_list = [t - timedelta(days=i) for i in range(dela)]
    return list(reversed(date_list))


def traffic_format(traffic):
    if traffic < 1024 * 8:
        return str(int(traffic)) + "B"

    if traffic < 1024 * 1024:
        return str(round((traffic / 1024.0), 2)) + "KB"

    if traffic < 1024 * 1024 * 1024:
        return str(round((traffic / (1024.0 * 1024)), 2)) + "MB"

    return str(round((traffic / 1073741824.0), 2)) + "GB"


def reverse_traffic(str):
    '''
    将流量字符串转换为整数类型
    '''
    if 'GB' in str:
        num = float(str.replace('GB', '')) * 1024 * 1024 * 1024
    elif 'MB' in str:
        num = float(str.replace('MB', '')) * 1024 * 1024
    elif 'KB' in str:
        num = float(str.replace('KB', '')) * 1024
    else:
        num = num = float(str.replace('B', ''))
    return round(num)


def simple_cached_view(key=None, ttl=None):
    def decorator(func):
        cache_key = key if key else func.__name__
        cache_ttl = ttl if ttl else DEFUALT_CACHE_TTL
        @wraps(func)
        def cached_view(*agrs, **kwagrs):
            resp = cache.get(cache_key)
            if resp:
                return resp
            else:
                resp = func(*agrs, **kwagrs)
                cache.set(cache_key, resp, cache_ttl)
                return resp
        return cached_view
    return decorator
