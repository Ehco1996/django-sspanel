from uuid import uuid4


def gen_user_vmess_uuid():
    from apps.sspanel.models import User

    for user in User.objects.all():
        if not user.vmess_uuid:
            user.vmess_uuid = str(uuid4())
            user.save()
    print("job is down")


if __name__ == "__main__":
    from importlib import import_module

    import_module("__init__", "commands")
    gen_user_vmess_uuid()
