'''
api性能测试工具
'''

import logging
import threading
import time
from random import randint

import requests


class EhcoApi(object):
    '''
    提供发送get/post的抽象类
    '''

    def __init__(self):
        self.session_pool = requests.Session()
        self.TOKEN = 'ZWhjbysyMzQ1'
        self.WEBAPI_URL = 'http://127.0.0.1:8000/api'

    def getApi(self, uri):
        res = None
        try:
            payload = {'token': self.TOKEN}
            url = self.WEBAPI_URL+uri
            res = self.session_pool.get(url, params=payload, timeout=10)
            time.sleep(0.005)
            try:
                data = res.json()
            except Exception:
                if res:
                    logging.error('接口返回值格式错误: {}'.format(res.text))
                return []

            if data['ret'] == -1:
                logging.error("接口返回值不正确:{}".format(res.text))
                logging.error("请求头：{}".format(uri))
                return []
            return data['data']

        except Exception:
            import traceback
            trace = traceback.format_exc()
            logging.error(trace)
            raise Exception(
                '网络问题，请保证api接口地址设置正确！当前接口地址：{}'.format(self.WEBAPI_URL))

    def postApi(self, uri, raw_data={}):
        res = None
        try:
            payload = {'token': self.TOKEN}
            url = self.WEBAPI_URL+uri
            res = self.session_pool.post(
                url, params=payload, json=raw_data, timeout=10)
            time.sleep(0.01)
            try:
                data = res.json()
            except Exception:
                if res:
                    logging.error('接口返回值格式错误: {}'.format(res.text))
                return []
            if data['ret'] == -1:
                logging.error("接口返回值不正确:{}".format(res.text))
                logging.error("请求头：{}".format(uri))
                return []
            return data['data']
        except Exception:
            import traceback
            trace = traceback.format_exc()
            logging.error(trace)
            raise Exception(
                '网络问题，请保证api接口地址设置正确！当前接口地址：{}'.format(self.WEBAPI_URL))

    def close(self):
        self.session_pool.close()


class TestUserApi(object):

    def __init__(self):
        self.api = EhcoApi()
        self.id = id(self.api)
        print('当前实例id：{}'.format(self.id))

    def test_user_api(self, times=100):
        '''
        测试用户配置数据
        '''
        for i in range(0, times):
            uri = '/users/nodes/1'
            self.api.getApi(uri)
            print('当前测试ID：{} 第 {}次调用getApi'.format(self.id, i))


class TestTrafficApi(object):
    def __init__(self):
        self.api = EhcoApi()
        self.id = id(self.api)
        print('当前实例id：{}'.format(self.id))

    def gen_fake_traffic_data(self):
        '''
        生成流量数据
        '''
        data = []
        for i in range(randint(1, 100)):
            data.append({'u': randint(999, 99999),
                         'd': randint(999, 99999),
                         'user_id': 1})
        return data

    def test_traffic_api(self, data={}, times=100):
        '''
        测试流量上报接口
        '''
        uri = '/traffic/upload'
        for i in range(times):
            data = {
                'node_id': 1,
                'data': self.gen_fake_traffic_data()}
            self.api.postApi(uri, data)
            print('当前测试ID：{} 第 {}次调用postApi'.format(self.id, i))


def main_test(thread_num=10):
    # for i in range(thread_num):
    #     user_api_test = TestUserApi()
    #     thread = threading.Thread(
    #         target=user_api_test.test_user_api)
    #     thread.start()

    for i in range(thread_num):
        traffic_api_test = TestTrafficApi()
        thread = threading.Thread(
            target=traffic_api_test.test_traffic_api)
        thread.start()


if __name__ == '__main__':
    import os
    print('当前的进程id为：', os.getpid())
    main_test(20)
