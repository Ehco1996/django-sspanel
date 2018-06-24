from django.conf import settings
from django.utils import timezone

from apps.sspanel.models import User
from apps.ssserver.models import (Node, NodeInfoLog, NodeOnlineLog,
                                  TrafficLog, AliveIp)


def check_user_state():
    '''检测用户状态，将所有账号到期的用户状态重置'''
    users = User.objects.filter(level__gt=0)
    for user in users:
        # 判断用户过期
        if timezone.now() - timezone.timedelta(days=1) > \
                user.level_expire_time:
            user.level = 0
            user.save()
            user.ss_user.enable = False
            user.ss_user.upload_traffic = 0
            user.ss_user.download_traffic = 0
            user.ss_user.transfer_enable = settings.DEFAULT_TRAFFIC
            user.ss_user.save()
            logs = 'time: {} user: {} level timeout ' \
                .format(timezone.now().strftime('%Y-%m-%d'),
                        user.username).encode('utf8')
            print(logs)
    print('Time: {} CHECKED'.format(timezone.now()))


def auto_reset_traffic():
    '''重置所有免费用户流量'''
    users = User.objects.filter(level=0)

    for user in users:
        user.ss_user.download_traffic = 0
        user.ss_user.upload_traffic = 0
        user.ss_user.transfer_enable = settings.DEFAULT_TRAFFIC
        user.ss_user.save()
        logs = 'user {}  traffic reset! '.format(
            user.username).encode('utf8')
        print(logs)


def clean_traffic_log():
    '''清空所有流量记录'''
    res = TrafficLog.objects.all().delete()
    log = str(res)
    print('all traffic record removed!:{}'.format(log))


def clean_online_log():
    '''清空所有在线记录'''
    res = NodeOnlineLog.objects.all().delete()
    log = str(res)
    print('all online record removed!:{}'.format(log))


def clean_node_log():
    '''清空所有节点负载记录'''
    res = NodeInfoLog.objects.all().delete()
    log = str(res)
    print('all node info record removed!:{}'.format(log))


def clean_online_ip_log():
    '''清空在线ip记录'''
    res = AliveIp.objects.all().delete()
    log = str(res)
    print('Today: {} all online ip log removed!:{}'.format(timezone.now(),
                                                           log))


def reset_node_traffic():
    '''月初重置节点使用流量'''
    for node in Node.objects.all():
        node.used_traffic = 0
        node.save()
    print('all node traffic removed!')
