"""
这里定义了一些计划任务
可以手动执行，也可以放到crontab job里去用

ex:
    python print_user_count.py
"""

import os
import sys
from os.path import dirname, abspath

import django


def ready():
    """ready for cmds"""
    path = dirname((abspath(dirname(__file__))))
    sys.path.insert(0, path)
    env = os.getenv("DJANGO_ENV", "development")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configs.{}".format(env))
    django.setup()


ready()
