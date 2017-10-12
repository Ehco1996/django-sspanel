# 导入django内置模块
from django.shortcuts import render, render_to_response, redirect, HttpResponseRedirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.six import BytesIO
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic.list import ListView
from django.db.models import Q
from django.conf import settings
from decimal import Decimal
# 导入shadowsocks节点相关文件
from .models import Node, InviteCode, User, Aliveip, Donate, Shop, MoneyCode, PurchaseHistory, AlipayRecord, NodeOnlineLog, AlipayRequest, NodeInfoLog, Announcement, Ticket
from .forms import RegisterForm, LoginForm, NodeForm, ShopForm, AnnoForm

# 导入加密混淆协议选项
from .models import METHOD_CHOICES, PROTOCOL_CHOICES, OBFS_CHOICES

# 导入ssservermodel
from ssserver.models import SSUser, TrafficLog

# 导入第三方模块
import qrcode
import base64
import datetime
import time
import tomd
from random import randint
import json

# 导入支付宝当面付插件
from .payments import alipay


# Create your views here.

# 网站用户界面：

def index(request):
    '''跳转到首页'''
    return render(request, 'sspanel/index.html')


def sshelp(request):
    '''跳转到帮助界面'''
    return render(request, 'sspanel/help.html')


@login_required
def ssclient(request):
    '''跳转到客户端界面'''
    return render(request, 'sspanel/client.html')


def ssinvite(request):
    '''跳转到邀请码界面'''

    codelist = InviteCode.objects.filter(type='1')[:20]

    context = {'codelist': codelist, }

    return render(request, 'sspanel/invite.html', context=context)


def pass_invitecode(request, invitecode):
    '''提供点击邀请码连接之后自动填写邀请码'''
    form = RegisterForm(initial={'invitecode': invitecode})
    return render(request, 'sspanel/register.html', {'form': form})


def register(request):
    '''用户注册时的函数'''
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            # 获取用户填写的邀请码
            code = request.POST.get('invitecode')
            # 数据库查询邀请码
            code_query = InviteCode.objects.filter(code=code)
            # 判断邀请码是否存在并返回信息
            if len(code_query) == 0:
                registerinfo = {
                    'title': '邀请码失效',
                    'subtitle': '请重新获取邀请码',
                    'status': 'error',
                }
                context = {
                    'registerinfo': registerinfo,
                    'form': form,
                }
                return render(request, 'sspanel/register.html', context=context)

            else:
                registerinfo = {
                    'title': '注册成功！',
                    'subtitle': '请登录使用吧！',
                    'status': 'success',
                }
                context = {
                    'registerinfo': registerinfo
                }
                form.save()
                # 删除使用过的邀请码
                code_query.delete()
                # 将user和ssuser关联
                user = User.objects.get(username=request.POST.get('username'))
                max_port_user = SSUser.objects.order_by('-port').first()
                port = max_port_user.port + randint(2, 3)
                ss_user = SSUser.objects.create(user=user, port=port)
                return render(request, 'sspanel/index.html', context=context)

    else:
        form = RegisterForm()

    return render(request, 'sspanel/register.html', {'form': form})


def Login_view(request):
    '''用户登录函数'''
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # 获取表单用户名和密码
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # 进行用户验证
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                login(request, user)
                try:
                    anno = Announcement.objects.all()[0]
                except:
                    anno = None
                registerinfo = {
                    'title': '登录成功！',
                    'subtitle': '自动跳转到用户中心',
                    'status': 'success',
                }
                context = {
                    'registerinfo': registerinfo,
                    'anno': anno,

                }
                return render(request, 'sspanel/userinfo.html', context=context)
            else:
                form = LoginForm()
                registerinfo = {
                    'title': '登录失败！',
                    'subtitle': '请重新填写信息！',
                    'status': 'error',
                }
                context = {
                    'registerinfo': registerinfo,
                    'form': form,

                }
                return render(request, 'sspanel/login.html', context=context)
    else:
        form = LoginForm()
        return render(request, 'sspanel/login.html', {'form': form})


def Logout_view(request):
    '''用户登出函数'''
    logout(request)
    registerinfo = {
        'title': '注销成功！',
        'subtitle': '欢迎下次再来!！',
                    'status': 'success',
    }
    context = {
        'registerinfo': registerinfo,
    }

    return render(request, 'sspanel/index.html', context=context)


