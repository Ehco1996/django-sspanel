import json

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import HttpResponse, render

from shadowsocks.models import User, NodeOnlineLog, Node, Donate
from ssserver.models import SSUser, TrafficLog

# Create your views here.

@permission_required('shadowsocks')
def test(request):
    '''测试api'''

    data = {
        'user': [1, 2, 3, 4]
    }
    result = json.dumps(data, ensure_ascii=False)
    return HttpResponse(result, content_type='application/json')


@permission_required('shadowsocks')
def userData(request):
    '''
    返回用户信息：
    在线人数、今日签到、从未签到、从未使用
    '''

    data = [NodeOnlineLog.totalOnlineUser(),
            SSUser.userTodyChecked(), SSUser.userNeverChecked(), SSUser.userNeverUsed(), ]

    result = json.dumps(data, ensure_ascii=False)
    return HttpResponse(result, content_type='application/json')


@permission_required('shadowsocks')
def nodeData(request):
    '''
    返回节点信息
    所有节点名
    各自消耗的流量
    '''

    nodeName = [node.name for node in Node.objects.all()]
    nodeTraffic = [TrafficLog.totalTraffic(
        node.node_id) for node in Node.objects.all()]

    data = {
        'nodeName': nodeName,
        'nodeTraffic': nodeTraffic,
    }
    result = json.dumps(data, ensure_ascii=False)
    return HttpResponse(result, content_type='application/json')


@permission_required('shadowsocks')
def donateData(request):
    '''
    返回捐赠信息
    捐赠笔数
    捐赠总金额
    '''
    data = [Donate.totalDonateNums(), int(Donate.totalDonateMoney())]

    result = json.dumps(data, ensure_ascii=False)
    return HttpResponse(result, content_type='application/json')
