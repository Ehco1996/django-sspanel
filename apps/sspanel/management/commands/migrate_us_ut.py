from django.core.management.base import BaseCommand
from apps.sspanel.models import User, UserTraffic, UserSSConfig


class Command(BaseCommand):
    help = "将usertraffic 和 userssconfig 的数据洗到user表里"

    def handle(self, *args, **options):

        for user in User.objects.all():
            us = UserSSConfig.get_by_user_id(user.pk)
            ut = UserTraffic.get_by_user_id(user.pk)

            user.ss_port = us.port
            user.ss_password = us.password
            user.ss_method = us.method

            user.upload_traffic = ut.upload_traffic
            user.download_traffic = ut.download_traffic
            user.total_traffic = ut.total_traffic
            user.last_use_time = ut.last_use_time
            user.save()
            print(f"migrate user:{user}")
