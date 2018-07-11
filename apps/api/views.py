import time
import datetime
from random import randint

from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required

from apps.payments import alipay
from apps.constants import NODE_USER_INFO_TTL
from apps.utils import (get_date_list, traffic_format, simple_cached_view,
                        get_node_user, authorized)
from apps.ssserver.models import (SSUser, TrafficLog, Node, NodeOnlineLog,
                                  AliveIp)
from apps.sspanel.models import (InviteCode, PurchaseHistory, RebateRecord,
                                 Goods, User, MoneyCode, Donate, PayRecord,
                                 PayRequest)


@permission_required('sspanel')
def userData(request):
    '''
    返回用户信息：
    在线人数、今日签到、从未签到、从未使用
    '''

    data = [
        NodeOnlineLog.totalOnlineUser(),
        len(User.todayRegister()),
        SSUser.userTodyChecked(),
        SSUser.userNeverChecked(),
        SSUser.userNeverUsed(),
    ]
    return JsonResponse({'data': data})


@permission_required('sspanel')
def nodeData(request):
    '''
    返回节点信息
    所有节点名
    各自消耗的流量
    '''
    nodeName = [node.name for node in Node.objects.filter(show=1)]

    nodeTraffic = [
        round(node.used_traffic / settings.GB, 2)
        for node in Node.objects.filter(show=1)
    ]

    data = {
        'nodeName': nodeName,
        'nodeTraffic': nodeTraffic,
    }
    return JsonResponse(data)


@permission_required('sspanel')
def donateData(request):
    '''
    返回捐赠信息
    捐赠笔数
    捐赠总金额
    '''
    data = [Donate.totalDonateNums(), int(Donate.totalDonateMoney())]
    return JsonResponse({'data': data})


@login_required
def change_ss_port(request):
    '''
    随机重置用户用端口
    返回是否成功
    '''
    user = request.user.ss_user
    # 找到端口池中最大的端口
    port = SSUser.randomPord()
    user.port = port
    user.save()
    registerinfo = {
        'title': '修改成功！',
        'subtitle': '端口修改为：{}！'.format(port),
        'status': 'success',
    }
    return JsonResponse(registerinfo)


@login_required
def gen_invite_code(request):
    '''
    生成用户的邀请码
    返回是否成功
    '''
    u = request.user
    if u.is_superuser is True:
        # 针对管理员特出处理，每次生成5个邀请码
        num = 5
    else:
        num = u.invitecode_num - len(InviteCode.objects.filter(code_id=u.pk))
    if num > 0:
        for i in range(num):
            code = InviteCode(code_type=0, code_id=u.pk)
            code.save()
        registerinfo = {
            'title': '成功',
            'subtitle': '添加邀请码{}个,请刷新页面'.format(num),
            'status': 'success',
        }
    else:
        registerinfo = {
            'title': '失败',
            'subtitle': '已经不能生成更多的邀请码了',
            'status': 'error',
        }
    return JsonResponse(registerinfo)


@login_required
def purchase(request):
    '''
    购买商品的逻辑
    返回是否成功
    '''
    if request.method == "POST":
        user = request.user
        ss_user = user.ss_user
        goodId = request.POST.get('goodId')
        good = Goods.objects.get(pk=goodId)
        if user.balance < good.money:
            registerinfo = {
                'title': '金额不足！',
                'subtitle': '请去捐赠界面/联系站长充值',
                'status': 'error',
            }
        else:
            # 验证成功进行提权操作
            ss_user.enable = True
            ss_user.transfer_enable += good.transfer
            user.balance -= good.money
            if (user.level == good.level
                    and user.level_expire_time > datetime.datetime.now()):
                user.level_expire_time += datetime.timedelta(days=good.days)
            else:
                user.level_expire_time = datetime.datetime.now() \
                    + datetime.timedelta(days=good.days)
            user.level = good.level
            user.save()
            ss_user.save()
            # 增加购买记录
            record = PurchaseHistory(
                good=good,
                user=user,
                money=good.money,
                purchtime=timezone.now())
            record.save()
            # 增加返利记录
            inviter = User.objects.get(pk=user.invited_by)
            rebaterecord = RebateRecord(
                user_id=inviter.pk,
                money=good.money * Decimal(settings.INVITE_PERCENT))
            inviter.balance += rebaterecord.money
            inviter.save()
            rebaterecord.save()
            registerinfo = {
                'title': '购买成功',
                'subtitle': '请在用户中心检查最新信息',
                'status': 'success',
            }
            # 删除缓存
        return JsonResponse(registerinfo)
    else:
        return HttpResponse('errors')


@login_required
def pay_request(request):
    '''
    当面付请求逻辑
    '''
    amount = int(request.POST.get('num'))

    if amount < 1:
        info = {
            'title': '失败',
            'subtitle': '请保证金额大于1元',
            'status': 'error',
        }
    else:
        req = PayRequest.make_pay_request(request.user, amount)
        if req is not None:
            info = {
                'title': '请求成功！',
                'subtitle': '支付宝扫描下方二维码付款，付款完成记得按确认哟！',
                'status': 'success',
            }
        else:
            info = {
                'title': '糟糕，当面付插件可能出现问题了',
                'subtitle': '如果一直失败,请后台联系站长',
                'status': 'error',
            }
    return JsonResponse({'info': info})


@login_required
def pay_query(request):
    '''
    当面付结果查询逻辑
    '''
    user = request.user
    info_code = PayRequest.get_user_recent_pay_req(user).info_code
    paid = PayRequest.pay_query(user, info_code)
    if paid:
        info = {
            'title': '充值成功！',
            'subtitle': '请去商品界面购买商品！',
            'status': 'success',
        }
    else:
        info = {
            'title': '支付查询失败！请稍候再试',
            'subtitle': '亲，确认支付了么？',
            'status': 'error',
        }
    return JsonResponse({'info': info})


