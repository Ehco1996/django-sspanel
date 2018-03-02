import time
import json
import base64
import datetime

import qrcode
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.utils.six import BytesIO
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required


from shadowsocks.tools import get_date_list
from shadowsocks.tools import traffic_format
from shadowsocks.payments import alipay, pay91
from ssserver.models import SSUser, TrafficLog, Node, NodeOnlineLog, AliveIp
from shadowsocks.models import (Donate, InviteCode, PurchaseHistory,
                                RebateRecord, Shop, User, MoneyCode, Donate, PayRequest, PayRecord)


@permission_required('shadowsocks')
def userData(request):
    '''
    返回用户信息：
    在线人数、今日签到、从未签到、从未使用
    '''

    data = [NodeOnlineLog.totalOnlineUser(), len(User.todayRegister()),
            SSUser.userTodyChecked(), SSUser.userNeverChecked(), SSUser.userNeverUsed(), ]
    return JsonResponse({'data': data})


@permission_required('shadowsocks')
def nodeData(request):
    '''
    返回节点信息
    所有节点名
    各自消耗的流量
    '''
    nodeName = [node.name for node in Node.objects.filter(show='显示')]

    nodeTraffic = [
        round(node.used_traffic/settings.GB, 2) for node in Node.objects.filter(show='显示')]

    data = {
        'nodeName': nodeName,
        'nodeTraffic': nodeTraffic,
    }
    return JsonResponse(data)


@permission_required('shadowsocks')
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
    if u.pk == 1:
        # 针对管理员特出处理，每次生成5个邀请码
        num = 5
    else:
        num = u.invitecode_num - len(InviteCode.objects.filter(code_id=u.pk))
    if num > 0:
        for i in range(num):
            code = InviteCode(type=0, code_id=u.pk)
            code.save()

        registerinfo = {
            'title': '成功',
            'subtitle': '添加邀请码{}个,请刷新页面'.format(num),
            'status': 'success', }
    else:
        registerinfo = {
            'title': '失败',
            'subtitle': '已经不能生成更多的邀请码了',
            'status': 'error', }
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
        good = Shop.objects.get(pk=goodId)
        if user.balance < good.money:
            registerinfo = {
                'title': '金额不足！',
                'subtitle': '请去捐赠界面/联系站长充值',
                'status': 'error', }
        else:
            # 验证成功进行提权操作
            ss_user.enable = True
            ss_user.transfer_enable += good.transfer
            user.balance -= good.money
            user.level = good.level
            if user.level_expire_time < datetime.datetime.now():
                user.level_expire_time = datetime.datetime.now() + datetime.timedelta(days=good.days)
            else:
                user.level_expire_time += datetime.timedelta(days=good.days)
            user.save()
            ss_user.save()
            # 增加购买记录
            record = PurchaseHistory(info=good, user=user, money=good.money,
                                     purchtime=timezone.now())
            record.save()
            # 增加返利记录
            inviter = User.objects.get(pk=user.invited_by)
            rebaterecord = RebateRecord(
                user_id=inviter.pk, money=good.money * Decimal(settings.INVITE_PERCENT))
            inviter.balance += rebaterecord.money
            inviter.save()
            rebaterecord.save()
            registerinfo = {
                'title': '购买成功',
                'subtitle': '请在用户中心检查最新信息',
                'status': 'success', }
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
            'status': 'error', }
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
                timeout_express='60s',)
            # 获取二维码链接
            code_url = trade.get('qr_code', '')
            request.session['code_url'] = code_url
            request.session['out_trade_no'] = out_trade_no
            request.session['amount'] = amount
            info = {
                'title': '请求成功！',
                'subtitle': '支付宝扫描下方二维码付款，付款完成记得按确认哟！',
                'status': 'success', }
            context['info'] = info
        except:
            res = alipay.api_alipay_trade_cancel(
                out_trade_no=out_trade_no)
            info = {
                'title': '糟糕，当面付插件可能出现问题了',
                'subtitle': '如果一直失败,请后台联系站长',
                'status': 'error', }
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
        donate = Donate.objects.create(user=user, money=amount)
        # 后台数据库增加记录
        record = PayRecord.objects.create(username=user,
                                          info_code=trade_num, amount=amount, money_code=code)
        del request.session['out_trade_no']
        # 返回充值信息
        info = {
            'title': '充值成功！',
            'subtitle': '请去商品界面购买商品！',
            'status': 'success', }
        context['info'] = info

    # 如果三次还没成功择关闭订单
    if paid is False:
        alipay.api_alipay_trade_cancel(out_trade_no=trade_num)
        info = {
            'title': '支付查询失败！',
            'subtitle': '亲，确认支付了么？',
            'status': 'error', }
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
    last_week = get_date_list(6)
    labels = ['{}-{}'.format(t.month, t.day) for t in last_week]
    trafficdata = [TrafficLog.getTrafficByDay(
        node_id, user_id, t) for t in last_week]
    title = '节点 {} 当月共消耗：{} GB'.format(node_name,
                                       TrafficLog.getUserTraffic(node_id, user_id))
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
def get_qrcode(request, content):
    '''返回字符串编码后的二维码图片'''
    # 加入节点信息等级判断
    ss_img = qrcode.make(content)
    buf = BytesIO()
    ss_img.save(buf)
    image_stream = buf.getvalue()
    # 构造图片reponse
    response = HttpResponse(image_stream, content_type="image/png")
    return response


