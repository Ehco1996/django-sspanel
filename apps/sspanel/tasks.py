from django.conf import settings

from apps import celery_app
from apps.sspanel import models as m
from apps.utils import get_current_datetime


@celery_app.task
def debug_task():
    u = m.User.objects.first()
    print("i am in debug", u)


@celery_app.task
def sync_user_ss_traffic_task(node_id, data):
    """
        这个接口操作比较重，所以为了避免发信号
        所有写操作都需要用BULK的方式
        1 更新节点流量
        2 更新用户流量
        3 记录节点在线IP
        4 关闭超出流量的节点
        """
    ss_node = m.SSNode.get_or_none_by_node_id(node_id)
    if not ss_node:
        return
    node_total_traffic = 0
    log_time = get_current_datetime()
    active_tcp_connections = 0
    need_clear_cache = False
    user_model_list = []
    trafficlog_model_list = []
    online_ip_log_model_list = []

    for user_data in data:
        user_id = user_data["user_id"]
        u = int(user_data["upload_traffic"] * ss_node.enlarge_scale)
        d = int(user_data["download_traffic"] * ss_node.enlarge_scale)
        # 个人流量增量
        user = m.User.get_by_pk(user_id)
        user.download_traffic += d
        user.upload_traffic += u
        user.last_use_time = log_time
        user_model_list.append(user)
        if user.overflow or user.level < ss_node.level:
            need_clear_cache = True
        # 个人流量记录
        trafficlog_model_list.append(
            m.UserTrafficLog(
                node_type=m.UserTrafficLog.NODE_TYPE_SS,
                node_id=node_id,
                user_id=user_id,
                download_traffic=u,
                upload_traffic=d,
            )
        )
        # 节点流量增量
        node_total_traffic += u + d
        # active_tcp_connections
        active_tcp_connections += user_data["tcp_conn_num"]
        # online ip log
        for ip in user_data.get("ip_list", []):
            online_ip_log_model_list.append(
                m.UserOnLineIpLog(user_id=user_id, node_id=node_id, ip=ip)
            )

    # 用户流量
    m.User.objects.bulk_update(
        user_model_list, ["download_traffic", "upload_traffic", "last_use_time"],
    )
    # 节点流量记录
    m.SSNode.increase_used_traffic(node_id, node_total_traffic)
    # 流量记录
    m.UserTrafficLog.objects.bulk_create(trafficlog_model_list)
    # 在线IP
    m.UserOnLineIpLog.objects.bulk_create(online_ip_log_model_list)
    # 节点在线人数
    m.NodeOnlineLog.add_log(
        m.NodeOnlineLog.NODE_TYPE_SS, node_id, len(data), active_tcp_connections
    )
    # check node && user traffic
    if ss_node.overflow:
        ss_node.enable = False
    if need_clear_cache or ss_node.overflow:
        ss_node.save()


@celery_app.task
def sync_user_vmess_traffic_task(node_id, data):
    node = m.VmessNode.get_or_none_by_node_id(node_id)
    if not node:
        return

    log_time = get_current_datetime()
    node_total_traffic = 0
    need_clear_cache = False
    trafficlog_model_list = []
    user_model_list = []

    for log in data:
        user_id = log["user_id"]
        u = int(log["ut"] * node.enlarge_scale)
        d = int(log["dt"] * node.enlarge_scale)
        # 个人流量增量
        user = m.User.get_by_pk(user_id)
        user.download_traffic += d
        user.upload_traffic += u
        user.last_use_time = log_time
        user_model_list.append(user)
        if user.overflow or user.level < node.level:
            need_clear_cache = True
        # 个人流量记录
        trafficlog_model_list.append(
            m.UserTrafficLog(
                node_type=m.UserTrafficLog.NODE_TYPE_VMESS,
                node_id=node_id,
                user_id=user_id,
                download_traffic=u,
                upload_traffic=d,
            )
        )
        # 节点流量增量
        node_total_traffic += u + d
    # 节点流量记录
    m.VmessNode.increase_used_traffic(node_id, node_total_traffic)
    # 流量记录
    m.UserTrafficLog.objects.bulk_create(trafficlog_model_list)
    # 个人流量记录
    m.User.objects.bulk_update(
        user_model_list, ["download_traffic", "upload_traffic", "last_use_time"],
    )
    # 节点在线人数
    m.NodeOnlineLog.add_log(m.NodeOnlineLog.NODE_TYPE_VMESS, node_id, len(data))
    # check node && user traffic
    if node.overflow:
        node.enable = False
    if need_clear_cache or node.overflow:
        node.save()


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
    for node in m.SSNode.objects.all():
        node.used_traffic = 0
        node.save()

    for node in m.VmessNode.objects.all():
        node.used_traffic = 0
        node.save()


@celery_app.task
def make_up_lost_order_task():
    """定时补单"""
    m.UserOrder.make_up_lost_orders()


@celery_app.task
def clean_traffic_log_task():
    """清空七天前的所有流量记录"""
    dt = get_current_datetime().subtract(days=7).date()
    query = m.UserTrafficLog.objects.filter(date__lt=dt)
    count, res = query.delete()
    print(f"UserTrafficLog  removed count:{count}")


@celery_app.task
def clean_node_online_log_task():
    """清空所有在线记录"""
    count = m.NodeOnlineLog.objects.count()
    m.NodeOnlineLog.truncate()
    print(f"NodeOnlineLog  removed count:{count}")


@celery_app.task
def clean_online_ip_log_task():
    """清空在线ip记录"""
    count = m.UserOnLineIpLog.objects.count()
    m.UserOnLineIpLog.truncate()
    print(f"UserOnLineIpLog  removed count:{count}")
