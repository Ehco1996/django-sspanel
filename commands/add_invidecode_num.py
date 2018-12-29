def add_user_invitecode_num():
    from apps.sspanel.models import User

    for user in User.objects.all():
        user.invitecode_num = 10
        user.save()
    print("job is down")


if __name__ == "__main__":
    from importlib import import_module

    import_module("__init__", "commands")
    add_user_invitecode_num()
