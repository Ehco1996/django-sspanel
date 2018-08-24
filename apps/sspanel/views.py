import tomd
import qrcode
from random import randint

from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.shortcuts import render
from django.contrib import messages
from django.utils.six import BytesIO
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required

from apps.custom_views import Page_List_View
from apps.utils import reverse_traffic, traffic_format
from .forms import RegisterForm, LoginForm, NodeForm, GoodsForm, AnnoForm
from apps.ssserver.models import SSUser, Node, NodeOnlineLog, AliveIp
from .models import (InviteCode, User, Donate, Goods, MoneyCode,
                     PurchaseHistory, PayRequest, Announcement, Ticket,
                     RebateRecord)
from apps.constants import (METHOD_CHOICES, PROTOCOL_CHOICES, OBFS_CHOICES,
                            THEME_CHOICES)


def index(request):
    '''跳转到首页'''

    return render(request, 'sspanel/index.html',
                  {'allow_register': settings.ALLOW_REGISET})


def sshelp(request):
    '''跳转到帮助界面'''
    return render(request, 'sspanel/help.html')


@login_required
def ssclient(request):
    '''跳转到客户端界面'''
    return render(request, 'sspanel/client.html')


def ssinvite(request):
    '''跳转到邀请码界面'''
    codelist = InviteCode.objects.filter(
        code_type=1, isused=False, code_id=1)[:20]

    context = {
        'codelist': codelist,
    }

    return render(request, 'sspanel/invite.html', context=context)


def pass_invitecode(request, invitecode):
    '''提供点击邀请码连接之后自动填写邀请码'''
    form = RegisterForm(initial={'invitecode': invitecode})
    return render(request, 'sspanel/register.html', {'form': form})


def register(request):
    '''用户注册时的函数'''
    if settings.ALLOW_REGISET is False:
        return HttpResponse('已经关闭注册了喵')
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                # 获取用户填写的邀请码
                code = request.POST.get('invitecode')
                # 数据库查询邀请码
                code = InviteCode.objects.filter(
                    code=code, isused=False).first()
                # 判断邀请码是否存在并返回信息
                if not code:
                    messages.error(request, "请重新获取邀请码",
                                   extra_tags="邀请码失效")
                    return render(
                        request, 'sspanel/register.html', {'form': form})
                else:
                    messages.success(request, "请登录使用吧！",
                                     extra_tags="注册成功！")
                    form.save()
                    # 改变表邀请码状态
                    code.isused = True
                    code.save()
                    # 将user和ssuser关联
                    user = User.objects.get(
                        username=request.POST.get('username'))
                    # 绑定邀请人
                    user.invited_by = code.code_id
                    user.save()
                    max_port_user = SSUser.objects.order_by('-port').first()
                    port = max_port_user.port + randint(2, 3)
                    SSUser.objects.create(user=user, port=port)
                    return HttpResponseRedirect(reverse('sspanel:index'))
    else:
        form = RegisterForm()

    return render(request, 'sspanel/register.html', {'form': form})


def user_login(request):
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
                messages.success(request, "自动跳转到用户中心", extra_tags="登录成功！")
                return HttpResponseRedirect(reverse('sspanel:userinfo'))
            else:
                form = LoginForm()
                messages.error(request, "请重新填写信息！", extra_tags="登录失败！")
                context = {
                    'form': form,
                }
                return render(request, 'sspanel/login.html', context=context)
    else:
        context = {
            'form': LoginForm(),
        }

        return render(request, 'sspanel/login.html', context=context)


def user_logout(request):
    '''用户登出函数'''
    logout(request)
    messages.success(request, "欢迎下次再来", extra_tags="注销成功")
    return HttpResponseRedirect(reverse("sspanel:index"))