@login_required
def userinfo(request):
    '''用户中心'''
    user = request.user

    # 获取公告
    try:
        anno = Announcement.objects.all()[0]
    except:
        anno = None

    min_traffic = '{}m'.format(int(settings.MIN_CHECKIN_TRAFFIC / 1024 / 1024))
    max_traffic = '{}m'.format(int(settings.MAX_CHECKIN_TRAFFIC / 1024 / 1024))
    remain_traffic = 100 - eval(user.ss_user.get_used_percentage())
    context = {
        'user': user,
        'anno': anno,
        'remain_traffic': remain_traffic,
        'min_traffic': min_traffic,
        'max_traffic': max_traffic,
    }
    return render(request, 'sspanel/userinfo.html', context=context)


@login_required
def checkin(request):
    '''用户签到'''
    ss_user = request.user.ss_user
    try:
        anno = Announcement.objects.all()[0]
    except:
        anno = None

    if not ss_user.get_check_in():
        # 距离上次签到时间大于一天 增加随机流量
        ll = randint(settings.MIN_CHECKIN_TRAFFIC,
                     settings.MAX_CHECKIN_TRAFFIC)
        ss_user.transfer_enable += ll
        ss_user.last_check_in_time = timezone.now()
        ss_user.save()
        registerinfo = {
            'title': '签到成功！',
            'subtitle': '获得{}m流量！'.format(ll // settings.MB),
            'status': 'success', }
    else:
        registerinfo = {
            'title': '签到失败！',
            'subtitle': '距离上次签到不足一天',
            'status': 'error', }

    result = json.dumps(registerinfo, ensure_ascii=False)
    return HttpResponse(result, content_type='application/json')


@login_required
def get_ssr_qrcode(request, node_id):
    '''返回节点配置信息的ssr二维码'''

    # 获取用户对象
    ss_user = request.user.ss_user
    user = request.user
    # 获取节点对象
    node = Node.objects.get(node_id=node_id)
    # 加入节点信息等级判断
    if user.level < node.level:
        return HttpResponse('哟小伙子，可以啊！但是投机取巧是不对的哦！')

    # 符合ssr qrcode schema最后需要特殊处理的密码部分
    ssr_password = base64.b64encode(
        bytes(ss_user.password, 'utf8')).decode('ascii')
    ssr_code = '{}:{}:{}:{}:{}:{}'.format(
        node.server, ss_user.port, ss_user.protocol, ss_user.method, ss_user.obfs, ssr_password)
    # 将信息编码
    ssr_pass = base64.b64encode(bytes(ssr_code, 'utf8')).decode('ascii')
    # 生成ss二维码
    ssr_img = qrcode.make('ssr://{}'.format(ssr_pass))
    buf = BytesIO()
    ssr_img.save(buf)
    image_stream = buf.getvalue()
    # 构造图片reponse
    response = HttpResponse(image_stream, content_type="image/png")
    return response


@login_required
def get_ss_qrcode(request, node_id):
    '''返回节点配置信息的ss二维码'''

    # 获取用户对象
    ss_user = request.user.ss_user
    user = request.user
    # 获取节点对象
    node = Node.objects.get(node_id=node_id)
    # 加入节点信息等级判断
    if user.level < node.level:
        return HttpResponse('哟小伙子，可以啊！但是投机取巧是不对的哦！')
    ss_code = '{}:{}@{}:{}'.format(
        node.method, ss_user.password, node.server, ss_user.port)
    # 将信息编码
    ss_pass = base64.b64encode(bytes(ss_code, 'utf8')).decode('ascii')
    # 生成ss二维码
    ss_img = qrcode.make('ss://{}'.format(ss_pass))
    buf = BytesIO()
    ss_img.save(buf)
    image_stream = buf.getvalue()
    # 构造图片reponse
    response = HttpResponse(image_stream, content_type="image/png")
    return response


@login_required
def userinfo_edit(request):
    '''跳转到资料编辑界面'''
    ss_user = request.user.ss_user
    methods = [m[0] for m in METHOD_CHOICES]
    protocols = [p[0] for p in PROTOCOL_CHOICES]
    obfss = [o[0] for o in OBFS_CHOICES]

    context = {
        'ss_user': ss_user,
        'methods': methods,
        'protocols': protocols,
        'obfss': obfss,
    }
    return render(request, 'sspanel/userinfoedit.html', context=context)


@login_required
def donate(request):
    '''捐赠界面和支付宝当面付功能'''
    donatelist = Donate.objects.all()[:8]
    context = {'donatelist': donatelist, }
    if settings.USE_ALIPAY == True:
        context['alipay'] = True
        # 尝试获取流水号
        if request.method == 'POST':
            number = request.POST.get('q')
            out_trade_no = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y%m%d%H%M%S%s')
            try:
                # 获取金额数量
                amount = number
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
                # 将订单号传入模板
                context['out_trade_no'] = out_trade_no
            except:
                res = alipay.api_alipay_trade_cancel(out_trade_no=out_trade_no)
                registerinfo = {
                    'title': '糟糕，当面付插件可能出现问题了',
                    'subtitle': '如果一直失败,请后台联系站长',
                    'status': 'error', }
                context['registerinfo'] = registerinfo
    else:
        # 关闭支付宝支付
        context['alipay'] = False
    return render(request, 'sspanel/donate.html', context=context)


@login_required
def gen_face_pay_qrcode(request):
    '''生成当面付的二维码'''
    # 从seesion中获取订单的二维码
    url = request.session.get('code_url', '')
    # 生成支付宝申请记录
    record = AlipayRequest.objects.create(username=request.user,
                                          info_code=request.session['out_trade_no'],
                                          amount=request.session['amount'],)
    # 删除sessions信息
    del request.session['code_url']
    del request.session['out_trade_no']
    del request.session['amount']
    # 生成ss二维码
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf)
    image_stream = buf.getvalue()
    # 构造图片reponse
    response = HttpResponse(image_stream, content_type="image/png")

    return response