@login_required
def traffic_query(request):
    '''
    流量查请求
    '''
    node_id = request.POST.get('node_id', 0)
    node_name = request.POST.get('node_name', '')
    user_id = request.user.ss_user.user_id
    last_week = get_date_list(7)
    labels = ['{}-{}'.format(t.month, t.day) for t in last_week]
    trafficdata = [
        TrafficLog.getTrafficByDay(node_id, user_id, t) for t in last_week
    ]
    title = '节点 {} 当月共消耗：{} GB'.format(node_name,
                                       TrafficLog.getUserTraffic(
                                           node_id, user_id))
    configs = {
        'title': title,
        'labels': labels,
        'data': trafficdata,
        'data_title': node_name,
        'x_label': '日期 最近七天',
        'y_label': '流量 单位：GB'
    }
    return JsonResponse(configs)


@login_required
def change_theme(request):
    '''
    更换用户主题
    '''
    theme = request.POST.get('theme', 'default')
    user = request.user
    user.theme = theme
    user.save()
    registerinfo = {
        'title': '修改成功！',
        'subtitle': '主题更换成功，刷新页面可见',
        'status': 'success',
    }
    return JsonResponse(registerinfo)


@authorized
@csrf_exempt
@require_http_methods(['POST'])
def get_invitecode(request):
    '''
    获取邀请码接口
    只开放给管理员账号
    返回一个没用过的邀请码
    需要验证token
    '''
    admin_user = User.objects.filter(is_superuser=True).first()
    code = InviteCode.objects.filter(
        code_id=admin_user.pk, isused=False).first()
    if code:
        return JsonResponse({'msg': code.code})
    else:
        return JsonResponse({'msg': '邀请码用光啦'})


@authorized
@simple_cached_view()
@require_http_methods(['GET'])
def node_api(request, node_id):
    '''
    返回节点信息
    筛选节点是否用光
    '''
    node = Node.objects.filter(node_id=node_id).first()
    if node and node.used_traffic < node.total_traffic:
        data = (node.traffic_rate, )
    else:
        data = None
    res = {'ret': 1, 'data': data}
    return JsonResponse(res)


@authorized
@csrf_exempt
@require_http_methods(['POST'])
def node_online_api(request):
    '''
    接受节点在线人数上报
    '''
    data = request.json
    node = Node.objects.filter(node_id=data['node_id']).first()
    if node:
        NodeOnlineLog.objects.create(
            node_id=data['node_id'],
            online_user=data['online_user'],
            log_time=int(time.time()))
    res = {'ret': 1, 'data': []}
    return JsonResponse(res)


@authorized
@simple_cached_view(ttl=NODE_USER_INFO_TTL)
@require_http_methods(['GET'])
def user_api(request, node_id):
    '''
    返回符合节点要求的用户信息
    '''
    data = get_node_user(node_id)
    res = {'ret': 1, 'data': data}
    return JsonResponse(res)


@authorized
@csrf_exempt
@require_http_methods(['POST'])
def traffic_api(request):
    '''
    接受服务端的用户流量上报
    '''
    data = request.json
    node_id = data['node_id']
    traffic_list = data['data']
    log_time = int(time.time())

    node_total_traffic = 0
    trafficlog_model_list = []
    for rec in traffic_list:
        ss_user = SSUser.objects.filter(pk=rec['user_id']).first()
        # 个人流量更新
        SSUser.objects.filter(pk=rec['user_id']).update(
            upload_traffic=(ss_user.upload_traffic + rec['u']),
            download_traffic=(ss_user.download_traffic + rec['d']),
            last_use_time=log_time)
        # 个人流量记录
        trafficlog_model_list.append(
            TrafficLog(node_id=node_id, user_id=rec['user_id'],
                       traffic=traffic_format(rec['u'] + rec['d']),
                       download_traffic=rec['d'], upload_traffic=rec['u'],
                       log_time=log_time))
        node_total_traffic = node_total_traffic + rec['u'] + rec['d']
    # 节点流量记录
    node = Node.objects.get(node_id=node_id)
    node.used_traffic += node_total_traffic
    node.save()
    # 个人流量记录
    TrafficLog.objects.bulk_create(trafficlog_model_list)
    return JsonResponse({'ret': 1, 'data': []})


@authorized
@csrf_exempt
@require_http_methods(['POST'])
def alive_ip_api(request):
    data = request.json
    node_id = data['node_id']
    model_list = []
    for user_id, ip_list in data['data'].items():
        user = SSUser.objects.get(pk=user_id).user
        for ip in ip_list:
            model_list.append(AliveIp(node_id=node_id, user=user, ip=ip))
    AliveIp.objects.bulk_create(model_list)
    res = {'ret': 1, 'data': []}
    return JsonResponse(res)


@login_required
def checkin(request):
    '''用户签到'''
    ss_user = request.user.ss_user
    if not ss_user.get_check_in():
        # 距离上次签到时间大于一天 增加随机流量
        ll = randint(settings.MIN_CHECKIN_TRAFFIC,
                     settings.MAX_CHECKIN_TRAFFIC)
        ss_user.transfer_enable += ll
        ss_user.last_check_in_time = timezone.now()
        ss_user.save()
        data = {
            'title': '签到成功！',
            'subtitle': '获得{}流量！'.format(traffic_format(ll)),
            'status': 'success',
        }
    else:
        data = {
            'title': '签到失败！',
            'subtitle': '距离上次签到不足一天',
            'status': 'error',
        }
    return JsonResponse(data)
