import pendulum
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.sspanel.models import (
    NodeOnlineLog,
    SSNode,
    User,
    UserOnLineIpLog,
    UserOrder,
    UserTrafficLog,
    VmessNode,
)


class Command(BaseCommand):
    help = "执行cronjob"

    def add_arguments(self, parser):
        parser.add_argument(
            "--jobname",
            help="check_user_state auto_reset_traffic reset_node_traffic "
            "make_up_lost_order clean_traffic_log clean_node_online_log"
            "clean_online_ip_log",
        )

    def handle(self, *args, **options):

        job_name = options.get("jobname")
        if not job_name:
            raise CommandError("--jobname are required options")
        job_func = getattr(self, job_name, None)
        if not job_func:
            raise CommandError(f"job: {job_name} not found")

        now = pendulum.now().strftime("%Y-%m-%d %H:%M")
        print(f"RUNNING JOB: {job_name} .... Time: {now}")
        job_func()

    def check_user_state(self):
        """检测用户状态，将所有账号到期的用户状态重置"""
        User.check_and_disable_expired_users()
        User.check_and_disable_out_of_traffic_user()

    def auto_reset_traffic(self):
        """重置所有免费用户流量"""
        for user in User.objects.filter(level=0):
            user.reset_traffic(settings.DEFAULT_TRAFFIC)

    def reset_node_traffic(self):
        """月初重置节点使用流量"""
        for node in SSNode.objects.all():
            node.used_traffic = 0
            node.save()

        for node in VmessNode.objects.all():
            node.used_traffic = 0
            node.save()

    def make_up_lost_order(self):
        """定时补单"""
        UserOrder.make_up_lost_orders()

    def clean_traffic_log(self):
        """清空七天前的所有流量记录"""
        dt = pendulum.now().subtract(days=7).date()
        query = UserTrafficLog.objects.filter(date__lt=dt)
        count, res = query.delete()
        print(f"UserTrafficLog  removed count:{count}")

    def clean_node_online_log(self):
        """清空所有在线记录"""
        count = NodeOnlineLog.objects.count()
        NodeOnlineLog.truncate()
        print(f"NodeOnlineLog  removed count:{count}")

    def clean_online_ip_log(self):
        """清空在线ip记录"""
        count = UserOnLineIpLog.objects.count()
        UserOnLineIpLog.truncate()
        print(f"UserOnLineIpLog  removed count:{count}")