@login_required
def Face_pay_view(request, out_trade_no):
    '''当面付处理逻辑'''
    context = {}
    user = request.user
    paid = False
    # 等待3秒后再查询支付结果
    time.sleep(3)
    res = alipay.api_alipay_trade_query(out_trade_no=out_trade_no)
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
                                             info_code=out_trade_no, amount=amount, money_code=code)
        # 返回充值码到网页
        messages.info(request, '充值成功{}元，请去商品界面购买'.format(amount))
        return HttpResponseRedirect('/donate')
    # 如果30秒内没有支付，则关闭订单：
    if paid is False:
        alipay.api_alipay_trade_cancel(out_trade_no=out_trade_no)
        messages.warning(request, "充值失败了!自动跳转回充值界面")
        return HttpResponseRedirect('/donate')


@login_required
def nodeinfo(request):
    '''跳转到节点信息的页面'''

    nodelists = []
    ss_user = request.user.ss_user
    user = request.user
    # 将节点信息查询结果保存dict中，方便增加在线人数字段
    # 加入等级的判断
    nodes = Node.objects.filter(level__lte=user.level, show='显示').values()
    # 循环遍历每一条线路的在线人数
    for node in nodes:
        # 生成SSR和SS的链接
        ssr_password = base64.b64encode(
            bytes(ss_user.password, 'utf8')).decode('ascii')
        ssr_code = '{}:{}:{}:{}:{}:{}'.format(
            node['server'], ss_user.port, ss_user.protocol, ss_user.method, ss_user.obfs, ssr_password)
        ssr_pass = base64.b64encode(bytes(ssr_code, 'utf8')).decode('ascii')
        ssr_link = 'ssr://{}'.format(ssr_pass)
        ss_code = '{}:{}@{}:{}'.format(
            node['method'], ss_user.password, node['server'], ss_user.port)
        ss_pass = base64.b64encode(bytes(ss_code, 'utf8')).decode('ascii')
        ss_link = 'ss://{}'.format(ss_pass)
        node['ssrlink'] = ssr_link
        node['sslink'] = ss_link
        try:
            otime = NodeInfoLog.objects.filter(
                node_id=node['node_id'])[0].log_time
            # 判断节点最后一次心跳时间
            # 判断节点是否在线
            node['online'] = False if (time.time() - otime) > 75 else True
            # 检索节点的在线人数
            node['count'] = NodeOnlineLog.objects.filter(
                node_id=node['node_id'])[::-1][0].online_user
        except IndexError:
            node['count'] = 0
        nodelists.append(node)
    context = {
        'nodelists': nodelists,
        'ss_user': ss_user,
        'user': user,
    }

    return render(request, 'sspanel/nodeinfo.html', context=context)