@csrf_exempt
def pay_notify(request):
    '''
    保存91pay的回掉信息入数据库
    '''
    if request.method == 'POST':
        data = request.POST
        try:
            code = MoneyCode.objects.create(number=data['money'])
            record = PayRecord.objects.create(username=data['pay_id'],
                                              info_code=data['pay_no'], amount=data['money'], money_code=code, type=data['type'])
            return HttpResponse('ok')
        except:
            return HttpResponse('error')
    else:
        return HttpResponse('error')


@login_required
def pay91_request(request):
    '''
    91pay请求逻辑
    '''
    try:
        data = request.POST
        context = {}
        # 获取金额数量
        amount = data['paynum']
        type = data['type']
        # 生成订单号
        pay_id = '{}@{}@{}@{}'.format(request.user.pk, settings.HOST, settings.ALIPAY_NUM,
                                      datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S%s'))
        res = pay91.pay_request(type, amount, pay_id)
        request.session['pay_id'] = pay_id
        # 记录申请记录
        record = PayRequest.objects.create(username=request.user.username,
                                           info_code=res['trade_no'],
                                           amount=amount, type=res['type'])
        # 获取二维码链接
        context['qrcode'] = res['qrcode']
        info = {
            'title': '请求成功！',
            'subtitle': '描下方二维码付款，付款完成记得按确认哟！',
            'status': 'success', }
        context['info'] = info
    except:
        info = {
            'title': '糟糕，当面付插件可能出现问题了',
            'subtitle': '如果一直失败,请后台联系站长',
            'status': 'error', }
        context['info'] = info
    return JsonResponse(context)


@login_required
def pay91_query(request):
    '''
    91pay结果查询逻辑
    rtype:
        json
    '''
    context = {}
    user = request.user
    paid = False
    pay_id = request.session['pay_id']
    # 等待1秒在查询
    time.sleep(1)
    res = PayRecord.objects.filter(username=pay_id)
    if len(res) == 1:
        rec = res[0]
        code = MoneyCode.objects.get(code=rec.money_code)
        user.balance += code.number
        user.save()
        code.user = user.username
        code.isused = True
        code.save()
        # 将充值记录和捐赠绑定
        donate = Donate.objects.create(user=user, money=rec.amount)
        # 后台数据库增加记录
        del request.session['pay_id']
        paid = True
        # 返回充值信息
        info = {
            'title': '充值成功！',
            'subtitle': '请去商品界面购买商品！',
            'status': 'success', }
        context['info'] = info
    else:
        paid = False
    if paid is False:
        info = {
            'title': '支付查询失败！',
            'subtitle': '亲，确认支付了么？',
            'status': 'error', }
        context['info'] = info
    return JsonResponse(context)


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


@csrf_exempt
def get_invitecode(request):
    '''
    获取邀请码接口
    只开放给管理员账号（user_id=1）
    只接受post请求
    返回一个没用过的邀请码
    需要验证token
    token为 base64(username+port)
    '''
    if request.method == 'POST':
        token = request.POST.get('token', '')
        if token == settings.TOKEN:
            code = InviteCode.objects.filter(code_id=1, isused=False)
            if len(code) > 1:
                return JsonResponse({'msg': code[0].code})
            else:
                return JsonResponse({'msg': '邀请码用光啦'})
        else:
            return JsonResponse({'msg': 'auth error'})
    else:
        return JsonResponse({'msg': 'method error'})


@require_http_methods(['GET', ])
def node_api(request, node_id):
    '''
    返回节点信息
    筛选节点是否用光
    '''
    token = request.GET.get('token', '')
    if token == settings.TOKEN:
        node = Node.objects.filter(node_id=node_id)
        if len(node) > 0 and node[0].used_traffic < node[0].total_traffic:
            data = (node[0].traffic_rate,)
        else:
            data = None
        re_dict = {'ret': 1,
                   'data': data}
    else:
        re_dict = {'ret': -1}
    return JsonResponse(re_dict)


@require_http_methods(['POST', ])
@csrf_exempt
def node_online_api(request):
    '''
    接受节点在线人数上报
    '''
    token = request.GET.get('token', '')
    if token == settings.TOKEN:
        data = json.loads(request.body)
        node = Node.objects.filter(node_id=data['node_id'])
        if len(node) > 0:
            NodeOnlineLog.objects.create(
                node_id=data['node_id'], online_user=data['online_user'], log_time=round(time.time()))
        else:
            data = None
        re_dict = {'ret': 1,
                   'data': []}
    else:
        re_dict = {'ret': -1}
    return JsonResponse(re_dict)


@require_http_methods(['GET', ])
def user_api(request, node_id):
    '''
    返回符合节点要求的用户信息
    '''
    token = request.GET.get('token', '')
    if token == settings.TOKEN:
        node = Node.objects.filter(node_id=node_id)
        if len(node) > 0:
            data = []
            level = node[0].level
            user_list = SSUser.objects.filter(
                level__gte=level, transfer_enable__gte=0)
            for user in user_list:
                cfg = {'port': user.port,
                       'u': user.upload_traffic,
                       'd': user.download_traffic,
                       'transfer_enable': user.transfer_enable,
                       'passwd': user.password,
                       'enable': user.enable,
                       'id': user.pk,
                       'method': user.method,
                       'obfs': user.obfs,
                       'protocol': user.protocol}
                data.append(cfg)
        else:
            data = None
        re_dict = {'ret': 1,
                   'data': data}
    else:
        re_dict = {'ret': -1}
    return JsonResponse(re_dict)


@csrf_exempt
@require_http_methods(['POST', ])
def traffic_api(request):
    '''
    接受服务端的用户流量上报
    '''
    token = request.GET.get('token', '')
    if token == settings.TOKEN:
        traffic_rec_list = json.loads(request.body)['data']
        node_id = json.loads(request.body)['node_id']
        node = Node.objects.get(node_id=node_id)
        traffic_pool = 0
        for rec in traffic_rec_list:
            #  用户流量流量记录
            user = SSUser.objects.get(pk=rec['user_id'])
            user.upload_traffic += rec['u']
            user.download_traffic += rec['d']
            user.save()
            traffic = traffic_format(rec['u'] + rec['d'])
            TrafficLog.objects.create(
                node_id=node_id, user_id=rec['user_id'], traffic=traffic, download_traffic=rec['d'], upload_traffic=rec['u'], log_time=round(time.time()))
            traffic_pool = traffic_pool + int(rec['u'])+int(rec['d'])
        # 节点流量记录
        node.used_traffic = node.used_traffic + traffic_pool
        node.save()
        re_dict = {'ret': 1, 'data': []}
    else:
        re_dict = {'ret': -1}
    return JsonResponse(re_dict)


@csrf_exempt
@require_http_methods(['POST', ])
def alive_ip_api(request):
    token = request.GET.get('token', '')
    if token == settings.TOKEN:
        data = json.loads(request.body)['data']
        node_id = json.loads(request.body)['node_id']
        for user, ip_list in data.items():
            user = SSUser.objects.get(pk=user).user
            for ip in ip_list:
                AliveIp.objects.create(node_id=node_id, user=user, ip=ip)
        re_dict = {'ret': 1, 'data': []}
    else:
        re_dict = {'ret': -1}
    return JsonResponse(re_dict)
