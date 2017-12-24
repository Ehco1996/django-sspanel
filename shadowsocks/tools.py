import random
import hashlib
import time
from datetime import datetime, timedelta


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
    '''返回从当前日期开始回溯指定天数的日期列表'''
    t = datetime.today()
    l = [t - timedelta(days=i) for i in range(dela + 1)]
    return list(reversed(l))