@login_required
def trafficlog(request):
    '''跳转到流量记录的页面'''
    ss_user = request.user.ss_user
    nodes = Node.objects.all()
    node_id = request.GET.get('nodes', nodes[0].pk)
    # 检索符合要求得记录
    traffic = TrafficLog.objects.filter(user_id=ss_user.pk, node_id=node_id)
    node_name = Node.objects.get(pk=node_id)
    # 记录的前10条
    logs = traffic[:10]
    log_dic = []
    for log in logs:
        # 循环加入流量记录得时间
        rec = {
            't': timezone.datetime.fromtimestamp(log.log_time),
            'traffic': log.traffic,
            'node_id': log.node_id
        }
        log_dic.append(rec)
    # 记录该节点所消耗的所有流量
    total = 0
    for ll in traffic:
        total += ll.upload_traffic + ll.download_traffic
    total = total / settings.GB
    context = {'ss_user': ss_user,
               'log_dic': log_dic,
               'nodes': nodes,
               'total': '{:.2f} GB'.format(total),
               'node_name': node_name,

               }
    return render(request, 'sspanel/trafficlog.html', context=context)


@login_required
def shop(request):
    '''跳转到商品界面'''
    ss_user = request.user

    goods = Shop.objects.all()

    context = {'ss_user': ss_user,
               'goods': goods, }

    return render(request, 'sspanel/shop.html', context=context)


@login_required
def purchase(request, goods_id):
    '''商品购买逻辑'''

    goods = Shop.objects.all()
    good = goods.get(pk=goods_id)
    user = request.user
    ss_user = request.user.ss_user

    if user.balance < good.money:
        registerinfo = {
            'title': '金额不足！',
            'subtitle': '请联系站长充值',
            'status': 'error', }
        context = {'ss_user': ss_user,
                   'goods': goods,
                   'registerinfo': registerinfo,
                   }
        return render(request, 'sspanel/shop.html', context=context)

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
        registerinfo = {
            'title': '够买成功',
            'subtitle': '即将跳转回用户中心',
            'status': 'success', }

        context = {
            'ss_user': ss_user,
            'registerinfo': registerinfo,
        }
        return render(request, 'sspanel/userinfo.html', context=context)


@login_required
def purchaselog(request):
    '''用户购买记录页面'''

    records = PurchaseHistory.objects.filter(user=request.user)[:10]
    context = {
        'records': records,
    }
    return render(request, 'sspanel/purchaselog.html', context=context)


@login_required
def chargecenter(request):
    '''充值界面的跳转'''
    user = request.user
    codelist = MoneyCode.objects.filter(user=user)

    context = {'ss_user': user,
               'codelist': codelist}

    return render(request, 'sspanel/chargecenter.html', context=context)


@login_required
def charge(request):
    user = request.user
    if request.method == 'POST':
        input_code = request.POST.get('chargecode')
        # 在数据库里检索充值
        code_query = MoneyCode.objects.filter(code=input_code)
        # 判断充值码是否存在
        if len(code_query) == 0:
            registerinfo = {
                'title': '充值码失效',
                'subtitle': '请重新获取充值码',
                'status': 'error',
            }
            context = {
                'registerinfo': registerinfo,
                'ss_user': user,
            }
            return render(request, 'sspanel/chargecenter.html', context=context)

        else:
            code = code_query[0]
            # 判断充值码是否被使用
            if code.isused == True:
                # 当被使用的是时候
                registerinfo = {
                    'title': '充值码失效',
                    'subtitle': '请重新获取充值码',
                    'status': 'error', }
                context = {
                    'registerinfo': registerinfo,
                    'ss_user': user, }
                return render(request, 'sspanel/chargecenter.html', context=context)
            else:
                # 充值操作
                user.balance += code.number
                code.user = user.username
                code.isused = True
                user.save()
                code.save()
                # 将充值记录和捐赠绑定
                donate = Donate.objects.create(user=user, money=code.number)
                # 检索充值记录
                codelist = MoneyCode.objects.filter(user=user)
                registerinfo = {
                    'title': '充值成功！',
                    'subtitle': '请去商店购买商品！',
                    'status': 'success',
                }
                context = {
                    'registerinfo': registerinfo,
                    'ss_user': user,
                    'codelist': codelist,
                }
                return render(request, 'sspanel/chargecenter.html', context=context)


@login_required
def announcement(request):
    '''网站公告列表'''
    anno = Announcement.objects.all()

    return render(request, 'sspanel/announcement.html', {'anno': anno})


@login_required
def ticket(request):
    '''工单系统'''
    ticket = Ticket.objects.filter(user=request.user)
    context = {'ticket': ticket}

    return render(request, 'sspanel/ticket.html', context=context)


