from django.core.management.base import BaseCommand, CommandError

from apps.sspanel import tasks
from apps.utils import get_current_datetime


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

        now = get_current_datetime().strftime("%Y-%m-%d %H:%M")
        print(f"RUNNING JOB: {job_name} .... Time: {now}")
        job_func()

    def check_user_state(self):
        """检测用户状态，将所有账号到期的用户状态重置"""
        tasks.check_user_state_task()

    def auto_reset_free_user_traffic(self):
        """重置所有免费用户流量"""
        tasks.auto_reset_free_user_traffic_task()

    def reset_node_traffic(self):
        """重置节点使用流量"""
        tasks.reset_node_traffic_task()

    def make_up_lost_order(self):
        """定时补单"""
        tasks.make_up_lost_order_task()

    def clean_traffic_log(self):
        """清空七天前的所有流量记录"""
        tasks.clean_traffic_log_task()

    def clean_node_online_log(self):
        """清空所有在线记录"""
        tasks.clean_node_online_log_task()

    def clean_online_ip_log(self):
        """清空在线ip记录"""
        tasks.clean_online_ip_log_task()