@login_required
def userinfo(request):
    '''用户中心'''
    user = request.user
    # 获取公告
    anno = Announcement.objects.all().first()
    min_traffic = traffic_format(settings.MIN_CHECKIN_TRAFFIC)
    max_traffic = traffic_format(settings.MAX_CHECKIN_TRAFFIC)
    remain_traffic = 100 - eval(user.ss_user.get_used_percentage())
    # 订阅地址
    sub_link = user.get_sub_link()
    # 节点导入链接
    sub_code = Node.get_sub_code(user)
    context = {
        'user': user,
        'anno': anno,
        'remain_traffic': remain_traffic,
        'min_traffic': min_traffic,
        'max_traffic': max_traffic,
        'sub_link': sub_link,
        'sub_code': sub_code,
        'themes': THEME_CHOICES
    }
    return render(request, 'sspanel/userinfo.html', context=context)


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
    ssr_link = node.get_ssr_link(ss_user)
    ssr_img = qrcode.make(ssr_link)
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
    ss_link = node.get_ss_link(ss_user)
    ss_img = qrcode.make(ss_link)
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
    context = {
        'donatelist': donatelist,
    }
    if settings.USE_ALIPAY is True:
        context['alipay'] = True
    else:
        # 关闭支付宝支付
        context['alipay'] = False
    return render(request, 'sspanel/donate.html', context=context)


@login_required
def gen_face_pay_qrcode(request):
    '''生成当面付的二维码'''

    req = PayRequest.get_user_recent_pay_req(request.user)
    if req:
        # 生成ss二维码
        img = qrcode.make(req.qrcode_url)
        buf = BytesIO()
        img.save(buf)
        image_stream = buf.getvalue()
        # 构造图片reponse
        response = HttpResponse(image_stream, content_type="image/png")
        return response
    else:
        return HttpResponse('wrong')


@login_required
def nodeinfo(request):
    '''跳转到节点信息的页面'''

    nodelists = []
    ss_user = request.user.ss_user
    user = request.user
    # 加入等级的判断
    nodes = Node.objects.filter(show=1).values()
    # 循环遍历每一条线路的在线人数
    for node in nodes:
        # 生成SSR和SS的链接
        obj = Node.objects.get(node_id=node['node_id'])
        node['ssrlink'] = obj.get_ssr_link(ss_user)
        node['sslink'] = obj.get_ss_link(ss_user)
        node['country'] = obj.country.lower()
        node['node_type'] = obj.get_node_type_display()[:-3]
        if obj.node_type == 1:
            # 单端口的情况下
            node['port'] = obj.port
            node['method'] = obj.method
            node['password'] = obj.password
            node['protocol'] = obj.protocol
            node['node_color'] = 'warning'
            node['protocol_param'] = '{}:{}'.format(ss_user.port,
                                                    ss_user.password)
            node['obfs'] = obj.obfs
            node['obfs_param'] = obj.obfs_param
        else:
            node['port'] = ss_user.port
            node['method'] = ss_user.method
            node['password'] = ss_user.password
            node['protocol'] = ss_user.protocol
            node['node_color'] = 'info'
            node['protocol_param'] = ss_user.protocol_param
            node['obfs'] = ss_user.obfs
            node['obfs_param'] = ss_user.obfs_param
            # 得到在线人数
        log = NodeOnlineLog.objects.filter(node_id=node['node_id']).last()
        if log:
            node['online'] = log.get_oneline_status()
            node['count'] = log.get_online_user()
        else:
            node['online'] = False
            node['count'] = 0
        nodelists.append(node)
    # 订阅地址
    sub_link = user.get_sub_link()
    context = {
        'nodelists': nodelists,
        'ss_user': ss_user,
        'user': user,
        'sub_link': sub_link,
    }
    return render(request, 'sspanel/nodeinfo.html', context=context)


@login_required
def trafficlog(request):
    '''跳转到流量记录的页面'''

    ss_user = request.user.ss_user
    nodes = Node.objects.filter(show=1)
    context = {
        'ss_user': ss_user,
        'nodes': nodes,
    }
    return render(request, 'sspanel/trafficlog.html', context=context)


