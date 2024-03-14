import hashlib
import json
import random
import re
import time
from functools import wraps

import pendulum
from django import forms
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone


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
        return str(round((traffic / 1024.0), 1)) + "KB"

    if traffic < 1024 * 1024 * 1024:
        return str(round((traffic / (1024.0 * 1024)), 1)) + "MB"

    return str(round((traffic / 1073741824.0), 1)) + "GB"


def traffic_rate_format(traffic):
    return f"{traffic_format(traffic)}/s"


def api_authorized(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = request.GET.get("token", "")
        if token != settings.TOKEN:
            return JsonResponse({"msg": "auth error"})
        return view_func(request, *args, **kwargs)

    return wrapper


def handle_json_request(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kw):
        if request.headers.get("Content-Type") != "application/json":
            return
        try:
            request.json = json.loads(request.body)
        except Exception:
            return JsonResponse({"msg": "bad request"}, status=400)
        return view_func(request, *args, **kw)

    return wrapper


def get_current_datetime() -> pendulum.DateTime:
    return pendulum.now(tz=timezone.get_current_timezone())


def gen_datetime_list(t: pendulum.DateTime, days: int = 6):
    """根据日期和天数生成日期列表"""
    return [t.subtract(days=i) for i in range(days, -1, -1)]


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    else:
        return request.META.get("REMOTE_ADDR")


def is_ip_address(addr):
    ip_pattern = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    return bool(re.match(ip_pattern, addr))


class BytesToGigabytesField(forms.CharField):
    def prepare_value(self, value):
        # 将字节转换为GB用于显示
        if value is None:
            return None
        return value / (1024**3)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            return int(float(value) * (1024**3))
        except (ValueError, TypeError):
            raise forms.ValidationError("请输入有效的GB数值")
