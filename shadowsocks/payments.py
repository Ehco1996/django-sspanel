import os
import json
import requests
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


'''
91pay 相关设置
'''
# 自己网站的域名
HOST = 'http://xx.com'
# 91pay的账号id
ID = 10700
# 91pay的token
TOKEN = 'AWHrqo7x8y2nf6n9pT0blkb4jkKZx96n'


class Pay91():
    '''
    91pay支付接口封装

    需要授权请联系：
    https://t.me/gh012363  或者QQ群538609570
    '''

    def __init__(self, id, token):
        '''
        agrgs：
            id : 支付授权id
            token:支付授权token
        都为必填参数
        '''
        self.id = id
        self.token = token
        self.notify_url = HOST + '/api/pay/notify/'

    def pay_request(self, type, price, pay_id):
        '''
        发起支付请求
        args:
            type ：支付类型<int>     1：支付宝 2：QQ钱包 3：微信支付。默认值：1
            prcie: 支付金额<float>： 最大值99999.99最小值0.01
            pay_id: 用户ID<str>    用户ID,订单ID,用户名确保是唯一
        return:
            <json>:
            {
            "type":1,    1：支付宝 2：QQ钱包 3：微信支付。默认值：1
            "money":"100.00", 实际付款金额
            "price":"100.00", 提交订单的原价
            "trade_no":"115162529341100410564924230",
            "status":0, 0：成功 -1:失败 -2:参数有误
            "msg":"ok", 返回的错误信息为英文
            "qrcode":"http://codepay.fateqq.com:52888/qr/1/1/100/0_0.png",qrcode
            ...
            }
        '''
        # 根据参数拼凑支付url
        url = 'http://codepay.fateqq.com:52888/creat_order?id={}&token={}&price={}&pay_id={}&type={}&page=4&notify_url={}'.format(
            self.id, self.token, price, pay_id, type, self.notify_url)
        # 模拟一个常见headers
        headers = {
            "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
        try:
            # 防止请求失败，我们重试三次
            t = 3
            while t > 0:
                r = requests.get(url, headers=headers)
                data = r.json()
                if data:
                    break
                else:
                    t -= 1
            if data:
                return data
            else:
                return {'msg': '接口调用失败，请检查id和token是否正确'}
        except:
            return {'msg': '接口调用失败，请检查id和token是否正确'}


pay91 = Pay91(ID, TOKEN)
