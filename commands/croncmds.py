import pendulum
from django.conf import settings
from django.utils import timezone

from apps.sspanel.models import User, PayRequest
from apps.ssserver.models import Node, NodeOnlineLog, TrafficLog, AliveIp
from django.core.mail import send_mail


def check_user_state():
    '''检测用户状态，将所有账号到期的用户状态重置'''
    users = User.objects.filter(level__gt=0)
    expire_user = []
    for user in users:
        # 判断用户过期
        if timezone.now() - timezone.timedelta(days=1) > \
                user.level_expire_time:
            user.level = 0
            user.save()
            ss_user = user.ss_user
            ss_user.enable = False
            ss_user.upload_traffic = 0
            ss_user.download_traffic = 0
            ss_user.transfer_enable = settings.DEFAULT_TRAFFIC
            ss_user.save()
            expire_user.append(user.email)
            print('time: {} user: {} level timeout '
                  .format(timezone.now().strftime('%Y-%m-%d'),
                          user.username))
    if expire_user and settings.:
        send_mail('您的{0}账号已到期'.format(settings.TITLE),
                  "您的{0}账号已到期，现被暂停使用。如需继续使用请前往 {1} 充值".format(settings.TITLE, settings.HOST),
                  settings.DEFAULT_FROM_EMAIL,
                  expire_user)
    print('Time: {} CHECKED'.format(timezone.now()))


def auto_reset_traffic():
    '''重置所有免费用户流量'''
    users = User.objects.filter(level=0)

    for user in users:
        ss_user = user.ss_user
        ss_user.download_traffic = 0
        ss_user.upload_traffic = 0
        ss_user.transfer_enable = settings.DEFAULT_TRAFFIC
        ss_user.save()
    print('Time {} all free user traffic reset! '.format(timezone.now()))


def clean_traffic_log():
    '''清空七天前的所有流量记录'''
    dt = pendulum.now().subtract(days=7).date()
    query = TrafficLog.objects.filter(log_date__lt=dt)
    count, res = query.delete()
    print('Time: {} traffic record removed!:{}'.format(timezone.now(), count))


def clean_online_log():
    '''清空所有在线记录'''
    count = TrafficLog.objects.count()
    NodeOnlineLog.truncate()
    print('Time {} online record removed!:{}'.format(timezone.now(), count))


def clean_online_ip_log():
    '''清空在线ip记录'''
    count = TrafficLog.objects.count()
    AliveIp.truncate()
    print('Time: {} online ip log removed!:{}'.format(timezone.now(), count))


def reset_node_traffic():
    '''月初重置节点使用流量'''
    for node in Node.objects.all():
        node.used_traffic = 0
        node.save()
    print('Time: {} all node traffic removed!'.format(timezone.now()))


def check_pay_request():
    '''定时检查支付请求'''
    # 每次检查新的五条记录
    querys = PayRequest.objects.order_by('-time')[:5]
    for req in querys:
        user = User.objects.filter(username=req.username).first()
        paid = PayRequest.pay_query(user, req.info_code)
        if paid is True:
            print('用户：{} 掉单，已经补偿'.format(user.username))
    print('{} 检查过支付请求'.format(timezone.now().strftime("%Y-%m-%d %H:%M")))
