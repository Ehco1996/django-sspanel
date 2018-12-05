import os
from alipay import AliPay

from django.conf import settings


# AppId
APPID = ''
path = os.path.split(os.path.realpath(__file__))[0]
# Pub pem path
PUBLIC_KEY_PATH = path + '/Alipay_pub.pem'
# Private pem path
PRIVATE_KEY_PATH = path + '/App_pravite.pem'


class Alipayments:

    def __init__(self, app_id, pub_key_path, pri_key_path):
        self.app_id = app_id
        self.pub_key_path = pub_key_path
        self.pri_key_path = pri_key_path
        self.alipay = None

        if settings.USE_ALIPAY:
            self.init_payment()

    def init_payment(self):
        self.alipay = AliPay(
            appid=APPID,
            app_notify_url="",
            app_private_key_path=PRIVATE_KEY_PATH,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=PUBLIC_KEY_PATH,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=False,  # 默认False
        )


pay = Alipayments(APPID, PUBLIC_KEY_PATH, PRIVATE_KEY_PATH)
