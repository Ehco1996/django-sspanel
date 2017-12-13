import datetime
import time
import json
from decimal import Decimal
from random import randint

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import HttpResponse, render
from django.utils import timezone

from shadowsocks.models import (Donate, InviteCode, Node, NodeOnlineLog,
                                PurchaseHistory, RebateRecord, Shop, User, MoneyCode, Donate, AlipayRequest, AlipayRecord)

from ssserver.models import SSUser, TrafficLog

from shadowsocks.payments import alipay

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

    data = [NodeOnlineLog.totalOnlineUser(), len(User.todayRegister()),
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
    result = json.dumps(registerinfo, ensure_ascii=False)

    # AJAX 返回json数据
    return HttpResponse(result, content_type='application/json')


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

    result = json.dumps(registerinfo, ensure_ascii=False)

    return HttpResponse(result, content_type='application/json')


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
            user.level_expire_time = timezone.now() + datetime.timedelta(days=good.days)
            ss_user.save()
            user.save()
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

        result = json.dumps(registerinfo, ensure_ascii=False)
        return HttpResponse(result, content_type='application/json')
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

    result = json.dumps(context, ensure_ascii=False)
    return HttpResponse(result, content_type='application/json')


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
        record = AlipayRecord.objects.create(username=user,
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
    result = json.dumps(context, ensure_ascii=False)
    return HttpResponse(result, content_type='application/json')
