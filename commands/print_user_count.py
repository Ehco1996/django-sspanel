def print_user_count():
    from apps.sspanel.models import User
    print('total user count is : {}'.format(User.objects.all().count()))


if __name__ == '__main__':
    from importlib import import_module
    import_module('__init__', 'commands')
    print_user_count()
