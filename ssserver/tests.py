from django.test import TestCase
from ssserver.models import SSUser
from shadowsocks.models import User
from ssserver.views import auto_reset_traffic, check_user_state
from random import randint

# Create your tests here.


def auto_register(num, level=0):
    '''自动注册num个用户'''

    for i in range(num):
        username = 'test' + str(i)
        code = 'testcode' + str(i)
        User.objects.create_user(
            username=username, email=None, password=None, level=level, invitecode=code)
        user = User.objects.get(username=username)
        port = randint(10, 9999)
        ss_user = SSUser.objects.create(user=user, port=port)


class CrontabTestCase(TestCase):
    '''测试用户流量重置和有效期检测是否正常'''

    def setUp(self):
        auto_register(2, 1)

    def test_check_user_state_can_work(self):
        check_user_state()

    def test_auto_reset_traffic_can_work(self):
        auto_reset_traffic()
