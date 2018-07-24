import sys


def pay_redeem():
    '''给大于3级的用户每人发10元'''
    from apps.sspanel.models import User
    user_check = input('即将给所有大于3级的用户发送10元红包，键入 y键 确认操作\n')
    if user_check != 'y':
        print('取消操作')
        sys.exit()

    users = User.objects.filter(level__gte=3)
    print('pay user count is: {}'.format(users.count()))
    for user in users:
        user.balance += 10
        user.save()
        print(user.username, 'balance + 10 down')


if __name__ == '__main__':
    from importlib import import_module
    import_module('__init__', 'commands')
    pay_redeem()