@login_required
def ticket_create(request):
    '''工单提交'''
    if request.method == "POST":
        title = request.POST.get('title', '')
        body = request.POST.get('body', '')
        Ticket.objects.create(user=request.user, title=title, body=body)
        ticket = Ticket.objects.filter(user=request.user)
        registerinfo = {
            'title': '添加成功',
            'subtitle': '数据更新成功！',
            'status': 'success', }

        context = {
            'ticket': ticket,
            'registerinfo': registerinfo,
        }
        return redirect('/ticket')
    else:
        return render(request, 'sspanel/ticketcreate.html')


@login_required
def ticket_delete(request, pk):
    '''删除指定'''
    ticket = Ticket.objects.get(pk=pk)
    ticket.delete()
    registerinfo = {
        'title': '删除成功',
        'subtitle': '该工单已经删除',
        'status': 'success', }

    context = {
        'registerinfo': registerinfo,
        'ticket': Ticket.objects.filter(user=request.user)
    }
    return render(request, 'sspanel/ticket.html', context=context)


@login_required
def ticket_edit(request, pk):
    '''工单编辑'''
    ticket = Ticket.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        title = request.POST.get('title', '')
        body = request.POST.get('body', '')
        ticket.title = title
        ticket.body = body
        ticket.save()
        registerinfo = {
            'title': '修改成功',
            'subtitle': '数据更新成功',
            'status': 'success', }

        context = {
            'registerinfo': registerinfo,
            'ticket': Ticket.objects.filter(user=request.user)
        }
        return render(request, 'sspanel/ticket.html', context=context)
    # 当请求不是post时，渲染
    else:
        context = {
            'ticket': ticket,
        }
        return render(request, 'sspanel/ticketedit.html', context=context)


# 网站后台界面
@permission_required('shadowsocks')
def backend_index(request):
    '''跳转到后台界面'''

    User = SSUser.objects.all()
    # 找到用户的总量
    user_num = len(User)
    # 循环遍历用户的签到人数
    checkin_num = 0
    # 遍历没有使用过得人数
    nouse_num = 0
    # 遍历从未签到过得人数
    nocheck_num = 0
    for user in User:
        if user.get_check_in() == True:
            checkin_num += 1
        if user.last_use_time == 0:
            nouse_num += 1
        if user.last_check_in_time.year == 1970:
            nocheck_num += 1
    # 节点信息状态
    nodes = Node.objects.values()
    # 用户在线情况
    online = 0
    for node in nodes:
        try:
            # 遍历在线人数
            online += NodeOnlineLog.objects.filter(node_id=node['id'])[
                ::-1][0].online_user
        except:
            online = 0
        traffic = TrafficLog.objects.filter(node_id=node['id'])
        # 获取指定节点所有流量
        total_tratffic = 0
        try:
            for ll in traffic:
                total_tratffic += ll.upload_traffic + ll.download_traffic
            total_tratffic = round(total_tratffic / settings.GB, 2)
        except:
            total_tratffic = 0
        node['total_traffic'] = total_tratffic
    # 收入情况
    income = Donate.objects.all()
    total_income = 0
    for i in income:
        total_income += i.money

    context = {
        'user_num': user_num,
        'checkin_num': checkin_num,
        'nocheck_num': nocheck_num,
        'nouse_num': nouse_num,
        'nodes': nodes,
        'alive_user': online,
        'income_num': len(income),
        'total_income': total_income,
    }

    return render(request, 'backend/index.html', context=context)


@permission_required('shadowsocks')
def backend_node_info(request):
    '''节点编辑界面'''

    nodes = Node.objects.all()
    context = {
        'nodes': nodes,
    }
    return render(request, 'backend/nodeinfo.html', context=context)


@permission_required('shadowsocks')
def node_delete(request, node_id):
    '''删除节点'''
    node = Node.objects.filter(node_id=node_id)
    node.delete()
    nodes = Node.objects.all()

    registerinfo = {
        'title': '删除节点',
        'subtitle': '成功啦',
                    'status': 'success', }

    context = {
        'nodes': nodes,
        'registerinfo': registerinfo
    }
    return render(request, 'backend/nodeinfo.html', context=context)


