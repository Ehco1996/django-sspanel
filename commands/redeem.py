def pay_redeem():
    '''给大于3级的用户每人发10元'''
    from apps.sspanel.models import User
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
