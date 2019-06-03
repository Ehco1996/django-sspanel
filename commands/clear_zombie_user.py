from django.core.exceptions import ObjectDoesNotExist


def clear_zombie_user():
    """
    删除僵尸用户
    """
    from apps.sspanel.models import User, UserTraffic

    for ut in UserTraffic.objects.all():
        if ut.last_use_time == UserTraffic.DEFAULT_USE_TIME:
            user = User.get_by_pk(ut.user_id)
            if user.balance == 0 and user.level > 0:
                user.delete()
                print(f"delete zombie user {user.username}")


if __name__ == "__main__":
    from importlib import import_module

    import_module("__init__", "commands")
    clear_zombie_user()
