import os

import pendulum
from django.conf import settings
from django.utils import timezone

from apps.sspanel.models import (
    User,
    UserOrder,
    UserOnLineIpLog,
    UserTrafficLog,
    NodeOnlineLog,
    SSNode,
    UserTraffic,
)

os.environ["DJANGO_ENV"] = "production"


def check_user_state():
    """检测用户状态，将所有账号到期的用户状态重置"""
    User.check_and_disable_expired_users()
    UserTraffic.check_and_disable_out_of_traffic_user()
    print("CRONJOB: [check_user_state]")
    print("Time: {} CHECKED".format(timezone.now()))


def auto_reset_traffic():
    """重置所有免费用户流量"""
    users = User.objects.filter(level=0)

    for user in users:
        ut = UserTraffic.get_by_user_id(user.pk)
        ut.reset_traffic(settings.DEFAULT_TRAFFIC)
        ut.save()
    print("CRONJOB: [auto_reset_traffic]")
    print("Time {} all free user traffic reset! ".format(timezone.now()))


def clean_traffic_log():
    """清空七天前的所有流量记录"""
    dt = pendulum.now().subtract(days=7).date()
    query = UserTrafficLog.objects.filter(date__lt=dt)
    count, res = query.delete()
    print("CRONJOB: [clean_traffic_log]")
    print("Time: {} traffic record removed!:{}".format(timezone.now(), count))


def clean_online_log():
    """清空所有在线记录"""
    count = NodeOnlineLog.objects.count()
    NodeOnlineLog.truncate()
    print("CRONJOB: [clean_online_log]")
    print("Time {} online record removed!:{}".format(timezone.now(), count))


def clean_online_ip_log():
    """清空在线ip记录"""
    count = UserOnLineIpLog.objects.count()
    UserOnLineIpLog.truncate()
    print("CRONJOB: [clean_online_ip_log]")
    print("Time: {} online ip log removed!:{}".format(timezone.now(), count))


def reset_node_traffic():
    """月初重置节点使用流量"""
    for node in SSNode.objects.all():
        node.used_traffic = 0
        node.save()
    print("CRONJOB: [reset_node_traffic]")
    print("Time: {} all node traffic removed!".format(timezone.now()))


def make_up_lost_order():
    """定时补单"""
    UserOrder.make_up_lost_orders()
    print("CRONJOB: [make_up_lost_order]")
    print("{} 检查过支付请求".format(timezone.now().strftime("%Y-%m-%d %H:%M")))
