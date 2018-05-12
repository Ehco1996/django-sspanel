import time
import random
import hashlib
from functools import wraps
from datetime import datetime, timedelta

from django.core.cache import cache

from apps.constants import DEFUALT_CACHE_TTL
from apps.cache_keys import CacheKey as cache_keys


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


def clear_node_user_cache():
    from apps.ssserver.models import Node
    node_ids = Node.objects.filter(show=1).values_list('node_id', flat=True)
    for node_id in node_ids:
        key = cache_keys.key_of_node_user(node_id)
        cache.delete(key)


def get_node_user(node_id):
    '''
    返回所有当前节点可以使用的用户信息
    '''
    from apps.ssserver.models import Node, SSUser
    key = cache_keys.key_of_node_user(node_id)
    data = cache.get(key)
    if data:
        return data
    node = Node.objects.filter(node_id=node_id).first()
    if node:
        data = []
        level = node.level
        user_list = SSUser.objects.filter(
            level__gte=level, transfer_enable__gte=0)
        for user in user_list:
            cfg = {'port': user.port,
                   'u': user.upload_traffic,
                   'd': user.download_traffic,
                   'transfer_enable': user.transfer_enable,
                   'passwd': user.password,
                   'enable': user.enable,
                   'id': user.pk,
                   'method': user.method,
                   'obfs': user.obfs,
                   'obfs_param': user.obfs_param,
                   'protocol': user.protocol,
                   'protocol_param': user.protocol_param,
                   }
            if node.node_type == 1:
                cfg.update({
                    'passwd': node.password,
                    'method': node.method,
                    'obfs': node.obfs,
                    'protocol': node.protocol,
                    'protocol_param': '{}:{}'.format(user.port, user.password)
                })
            data.append(cfg)
        cache.set(key, data, DEFUALT_CACHE_TTL)
        return data
