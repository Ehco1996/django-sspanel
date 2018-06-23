import time
import datetime

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
                                 Goods, User, MoneyCode, Donate, PayRecord)


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
    num = int(request.POST.get('num', ''))
    context = {}
    if num < 1:
        info = {
            'title': '失败',
            'subtitle': '请保证金额大于1元',
            'status': 'error',
        }
        context['info'] = info
    else:
        out_trade_no = datetime.datetime.fromtimestamp(
            time.time()).strftime('%Y%m%d%H%M%S%s')
        try:
            # 获取金额数量
            amount = num
            # 生成订单
            trade = alipay.api_alipay_trade_precreate(
                subject=settings.ALIPAY_TRADE_INFO.format(amount),
                out_trade_no=out_trade_no,
                total_amount=amount,
                timeout_express='60s',
            )
            # 获取二维码链接
            code_url = trade.get('qr_code', '')
            request.session['code_url'] = code_url
            request.session['out_trade_no'] = out_trade_no
            request.session['amount'] = amount
            info = {
                'title': '请求成功！',
                'subtitle': '支付宝扫描下方二维码付款，付款完成记得按确认哟！',
                'status': 'success',
            }
            context['info'] = info
        except:
            alipay.api_alipay_trade_cancel(out_trade_no=out_trade_no)
            info = {
                'title': '糟糕，当面付插件可能出现问题了',
                'subtitle': '如果一直失败,请后台联系站长',
                'status': 'error',
            }
            context['info'] = info
    return JsonResponse(context)


@login_required
def pay_query(request):
    '''
    当面付结果查询逻辑
    rtype:
        json
    '''
    context = {}
    user = request.user
    trade_num = request.session['out_trade_no']
    paid = False
    # 等待1秒后再查询支付结果
    time.sleep(1)
    res = alipay.api_alipay_trade_query(out_trade_no=trade_num)
    if res.get("trade_status", "") == "TRADE_SUCCESS":
        paid = True
        amount = Decimal(res.get("total_amount", 0))
        # 生成对于数量的充值码
        code = MoneyCode.objects.create(number=amount)
        # 充值操作
        user.balance += code.number
        user.save()
        code.user = user.username
        code.isused = True
        code.save()
        # 将充值记录和捐赠绑定
        Donate.objects.create(user=user, money=amount)
        # 后台数据库增加记录
        PayRecord.objects.create(
            username=user, info_code=trade_num, amount=amount, money_code=code)
        del request.session['out_trade_no']
        # 返回充值信息
        info = {
            'title': '充值成功！',
            'subtitle': '请去商品界面购买商品！',
            'status': 'success',
        }
        context['info'] = info

    # 如果三次还没成功择关闭订单
    if paid is False:
        alipay.api_alipay_trade_cancel(out_trade_no=trade_num)
        info = {
            'title': '支付查询失败！',
            'subtitle': '亲，确认支付了么？',
            'status': 'error',
        }
        context['info'] = info
    return JsonResponse(context)


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
    traffic_rec_list = data['data']
    # 定义循环池
    node_total_traffic = 0
    trafficlog_model_list = []
    log_time = int(time.time())
    for rec in traffic_rec_list:
        res = SSUser.objects.filter(pk=rec['user_id']).values_list(
            'upload_traffic', 'download_traffic')[0]
        SSUser.objects.filter(pk=rec['user_id']).update(
            upload_traffic=(res[0] + rec['u']),
            download_traffic=(res[1] + rec['d']),
            last_use_time=log_time)
        traffic = traffic_format(rec['u'] + rec['d'])
        trafficlog_model_list.append(
            TrafficLog(
                node_id=node_id,
                user_id=rec['user_id'],
                traffic=traffic,
                download_traffic=rec['d'],
                upload_traffic=rec['u'],
                log_time=log_time))
        node_total_traffic = node_total_traffic + rec['u'] + rec['d']
    # 节点流量记录
    node = Node.objects.get(node_id=node_id)
    node.used_traffic += node_total_traffic
    node.save()
    # 个人流量记录
    TrafficLog.objects.bulk_create(trafficlog_model_list)
    res = {'ret': 1, 'data': []}
    return JsonResponse(res)


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
