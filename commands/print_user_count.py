from datetime import datetime

try:
    from __init__ import *
except ModuleNotFoundError:
    print('doing auto  django-crontab job Time:{}'.format(datetime.now()))


def print_user_count():
    from apps.sspanel.models import User
    print('total user count is : {}'.format(User.objects.all().count()))


if __name__ == '__main__':
    print_user_count()
