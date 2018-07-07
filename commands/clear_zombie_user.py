
from django.core.exceptions import ObjectDoesNotExist


def clear_zombie_user():
    '''
    删除僵尸用户
    '''
    from apps.sspanel.models import User
    users = User.objects.all()
    count = 0
    for user in users:
        try:
            if user.ss_user.last_use_time == 0 and user.balance == 0:
                user.delete()
                count += 1
        except ObjectDoesNotExist:
            user.delete()
            count += 1
    print('clear user count: ', count)


if __name__ == '__main__':
    from importlib import import_module
    import_module('__init__', 'commands')
    clear_zombie_user()
