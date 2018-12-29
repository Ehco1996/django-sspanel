import time
import json
import random
import hashlib
from functools import wraps

import pendulum
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

from apps.constants import DEFUALT_CACHE_TTL
from apps.cachext import make_default_key


def get_random_string(
    length=12,
    allowed_chars="abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
):
    """
    创建指定长度的完全不会重复字符串的
    """
    random.seed(
        hashlib.sha256(
            ("%s%s%s" % (random.getstate(), time.time(), "SCRWEWYOURBITCHES")).encode(
                "utf-8"
            )
        ).digest()
    )
    return "".join(random.choice(allowed_chars) for i in range(length))


def get_long_random_string():
    return get_random_string(24)


def get_short_random_string():
    return get_random_string(12)


def traffic_format(traffic):
    if traffic < 1024 * 8:
        return str(int(traffic)) + "B"

    if traffic < 1024 * 1024:
        return str(round((traffic / 1024.0), 2)) + "KB"

    if traffic < 1024 * 1024 * 1024:
        return str(round((traffic / (1024.0 * 1024)), 2)) + "MB"

    return str(round((traffic / 1073741824.0), 2)) + "GB"


def reverse_traffic(str):
    """
    将流量字符串转换为整数类型
    """
    if "GB" in str:
        num = float(str.replace("GB", "")) * 1024 * 1024 * 1024
    elif "MB" in str:
        num = float(str.replace("MB", "")) * 1024 * 1024
    elif "KB" in str:
        num = float(str.replace("KB", "")) * 1024
    else:
        num = num = float(str.replace("B", ""))
    return round(num)


def simple_cached_view(key=None, ttl=None):
    def decorator(func):
        @wraps(func)
        def cached_view(*agrs, **kwagrs):
            cache_key = key if key else make_default_key(func, *agrs, **kwagrs)
            cache_ttl = ttl if ttl else DEFUALT_CACHE_TTL
            resp = cache.get(cache_key)
            if resp:
                return resp
            else:
                resp = func(*agrs, **kwagrs)
                cache.set(cache_key, resp, cache_ttl)
                return resp

        return cached_view

    return decorator


def authorized(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method == "GET":
            token = request.GET.get("token", "")
        else:
            data = json.loads(request.body)
            token = data.get("token", "")
            request.json = data
        if token == settings.TOKEN:
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({"ret": -1, "msg": "auth error"})

    return wrapper


def get_node_user(node_id):
    """
    返回所有当前节点可以使用的用户信息
    """
    from apps.ssserver.models import Node, Suser

    node = Node.objects.filter(node_id=node_id).first()
    if node:
        data = []
        level = node.level
        user_list = Suser.get_vaild_user(level)
        for user in user_list:
            cfg = {
                "port": user.port,
                "u": user.upload_traffic,
                "d": user.download_traffic,
                "transfer_enable": user.transfer_enable,
                "passwd": user.password,
                "enable": user.enable,
                "user_id": user.user_id,
                "id": user.user_id,
                "method": user.method,
                "obfs": user.obfs,
                "obfs_param": user.obfs_param,
                "protocol": user.protocol,
                "protocol_param": user.protocol_param,
                "speed_limit_per_user": user.speed_limit,
            }
            if node.speed_limit > 0:
                if user.speed_limit > 0:
                    cfg["speed_limit_per_user"] = min(
                        user.speed_limit, node.speed_limit
                    )
                else:
                    cfg["speed_limit_per_user"] = node.speed_limit

            data.append(cfg)
        return data


def get_current_time():
    return pendulum.now(tz=settings.TIME_ZONE)


def global_settings(request):
    global_variable = {"USE_SMTP": settings.USE_SMTP}

    return global_variable