@permission_required('shadowsocks')
def node_edit(request, node_id):
    '''编辑节点'''
    node = Node.objects.get(node_id=node_id)
    nodes = Node.objects.all()
    # 当为post请求时，修改数据
    if request.method == "POST":
        form = NodeForm(request.POST, instance=node)
        if form.is_valid():
            form.save()
            registerinfo = {
                'title': '修改成功',
                'subtitle': '数据更新成功',
                'status': 'success', }

            context = {
                'nodes': nodes,
                'registerinfo': registerinfo,
            }
            return render(request, 'backend/nodeinfo.html', context=context)
        else:
            registerinfo = {
                'title': '错误',
                'subtitle': '数据填写错误',
                'status': 'error', }

            context = {
                'form': form,
                'registerinfo': registerinfo,
                'node': node,
            }
            return render(request, 'backend/nodeedit.html', context=context)
    # 当请求不是post时，渲染form
    else:
        form = NodeForm(instance=node)
        context = {
            'form': form,
            'node': node,
        }
        return render(request, 'backend/nodeedit.html', context=context)


@permission_required('shadowsocks')
def node_create(request):
    '''创建节点'''
    if request.method == "POST":
        form = NodeForm(request.POST)
        if form.is_valid():
            form.save()

            nodes = Node.objects.all()
            registerinfo = {
                'title': '添加成功',
                'subtitle': '数据更新成功！',
                'status': 'success', }

            context = {
                'nodes': nodes,
                'registerinfo': registerinfo,
            }
            return render(request, 'backend/nodeinfo.html', context=context)
        else:
            registerinfo = {
                'title': '错误',
                'subtitle': '数据填写错误',
                'status': 'error', }

            context = {
                'form': form,
                'registerinfo': registerinfo,
            }
            return render(request, 'backend/nodecreate.html', context=context)

    else:
        form = NodeForm()
        return render(request, 'backend/nodecreate.html', context={'form': form, })


class Page_List_View(object):
    '''拥有翻页功能的通用类'''

    def __init__(self, request, obj, page_num):
        self.request = request
        self.obj = obj
        self.page_num = page_num

    def get_page_context(self):
        '''返回分页context'''

        objects = self.obj.objects.all()
        # 每页显示10条记录
        paginator = Paginator(objects, self.page_num)
        # 构造分页.获取当前页码数量
        page = self.request.GET.get('page')

        # 页码为1时，防止异常
        try:
            contacts = paginator.page(page)
            page = int(page)
        except PageNotAnInteger:
            contacts = paginator.page(1)
            page = 1
        except EmptyPage:
            contacts = paginator.page(paginator.num_pages)

        # 获得整个分页页码列表
        page_list = paginator.page_range

        # 获得分页后的总页数
        total = paginator.num_pages

        left = []
        left_has_more = False
        right = []
        right_has_more = False
        first = False
        last = False
        # 开始构造页码列表
        if page == 1:
            # 当前页为第1页时
            right = page_list[page:page + 2]
            if len(right) > 0:
                # 当最后一页比总页数小时，我们应该显示省略号
                if right[-1] < total - 1:
                    right_has_more = True
                # 当最后一页比rigth大时候，我们需要显示最后一页
                if right[-1] < total:
                    last = True
        elif page == total:
            # 当前页为最后一页时
            left = page_list[(page - 3) if (page - 3) > 0 else 0:page - 1]
            if left[0] > 2:
                left_has_more = True
            if left[0] > 1:
                first = True
        else:
            left = page_list[(page - 2) if (page - 2) > 0 else 0:page - 1]
            right = page_list[page:page + 2]

            # 是否需要显示最后一页和最后一页前的省略号
            if right[-1] < total - 1:
                right_has_more = True
            if right[-1] < total:
                last = True

            # 是否需要显示第 1 页和第 1 页后的省略号
            if left[0] > 2:
                left_has_more = True
            if left[0] > 1:
                first = True

        context = {
            'contacts': contacts,
            'page_list': page_list,
            'left': left,
            'right': right,
            'left_has_more': left_has_more,
            'right_has_more': right_has_more,
            'first': first,
            'last': last,
            'total': total,
            'page': page,
        }

        return context


@permission_required('shadowsocks')
def backend_Aliveuser(request):
    '''返回在线用户的ip的View'''

    obj = Aliveip
    page_num = 10
    context = Page_List_View(request, obj, page_num).get_page_context()

    return render(request, 'backend/aliveuser.html', context=context)


@permission_required('shadowsocks')
def backend_UserList(request):
    '''返回所有用户的View'''

    obj = User
    page_num = 15
    context = Page_List_View(request, obj, page_num).get_page_context()

    return render(request, 'backend/userlist.html', context=context)


