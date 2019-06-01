def migrate_ss_users():
    from apps.sspanel.models import UserSSConfig, UserTraffic
    from apps.ssserver.models import Suser

    for ss_user in Suser.objects.all():
        UserSSConfig.objects.create(
            user_id=ss_user.user_id,
            port=ss_user.port,
            password=ss_user.password,
            enable=ss_user.enable,
            speed_limit=ss_user.speed_limit,
            method=ss_user.method,
        )
        UserTraffic.objects.create(
            user_id=ss_user.user_id,
            upload_traffic=ss_user.upload_traffic,
            download_traffic=ss_user.download_traffic,
            total_traffic=ss_user.transfer_enable,
        )
        print(f"migrate user_id {ss_user.user_id} down!")


if __name__ == "__main__":
    from importlib import import_module

    import_module("__init__", "commands")
    migrate_ss_users()
