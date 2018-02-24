import time
import tomd
import json
import qrcode
import base64
import datetime
from random import randint

from decimal import Decimal
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.utils.six import BytesIO
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, render_to_response, redirect, HttpResponseRedirect

from .payments import alipay
from shadowsocks.tools import reverse_traffic
from .forms import RegisterForm, LoginForm, NodeForm, ShopForm, AnnoForm
from ssserver.models import METHOD_CHOICES, PROTOCOL_CHOICES, OBFS_CHOICES
from ssserver.models import SSUser, TrafficLog, Node, NodeOnlineLog, NodeInfoLog, AliveIp
from .models import InviteCode, User, Donate, Shop, MoneyCode, PurchaseHistory, PayRequest,  Announcement, Ticket, RebateRecord


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
    codelist = InviteCode.objects.filter(type=1, isused=False, code_id=1)[:20]

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
            code_query = InviteCode.objects.filter(code=code, isused=False)
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
                # 改变表邀请码状态
                code = code_query[0]
                code.isused = True
                code.save()
                # 将user和ssuser关联
                user = User.objects.get(username=request.POST.get('username'))
                # 绑定邀请人
                user.invited_by = code.code_id
                user.save()
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
                min_traffic = '{}m'.format(
                    int(settings.MIN_CHECKIN_TRAFFIC / 1024 / 1024))
                max_traffic = '{}m'.format(
                    int(settings.MAX_CHECKIN_TRAFFIC / 1024 / 1024))
                remain_traffic = 100 - eval(user.ss_user.get_used_percentage())
                registerinfo = {
                    'title': '登录成功！',
                    'subtitle': '自动跳转到用户中心',
                    'status': 'success',
                }
                context = {
                    'registerinfo': registerinfo,
                    'anno': anno,
                    'remain_traffic': remain_traffic,
                    'min_traffic': min_traffic,
                    'max_traffic': max_traffic,
                    'sub_link': user.get_sub_link(),
                    'sub_code': Node.get_sub_code(user),

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
        context = {'form': LoginForm(),
                   'USE_SMTP': settings.USE_SMTP, }

        return render(request, 'sspanel/login.html', context=context)


def Logout_view(request):
    '''用户登出函数'''
    logout(request)
    registerinfo = {
        'title': '注销成功',
        'subtitle': '欢迎下次再来',
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
    }
    return render(request, 'sspanel/userinfo.html', context=context)


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
    context = {'donatelist': donatelist, }

    if settings.USE_91PAY == True:
        return render(request, 'sspanel/donate91.html', context=context)

    if settings.USE_ALIPAY == True:
        context['alipay'] = True
    else:
        # 关闭支付宝支付
        context['alipay'] = False
    return render(request, 'sspanel/donate.html', context=context)


@login_required
def gen_face_pay_qrcode(request):
    '''生成当面付的二维码'''
    try:
        # 从seesion中获取订单的二维码
        url = request.session.get('code_url', '')
        # 生成支付宝申请记录
        record = PayRequest.objects.create(username=request.user,
                                           info_code=request.session['out_trade_no'],
                                           amount=request.session['amount'],)
        # 删除sessions信息
        del request.session['code_url']
        del request.session['amount']
        # 生成ss二维码
        img = qrcode.make(url)
        buf = BytesIO()
        img.save(buf)
        image_stream = buf.getvalue()
        # 构造图片reponse
        response = HttpResponse(image_stream, content_type="image/png")
        return response
    except:
        return HttpResponse('wrong request')


@login_required
def nodeinfo(request):
    '''跳转到节点信息的页面'''

    nodelists = []
    ss_user = request.user.ss_user
    user = request.user
    # 加入等级的判断
    nodes = Node.objects.filter(show='显示').values()
    # 循环遍历每一条线路的在线人数
    for node in nodes:
        # 生成SSR和SS的链接
        obj = Node.objects.get(node_id=node['node_id'])
        node['ssrlink'] = obj.get_ssr_link(ss_user)
        node['sslink'] = obj.get_ss_link(ss_user)
        node['country'] = obj.country.lower()
        # 得到在线人数
        try:
            log = NodeOnlineLog.objects.filter(
                node_id=node['node_id']).order_by('-id')[0]
            node['online'] = log.get_oneline_status()
            node['count'] = log.get_online_user()
        except:
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
    nodes = Node.objects.filter(show='显示')
    context = {
        'ss_user': ss_user,
        'nodes': nodes,
    }
    return render(request, 'sspanel/trafficlog.html', context=context)


@login_required
def shop(request):
    '''跳转到商品界面'''
    ss_user = request.user
    goods = Shop.objects.filter(sale='上架')
    context = {'ss_user': ss_user,
               'goods': goods, }
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

    context = {'user': user,
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
                'codelist': MoneyCode.objects.filter(user=user),
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
                    'ss_user': user,
                    'codelist': codelist,
                }
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


@login_required
def affiliate(request):
    '''推广页面'''
    if request.user.pk != 1:
        invidecodes = InviteCode.objects.filter(
            code_id=request.user.pk, type=0)
        inviteNum = request.user.invitecode_num - len(invidecodes)
    else:
        # 如果是管理员，特殊处理
        # 写死，每次只能生成5额邀请码
        invidecodes = InviteCode.objects.filter(
            code_id=request.user.pk, type=0, isused=False)
        inviteNum = 5
    context = {
        'invitecodes': invidecodes,
        'invitePercent': settings.INVITE_PERCENT * 100,
        'inviteNumn': inviteNum}
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
@permission_required('shadowsocks')
def backend_index(request):
    '''跳转到后台界面'''
    context = {
        'userNum': User.userNum(),
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
            node.total_traffic = reverse_traffic(
                form.cleaned_data['human_total_traffic'])
            node.save()
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
    '''
    拥有翻页功能的通用类
    Args:
        request ： django request
        obj： 等待分分页的列表，例如 User.objects.all()
        page_num： 分页的页数
    '''

    def __init__(self, request, obj_list, page_num):
        self.request = request
        self.obj_list = obj_list
        self.page_num = page_num

    def get_page_context(self):
        '''返回分页context'''
        # 每页显示10条记录
        paginator = Paginator(self.obj_list, self.page_num)
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
def backend_UserList(request):
    '''返回所有用户的View'''
    obj = User.objects.all()
    page_num = 15
    context = Page_List_View(request, obj, page_num).get_page_context()
    try:
        registerinfo = request.session['registerinfo']
        del request.session['registerinfo']
        context.update({'registerinfo': registerinfo})
    except:
        pass
    return render(request, 'backend/userlist.html', context=context)


@permission_required('shadowsocks')
def user_delete(request, pk):
    '''删除user'''
    user = User.objects.filter(pk=pk)
    user.delete()

    obj = User.objects.all()
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


@permission_required('shadowsocks')
def backend_invite(request):
    '''邀请码生成'''
    code_list = InviteCode.objects.filter(type=0, isused=False, code_id=1)
    return render(request, 'backend/invitecode.html', {'code_list': code_list, })


@permission_required('shadowsocks')
def gen_invite_code(request):

    Num = request.GET.get('num')
    type = request.GET.get('type')
    for i in range(int(Num)):
        code = InviteCode(type=type)
        code.save()

    code_list = InviteCode.objects.filter(type=0, isused=False)
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
    obj = MoneyCode.objects.all()
    page_num = 10
    context = Page_List_View(request, obj, page_num).get_page_context()
    try:
        context['registerinfo'] = request.session['registerinfo']
        del request.session['registerinfo']
    except:
        pass
    # 获取充值的金额和数量
    Num = request.GET.get('num')
    money = request.GET.get('money')
    if Num and money:
        for i in range(int(Num)):
            code = MoneyCode(number=money)
            code.save()
        registerinfo = {
            'title': '成功',
            'subtitle': '添加{}元充值码{}个'.format(money, Num),
            'status': 'success'}
        request.session['registerinfo'] = registerinfo
        return redirect('/backend/charge')
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
        # 转换为GB
        data = request.POST.copy()
        data['transfer'] = eval(data['transfer']) * settings.GB
        form = ShopForm(data, instance=good)
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
        data = {'transfer': round(good.transfer / settings.GB)}
        form = ShopForm(initial=data, instance=good)
        context = {
            'form': form,
            'good': good,
        }
        return render(request, 'backend/goodedit.html', context=context)


@permission_required('shadowsocks')
def good_create(request):
    '''商品创建'''
    if request.method == "POST":
        # 转换为GB
        data = request.POST.copy()
        data['transfer'] = eval(data['transfer']) * settings.GB
        form = ShopForm(data)
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
    obj = PurchaseHistory.objects.all()
    page_num = 10
    context = Page_List_View(request, obj, page_num).get_page_context()
    return render(request, 'backend/purchasehistory.html', context=context)


@permission_required('shadowsocks')
def backend_anno(request):
    '''公告管理界面'''
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
                'subtitle': '数据更新成功',
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
    ticket = Ticket.objects.filter(status='开启')
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


@permission_required('ssserver')
def backend_alive_user(request):
    obj_list = []
    for node in Node.objects.all():
        obj_list.extend(AliveIp.recent_alive(node.node_id))
    page_num = 15
    context = Page_List_View(request, obj_list, page_num).get_page_context()

    return render(request, 'backend/aliveuser.html', context=context)