@permission_required('shadowsocks')
def user_delete(request, pk):
    '''删除user'''
    user = User.objects.filter(pk=pk)
    user.delete()

    obj = User
    page_num = 15
    context = Page_List_View(request, obj, page_num).get_page_context()

    registerinfo = {
        'title': '删除用户',
        'subtitle': '成功啦',
                    'status': 'success', }

    context['registerinfo'] = registerinfo
    return render(request, 'backend/userlist.html', context=context)


@permission_required('shadowsocks')
def user_search(request):
    '''用户搜索结果'''
    q = request.GET.get('q')
    contacts = User.objects.filter(
        Q(username__icontains=q) | Q(email__icontains=q) | Q(pk__icontains=q))
    context = {
        'contacts': contacts,
    }

    return render(request, 'backend/userlist.html', context=context)


@permission_required('shadowsocks')
def backend_invite(request):
    '''邀请码生成'''
    code_list = InviteCode.objects.filter(type=0)
    return render(request, 'backend/invitecode.html', {'code_list': code_list, })


@permission_required('shadowsocks')
def gen_invite_code(request):

    Num = request.GET.get('num')
    type = request.GET.get('type')
    for i in range(int(Num)):
        code = InviteCode(type=type)
        code.save()

    code_list = InviteCode.objects.filter(type=0)
    registerinfo = {
        'title': '成功',
        'subtitle': '添加邀请码{}个'.format(Num),
                    'status': 'success', }

    context = {
        'registerinfo': registerinfo,
        'code_list': code_list,
    }

    return render(request, 'backend/invitecode.html', context=context)


@permission_required('shadowsocks')
def backend_charge(request):
    '''后台充值码界面'''

    # 获取所有充值码记录
    obj = MoneyCode
    page_num = 10
    # 获取充值的金额和数量
    Num = request.GET.get('num')
    money = request.GET.get('money')
    if Num and money:
        for i in range(int(Num)):
            code = MoneyCode(number=money)
            code.save()
        context = Page_List_View(request, obj, page_num).get_page_context()
        registerinfo = {
            'title': '成功',
            'subtitle': '添加{}元充值码{}个'.format(money, Num),
            'status': 'success'}
        context['registerinfo'] = registerinfo

    else:
        context = Page_List_View(request, obj, page_num).get_page_context()

    return render(request, 'backend/charge.html', context=context)


@permission_required('shadowsocks')
def backend_shop(request):
    '''商品管理界面'''

    goods = Shop.objects.all()
    context = {
        'goods': goods,
    }
    return render(request, 'backend/shop.html', context=context)


@permission_required('shadowsocks')
def good_delete(request, pk):
    '''删除商品'''
    good = Shop.objects.filter(pk=pk)
    good.delete()
    goods = Shop.objects.all()

    registerinfo = {
        'title': '删除商品',
        'subtitle': '成功啦',
                    'status': 'success', }

    context = {
        'goods': goods,
        'registerinfo': registerinfo
    }
    return render(request, 'backend/shop.html', context=context)


@permission_required('shadowsocks')
def good_edit(request, pk):
    '''商品编辑'''

    good = Shop.objects.get(pk=pk)
    goods = Shop.objects.all()
    # 当为post请求时，修改数据
    if request.method == "POST":
        form = ShopForm(request.POST, instance=good)
        if form.is_valid():
            form.save()
            registerinfo = {
                'title': '修改成功',
                'subtitle': '数据更新成功',
                'status': 'success', }

            context = {
                'goods': goods,
                'registerinfo': registerinfo,
            }
            return render(request, 'backend/shop.html', context=context)
        else:
            registerinfo = {
                'title': '错误',
                'subtitle': '数据填写错误',
                'status': 'error', }

            context = {
                'form': form,
                'registerinfo': registerinfo,
                'good': good,
            }
            return render(request, 'backend/goodedit.html', context=context)
    # 当请求不是post时，渲染form
    else:
        form = ShopForm(instance=good)
        context = {
            'form': form,
            'good': good,
        }
        return render(request, 'backend/goodedit.html', context=context)