@login_required
def shop(request):
    '''跳转到商品界面'''
    ss_user = request.user
    goods = Goods.objects.filter(status=1)
    context = {
        'ss_user': ss_user,
        'goods': goods,
    }
    return render(request, 'sspanel/shop.html', context=context)


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

    context = {'user': user, 'codelist': codelist}

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
            messages.error(request, "请重新获取充值码", extra_tags="充值码失效")
            return HttpResponseRedirect(reverse('sspanel:chargecenter'))
        else:
            code = code_query[0]
            # 判断充值码是否被使用
            if code.isused is True:
                # 当被使用的是时候
                messages.error(request, "请重新获取充值码", extra_tags="充值码失效")
                return HttpResponseRedirect(reverse('sspanel:chargecenter'))
            else:
                # 充值操作
                user.balance += code.number
                code.user = user.username
                code.isused = True
                user.save()
                code.save()
                # 将充值记录和捐赠绑定
                Donate.objects.create(user=user, money=code.number)
                # 检索充值记录
                codelist = MoneyCode.objects.filter(user=user)
                messages.success(request, "请去商店购买商品！", extra_tags="充值成功！")
                return HttpResponseRedirect(reverse('sspanel:chargecenter'))


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
        messages.success(request, "数据更新成功！", extra_tags="添加成功")
        return HttpResponseRedirect(reverse('sspanel:ticket'))
    else:
        return render(request, 'sspanel/ticketcreate.html')


@login_required
def ticket_delete(request, pk):
    '''删除指定'''
    ticket = Ticket.objects.get(pk=pk)
    ticket.delete()
    messages.success(request, "该工单已经删除", extra_tags="删除成功")
    return HttpResponseRedirect(reverse('sspanel:ticket'))


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
        messages.success(request, "数据更新成功", extra_tags="修改成功")
        return HttpResponseRedirect(reverse('sspanel:ticket'))
    else:
        context = {
            'ticket': ticket,
        }
        return render(request, 'sspanel/ticketedit.html', context=context)


@login_required
def affiliate(request):
    '''推广页面'''
    if request.user.is_superuser is not True:
        invidecodes = InviteCode.objects.filter(
            code_id=request.user.pk, code_type=0)
        inviteNum = request.user.invitecode_num - len(invidecodes)
    else:
        # 如果是管理员，特殊处理
        invidecodes = InviteCode.objects.filter(
            code_id=request.user.pk, code_type=0, isused=False)
        inviteNum = 5
    context = {
        'invitecodes': invidecodes,
        'invitePercent': settings.INVITE_PERCENT * 100,
        'inviteNumn': inviteNum
    }
    return render(request, 'sspanel/affiliate.html', context=context)


@login_required
def rebate_record(request):
    '''返利记录'''
    u = request.user
    records = RebateRecord.objects.filter(user_id=u.pk)[:10]
    context = {
        'records': records,
        'user': request.user,
    }
    return render(request, 'sspanel/rebaterecord.html', context=context)


# 网站后台界面
@permission_required('sspanel')
def backend_index(request):
    '''跳转到后台界面'''
    context = {
        'userNum': User.userNum(),
    }

    return render(request, 'backend/index.html', context=context)


@permission_required('sspanel')
def backend_node_info(request):
    '''节点编辑界面'''
    nodes = Node.objects.all()
    context = {
        'nodes': nodes,
    }
    return render(request, 'backend/nodeinfo.html', context=context)


@permission_required('sspanel')
def node_delete(request, node_id):
    '''删除节点'''
    node = Node.objects.filter(node_id=node_id)
    node.delete()
    messages.success(request, "成功啦", extra_tags="删除节点")
    return HttpResponseRedirect(reverse('sspanel:backend_node_info'))


