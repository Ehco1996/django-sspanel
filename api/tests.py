import json
from django.test import TestCase, Client

from ssserver.models import Node


class TestBase(TestCase):

    def setUp(self):
        self.client = Client()
        self.token = 'ZWhjbysyMzQ1'

    def client_post(self, url, data):
        new_url = url + '?token={}'.format(self.token)
        res = self.client.post(new_url, data)
        return res.status_code, res.content

    def client_get(self, url):
        res = self.client.get(url, {'token': self.token})
        return res.status_code, json.loads(res.content)


class ApiTest(TestBase):

    def setUp(self):
        super().setUp()
        self.base_url = 'http://127.0.0.1:8000/api/'
        Node.objects.create(node_id=1, name='test server', server='1.1.1.1')

    def test_get_invitecode_api(self):
        url = self.base_url + 'get/invitecode/'
        status_code, _ = self.client_get(url)
        self.assertEqual(status_code, 200)

    def test_node_api(self):
        url = self.base_url+'nodes/1'
        status_code, res = self.client_get(url)
        ret = res['ret']
        self.assertEqual(status_code, 200)
        self.assertEqual(ret, 1)

    def test_user_api(self):
        url = self.base_url+'users/nodes/1'
        status_code, res = self.client_get(url)
        ret = res['ret']
        self.assertEqual(status_code, 200)
        self.assertEqual(ret, 1)