@permission_required('shadowsocks')
def good_create(request):
    '''商品创建'''
    if request.method == "POST":
        form = ShopForm(request.POST)
        if form.is_valid():
            form.save()

            goods = Shop.objects.all()
            registerinfo = {
                'title': '添加成功',
                'subtitle': '数据更新成功！',
                'status': 'success', }

            context = {
                'goods': goods,
                'registerinfo': registerinfo,
            }
            return render(request, 'backend/shop.html', context=context)
        else:
            registerinfo = {
                'title': '错误',
                'subtitle': '数据填写错误',
                'status': 'error', }

            context = {
                'form': form,
                'registerinfo': registerinfo,
            }
            return render(request, 'backend/goodcreate.html', context=context)

    else:
        form = ShopForm()
        return render(request, 'backend/goodcreate.html', context={'form': form, })


@permission_required('shadowsocks')
def purchase_history(request):
    '''购买历史'''
    obj = PurchaseHistory
    page_num = 10
    context = Page_List_View(request, obj, page_num).get_page_context()
    return render(request, 'backend/purchasehistory.html', context=context)


@permission_required('shadowsocks')
def backend_anno(request):
    '''公告管理界面'''

    anno = Announcement.objects.all()
    context = {
        'anno': anno,
    }
    return render(request, 'backend/annolist.html', context=context)


@permission_required('shadowsocks')
def anno_delete(request, pk):
    '''删除公告'''
    anno = Announcement.objects.filter(pk=pk)
    anno.delete()
    anno = Announcement.objects.all()

    registerinfo = {
        'title': '删除公告',
        'subtitle': '成功啦',
                    'status': 'success', }

    context = {
        'anno': anno,
        'registerinfo': registerinfo
    }
    return render(request, 'backend/annolist.html', context=context)


@permission_required('shadowsocks')
def anno_create(request):
    '''公告创建'''
    if request.method == "POST":
        form = AnnoForm(request.POST)
        if form.is_valid():
            form.save()
            anno = Announcement.objects.all()
            registerinfo = {
                'title': '添加成功',
                'subtitle': '数据更新成功！',
                'status': 'success', }

            context = {
                'anno': anno,
                'registerinfo': registerinfo,
            }
            return render(request, 'backend/annolist.html', context=context)
        else:
            registerinfo = {
                'title': '错误',
                'subtitle': '数据填写错误',
                'status': 'error', }

            context = {
                'form': form,
                'registerinfo': registerinfo,
            }
            return render(request, 'backend/annocreate.html', context=context)

    else:
        form = AnnoForm()
        return render(request, 'backend/annocreate.html', context={'form': form, })


@permission_required('shadowsocks')
def anno_edit(request, pk):
    '''公告编辑'''

    anno = Announcement.objects.get(pk=pk)

    # 当为post请求时，修改数据
    if request.method == "POST":
        form = AnnoForm(request.POST, instance=anno)
        if form.is_valid():
            form.save()
            registerinfo = {
                'title': '修改成功',
                'subtitle': '数据更新成功',
                'status': 'success', }

            context = {
                'registerinfo': registerinfo,
                'anno': Announcement.objects.all(),
            }
            return render(request, 'backend/annolist.html', context=context)
        else:
            registerinfo = {
                'title': '错误',
                'subtitle': '数据填写错误',
                'status': 'error', }

            context = {
                'form': form,
                'registerinfo': registerinfo,
                'anno': anno,
            }
            return render(request, 'backend/annoedit.html', context=context)
    # 当请求不是post时，渲染form
    else:
        anno.body = tomd.convert(anno.body)

        context = {
            'anno': anno,
        }
        return render(request, 'backend/annoedit.html', context=context)


@permission_required('shadowsocks')
def backend_ticket(request):
    '''工单系统'''
    ticket = Ticket.objects.all()
    context = {'ticket': ticket}
    return render(request, 'backend/ticket.html', context=context)


@permission_required('shadowsocks')
def backend_ticketedit(request, pk):
    '''后台工单编辑'''
    ticket = Ticket.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        title = request.POST.get('title', '')
        body = request.POST.get('body', '')
        status = request.POST.get('status', '开启')
        ticket.title = title
        ticket.body = body
        ticket.status = status
        ticket.save()
        registerinfo = {
            'title': '修改成功',
            'subtitle': '数据更新成功',
            'status': 'success', }

        context = {
            'registerinfo': registerinfo,
            'ticket': Ticket.objects.filter(status='开启')
        }
        return render(request, 'backend/ticket.html', context=context)
    # 当请求不是post时，渲染
    else:
        context = {
            'ticket': ticket,
        }
        return render(request, 'backend/ticketedit.html', context=context)