@permission_required('sspanel')
def node_edit(request, node_id):
    '''编辑节点'''
    node = Node.objects.get(node_id=node_id)
    # 当为post请求时，修改数据
    if request.method == "POST":
        form = NodeForm(request.POST, instance=node)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="修改成功")
            return HttpResponseRedirect(reverse('sspanel:backend_node_info'))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {
                'form': form,
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


@permission_required('sspanel')
def node_create(request):
    '''创建节点'''
    if request.method == "POST":
        form = NodeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功！", extra_tags="添加成功")
            return HttpResponseRedirect(reverse('sspanel:backend_node_info'))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {
                'form': form,
            }
            return render(request, 'backend/nodecreate.html', context=context)

    else:
        form = NodeForm()
        return render(
            request, 'backend/nodecreate.html', context={
                'form': form,
            })


@permission_required('sspanel')
def backend_userlist(request):
    '''返回所有用户的View'''
    obj = User.objects.all().order_by('-date_joined')
    page_num = 15
    context = Page_List_View(request, obj, page_num).get_page_context()
    return render(request, 'backend/userlist.html', context)


@permission_required('sspanel')
def user_delete(request, pk):
    '''删除user'''
    user = User.objects.filter(pk=pk)
    user.delete()
    messages.success(request, "成功啦", extra_tags="删除用户")
    return HttpResponseRedirect(reverse('sspanel:user_list'))


@permission_required('sspanel')
def user_search(request):
    '''用户搜索结果'''
    q = request.GET.get('q')
    contacts = User.objects.filter(
        Q(username__icontains=q) | Q(email__icontains=q) | Q(pk__icontains=q))
    context = {
        'contacts': contacts,
    }
    return render(request, 'backend/userlist.html', context=context)


@permission_required('sspanel')
def user_status(request):
    '''站内用户分析'''
    # 查询今日注册的用户
    todayRegistered = User.todayRegister().values()
    for t in todayRegistered:
        try:
            t['inviter'] = User.objects.get(pk=t['invited_by'])
        except:
            t['inviter'] = 'ehco'
    todayRegisteredNum = len(todayRegistered)
    # 查询消费水平前十的用户
    richUser = Donate.richPeople()
    # 查询流量用的最多的用户
    coreUser = SSUser.coreUser()
    context = {
        'userNum': User.userNum(),
        'todayChecked': SSUser.userTodyChecked(),
        'aliveUser': NodeOnlineLog.totalOnlineUser(),
        'todayRegistered': todayRegistered[:10],
        'todayRegisteredNum': todayRegisteredNum,
        'richUser': richUser,
        'coreUser': coreUser,
    }
    return render(request, 'backend/userstatus.html', context=context)


@permission_required('sspanel')
def backend_invite(request):
    '''邀请码生成'''
    code_list = InviteCode.objects.filter(code_type=0, isused=False, code_id=1)
    return render(request, 'backend/invitecode.html', {
        'code_list': code_list,
    })


@permission_required('sspanel')
def gen_invite_code(request):

    Num = request.GET.get('num')
    code_type = request.GET.get('type')
    for i in range(int(Num)):
        code = InviteCode(code_type=code_type)
        code.save()
    messages.success(request, '添加邀请码{}个'.format(Num), extra_tags="成功")
    return HttpResponseRedirect(reverse('sspanel:backend_invite'))


@permission_required('sspanel')
def backend_charge(request):
    '''后台充值码界面'''
    # 获取所有充值码记录
    obj = MoneyCode.objects.all()
    page_num = 10
    context = Page_List_View(request, obj, page_num).get_page_context()
    # 获取充值的金额和数量
    Num = request.GET.get('num')
    money = request.GET.get('money')
    if Num and money:
        for i in range(int(Num)):
            code = MoneyCode(number=money)
            code.save()
        messages.success(request, '添加{}元充值码{}个'.format(
            money, Num), extra_tags="成功")
        return HttpResponseRedirect(reverse('sspanel:backend_charge'))
    return render(request, 'backend/charge.html', context=context)


@permission_required('sspanel')
def backend_shop(request):
    '''商品管理界面'''

    goods = Goods.objects.all()
    context = {
        'goods': goods,
    }
    return render(request, 'backend/shop.html', context=context)


@permission_required('sspanel')
def good_delete(request, pk):
    '''删除商品'''
    good = Goods.objects.filter(pk=pk)
    good.delete()
    messages.success(request, "成功啦", extra_tags="删除商品")
    return HttpResponseRedirect(reverse('sspanel:backend_shop'))


@permission_required('sspanel')
def good_edit(request, pk):
    '''商品编辑'''

    good = Goods.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        # 转换为GB
        data = request.POST.copy()
        data['transfer'] = eval(data['transfer']) * settings.GB
        form = GoodsForm(data, instance=good)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="修改成功")
            return HttpResponseRedirect(reverse('sspanel:backend_shop'))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {
                'form': form,
                'good': good,
            }
            return render(request, 'backend/goodedit.html', context=context)
    # 当请求不是post时，渲染form
    else:
        data = {'transfer': round(good.transfer / settings.GB)}
        form = GoodsForm(initial=data, instance=good)
        context = {
            'form': form,
            'good': good,
        }
        return render(request, 'backend/goodedit.html', context=context)


