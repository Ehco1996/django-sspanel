from alipay import AliPay

from django.conf import settings


class Pay:
    def __init__(self):
        if not settings.USE_ALIPAY:
            return
        # NOTE 暂时只支持支付宝
        self.alipay = AliPay(
            app_notify_url="",
            appid=settings.ALIPAY_APP_ID,
            app_private_key_string=settings.ALIPAY_APP_PRIVATE_KEY_STRING,
            alipay_public_key_string=settings.ALIPAY_PUBLIC_KEY_STRING,
        )
