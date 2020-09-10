from alipay import AliPay
from alipay.utils import AliPayConfig
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
            config=AliPayConfig(timeout=3),
        )

    def trade_precreate(
        self, out_trade_no, total_amount, subject, timeout_express, notify_url
    ):
        return self.alipay.api_alipay_trade_precreate(
            out_trade_no=out_trade_no,
            total_amount=total_amount,
            subject=subject,
            timeout_express=timeout_express,
            notify_url=notify_url,
        )

    def trade_query(self, out_trade_no):
        return self.alipay.api_alipay_trade_query(out_trade_no=out_trade_no)

    def verify(self, data, signature):
        return self.alipay.verify(data=data, signature=signature)