@permission_required('sspanel')
def good_create(request):
    '''商品创建'''
    if request.method == "POST":
        # 转换为GB
        data = request.POST.copy()
        data['transfer'] = eval(data['transfer']) * settings.GB
        form = GoodsForm(data)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功！", extra_tags="添加成功")
            return HttpResponseRedirect(reverse('sspanel:backend_shop'))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {
                'form': form,
            }
            return render(request, 'backend/goodcreate.html', context=context)
    else:
        form = GoodsForm()
        return render(
            request, 'backend/goodcreate.html', context={
                'form': form,
            })


@permission_required('sspanel')
def purchase_history(request):
    '''购买历史'''
    obj = PurchaseHistory.objects.all()
    page_num = 10
    context = Page_List_View(request, obj, page_num).get_page_context()
    return render(request, 'backend/purchasehistory.html', context=context)


@permission_required('sspanel')
def backend_anno(request):
    '''公告管理界面'''
    anno = Announcement.objects.all()
    context = {
        'anno': anno,
    }
    return render(request, 'backend/annolist.html', context=context)


@permission_required('sspanel')
def anno_delete(request, pk):
    '''删除公告'''
    anno = Announcement.objects.filter(pk=pk)
    anno.delete()
    messages.success(request, "成功啦", extra_tags="删除公告")
    return HttpResponseRedirect(reverse('sspanel:backend_anno'))


@permission_required('sspanel')
def anno_create(request):
    '''公告创建'''
    if request.method == "POST":
        form = AnnoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="添加成功")
            return HttpResponseRedirect(reverse('sspanel:backend_anno'))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {
                'form': form,
            }
            return render(request, 'backend/annocreate.html', context=context)
    else:
        form = AnnoForm()
        return render(
            request, 'backend/annocreate.html', context={
                'form': form,
            })


@permission_required('sspanel')
def anno_edit(request, pk):
    '''公告编辑'''
    anno = Announcement.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        form = AnnoForm(request.POST, instance=anno)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="修改成功")
            return HttpResponseRedirect(reverse('sspanel:backend_anno'))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {
                'form': form,
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


@permission_required('sspanel')
def backend_ticket(request):
    '''工单系统'''
    ticket = Ticket.objects.filter(status=1)
    context = {'ticket': ticket}
    return render(request, 'backend/ticket.html', context=context)


@permission_required('sspanel')
def backend_ticketedit(request, pk):
    '''后台工单编辑'''
    ticket = Ticket.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        title = request.POST.get('title', '')
        body = request.POST.get('body', '')
        status = request.POST.get('status', 1)
        ticket.title = title
        ticket.body = body
        ticket.status = status
        ticket.save()

        messages.success(request, "数据更新成功", extra_tags="修改成功")
        return HttpResponseRedirect(reverse('sspanel:backend_ticket'))
    # 当请求不是post时，渲染
    else:
        context = {
            'ticket': ticket,
        }
        return render(request, 'backend/ticketedit.html', context=context)


@permission_required('ssserver')
def backend_alive_user(request):
    user_list = []
    for node_id in Node.get_node_ids():
        user_list.extend(AliveIp.recent_alive(node_id))
    page_num = 15
    context = Page_List_View(request, user_list, page_num).get_page_context()

    return render(request, 'backend/aliveuser.html', context=context)
