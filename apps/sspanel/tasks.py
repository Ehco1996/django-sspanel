from urllib.error import URLError

from django.conf import settings
from django.core.mail import send_mail

from apps import celery_app
from apps.proxy.models import ProxyNode, UserProxyNodeOccupancy, UserTrafficLog
from apps.sspanel import models as m
from apps.utils import get_current_datetime


@celery_app.task
def debug_task():
    u = m.User.objects.first()
    print("i am in debug", u)


@celery_app.task
def sync_user_traffic_task(node_id, data):
    """
    这个接口操作比较重，所以为了避免发信号
    所有写操作都需要用BULK的方式
    1 更新节点流量
    2 更新用户流量
    3 记录节点在线IP
    4 关闭超出流量的节点
    """
    node: ProxyNode = ProxyNode.get_or_none(node_id)
    if not node:
        return
    node_occurred_user_ids = [
        i["user_id"] for i in UserProxyNodeOccupancy.get_node_occupancy_user_ids(node)
    ]
    node_total_traffic = 0
    log_time = get_current_datetime()
    user_model_list = []
    trafficlog_model_list = []
    traffic_data = data.get("data", [])

    # load user in batch
    user_ids = []
    for user_data in traffic_data:
        user_id = user_data["user_id"]
        user_ids.append(user_data["user_id"])
    user_map = {}
    for u in m.User.objects.filter(id__in=user_ids):
        user_map[u.id] = u

    for user_data in traffic_data:
        user_id = int(user_data["user_id"])
        user = user_map[user_id]
        u = int(int(user_data["upload_traffic"]) * node.enlarge_scale)
        d = int(int(user_data["download_traffic"]) * node.enlarge_scale)

        # 节点流量增量
        node_total_traffic += u + d

        # 记录用户占用节点流量
        if user_id in node_occurred_user_ids:
            UserProxyNodeOccupancy.check_and_incr_traffic(
                user_id=user_id, proxy_node_id=node_id, traffic=d + u
            )
        else:
            # 个人流量增量
            user.download_traffic += d
            user.upload_traffic += u
            user.last_use_time = log_time
            user_model_list.append(user)
        # 流量记录
        trafficlog_model_list.append(
            UserTrafficLog(
                proxy_node=node,
                user=user,
                download_traffic=u,
                upload_traffic=d,
                ip_list=user_data.get("ip_list", []),
            )
        )

    if not traffic_data:
        # NOTE add blank log to show node is online
        trafficlog_model_list.append(UserTrafficLog(proxy_node=node))
    # 节点流量记录
    node.used_traffic += node_total_traffic
    if node.overflow:
        node.enable = False
    node.current_used_download_bandwidth_bytes = int(data.get("download_bandwidth", 0))
    node.current_used_upload_bandwidth_bytes = int(data.get("upload_bandwidth", 0))
    node.save(
        update_fields=[
            "used_traffic",
            "enable",
            "current_used_download_bandwidth_bytes",
            "current_used_upload_bandwidth_bytes",
        ]
    )
    # 用户流量
    m.User.objects.bulk_update(
        user_model_list,
        [
            "download_traffic",
            "upload_traffic",
            "last_use_time",
        ],
    )
    # 流量记录
    UserTrafficLog.objects.bulk_create(trafficlog_model_list)


@celery_app.task
def check_user_state_task():
    """检测用户状态，将所有账号到期的用户状态重置"""
    m.User.check_and_disable_expired_users()
    m.User.check_and_disable_out_of_traffic_user()


@celery_app.task
def auto_reset_free_user_traffic_task():
    """重置所有免费用户流量"""
    for user in m.User.objects.filter(level=0):
        user.reset_traffic(settings.DEFAULT_TRAFFIC)


@celery_app.task
def reset_node_traffic_task():
    """重置节点使用流量"""
    for node in ProxyNode.objects.all():
        node.used_traffic = 0
        node.save()


@celery_app.task
def make_up_lost_order_task():
    """定时补单"""
    try:
        m.UserOrder.make_up_lost_orders()
    except URLError:
        # Note请求支付宝挂了，等下次retry就好
        pass


@celery_app.task
def clean_traffic_log_task():
    """清空七天前的所有流量记录"""
    dt = get_current_datetime().subtract(days=7)
    query = UserTrafficLog.objects.filter(created_at__lt=dt)
    count = query._raw_delete(query.db)
    print(f"UserTrafficLog  removed count:{count}")


@celery_app.task
def send_mail_to_users_task(user_id_list, subject, message):
    users = m.User.objects.filter(id__in=user_id_list)
    address = [user.email for user in users]
    if send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, address):
        logs = [
            m.EmailSendLog(user=user, subject=subject, message=message)
            for user in users
        ]
        m.EmailSendLog.objects.bulk_create(logs)
        print(f"send email success user: address: {address}")
    else:
        raise Exception(f"Could not send mail {address} subject: {subject}")


@celery_app.task
def close_stale_tickets_task():
    m.Ticket.close_stale_tickets()
