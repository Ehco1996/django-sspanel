from django.contrib.auth.management.commands import createsuperuser

from apps.sspanel.models import SSNode, User, UserTraffic, VmessNode


class Command(createsuperuser.Command):
    def handle(self, *args, **options):
        levels = sorted(
            list(
                set(
                    [node.level for node in SSNode.objects.all()]
                    + [node.level for node in VmessNode.objects.all()]
                )
            )
        )
        # 去掉0级的
        levels.remove(0)
        print("now levels", levels)
        # migrate user
        for user in User.objects.all():
            if user.level > 0:
                level_0_ut = UserTraffic.get_by_user_id_and_level(user.id, 0)
                for level in levels:
                    ut = UserTraffic(user_id=user.id, level=level)
                    if level == user.level:
                        ut.download_traffic = level_0_ut.download_traffic
                        ut.upload_traffic = level_0_ut.upload_traffic
                        ut.total_traffic = level_0_ut.total_traffic
                        ut.last_use_time = level_0_ut.last_use_time
                    ut.save()
                level_0_ut.reset_traffic(0)
                level_0_ut.save()
                print(f"migrate user:{user}")
