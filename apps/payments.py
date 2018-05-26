import os
from alipay import AliPay
'''
支付宝相关设置
'''
# APPID
APPID = '2016103002422776'
path = os.path.split(os.path.realpath(__file__))[0]
# Pub pem path
PUBLIC_KEY_PATH = path + '/Alipay_pub.pem'
# Private pem path
PRIVATE_KEY_PATH = path + '/App_pravite.pem'
# 支付宝支付接口封装
alipay = AliPay(
    appid=APPID,
    app_notify_url="",
    app_private_key_path=PRIVATE_KEY_PATH,
    # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
    alipay_public_key_path=PUBLIC_KEY_PATH,
    sign_type="RSA2",  # RSA 或者 RSA2
    debug=False,  # 默认False
)