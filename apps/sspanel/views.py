import tomd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from apps.constants import METHOD_CHOICES, OBFS_CHOICES, PROTOCOL_CHOICES, THEME_CHOICES
from apps.custom_views import Page_List_View
from apps.sspanel.forms import AnnoForm, GoodsForm, LoginForm, NodeForm, RegisterForm
from apps.sspanel.models import (
    Announcement,
    Donate,
    Goods,
    InviteCode,
    MoneyCode,
    PurchaseHistory,
    RebateRecord,
    Ticket,
    User,
)
from apps.ssserver.models import AliveIp, Node, NodeOnlineLog, Suser
from apps.utils import traffic_format


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("sspanel:userinfo"))
        ref = request.GET.get("ref")
        if ref:
            form = RegisterForm(initial={"ref": ref})
        else:
            form = RegisterForm(initial={"invitecode": request.GET.get("invitecode")})
        return render(request, "sspanel/register.html", {"form": form})

    def post(self, request):
        if settings.ALLOW_REGISTER is False:
            return HttpResponse("已经关闭注册了喵")

        form = RegisterForm(data=request.POST)
        if form.is_valid():
            user = User.add_new_user(form.cleaned_data)
            if not user:
                messages.error(request, "服务出现了点小问题", extra_tags="请尝试或者联系站长~")
                return render(request, "sspanel/register.html", {"form": form})
            else:
                messages.success(request, "自动跳转到用户中心", extra_tags="注册成功！")
                user = authenticate(
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password1"],
                )
                login(request, user)
                return HttpResponseRedirect(reverse("sspanel:userinfo"))
        return render(request, "sspanel/register.html", {"form": form})


class InviteCodeView(View):
    def get(self, request):
        code_list = InviteCode.list_by_code_type(InviteCode.TYPE_PUBLIC)
        return render(request, "sspanel/invite.html", context={"code_list": code_list})


class AffInviteView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        context = {
            "code_list": InviteCode.list_by_user_id(user.pk),
            "invite_percent": settings.INVITE_PERCENT * 100,
            "invitecode_num": InviteCode.calc_num_by_user(user),
            "ref_link": user.ref_link,
        }
        return render(request, "sspanel/aff_invite.html", context=context)


class AffStatusView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        rebate_logs = RebateRecord.list_by_user_id_with_consumer_username(user.pk)
        bar_config = {
            "labels": ["z", "v", "x", "x", "z", "v", "x", "x", "z", "v"],
            "data": [1, 2, 3, 4, 1, 1, 1, 1, 1, 2],
            "data_title": "每日邀请注册人数",
        }
        context = {"rebate_logs": rebate_logs, "user": user, "bar_config": bar_config}
        return render(request, "sspanel/aff_status.html", context=context)


class UserInfoView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        # 获取公告
        anno = Announcement.objects.first()
        min_traffic = traffic_format(settings.MIN_CHECKIN_TRAFFIC)
        max_traffic = traffic_format(settings.MAX_CHECKIN_TRAFFIC)
        remain_traffic = "{:.2f}".format(100 - user.ss_user.used_percentage)
        context = {
            "user": user,
            "anno": anno,
            "remain_traffic": remain_traffic,
            "min_traffic": min_traffic,
            "max_traffic": max_traffic,
            "import_code": Node.get_import_code(user),
            "themes": THEME_CHOICES,
            "sub_link": user.sub_link,
            "sub_types": User.SUB_TYPES,
            "user_sub_type": user.get_sub_type_display(),
        }
        return render(request, "sspanel/userinfo.html", context=context)


class NodeInfoView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        ss_user = user.ss_user
        node_list = [node.to_dict_with_extra_info(
            ss_user) for node in Node.get_active_nodes()]
        context = {
            "node_list": node_list,
            "user": user,
            "sub_link": user.sub_link,
        }
        return render(request, "sspanel/nodeinfo.html", context=context)


def index(request):
    """跳转到首页"""

    return render(
        request, "sspanel/index.html", {"allow_register": settings.ALLOW_REGISTER}
    )


def sshelp(request):
    """跳转到帮助界面"""
    return render(request, "sspanel/help.html")


@login_required
def ssclient(request):
    """跳转到客户端界面"""
    return render(request, "sspanel/client.html")


def user_login(request):
    """用户登录函数"""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user and user.is_active:
                login(request, user)
                messages.success(request, "自动跳转到用户中心", extra_tags="登录成功！")
                return HttpResponseRedirect(reverse("sspanel:userinfo"))
            else:
                messages.error(request, "请重新填写信息！", extra_tags="登录失败！")
    context = {"form": LoginForm(), "USE_SMTP": settings.USE_SMTP}
    return render(request, "sspanel/login.html", context=context)


def user_logout(request):
    """用户登出函数"""
    logout(request)
    messages.success(request, "欢迎下次再来", extra_tags="注销成功")
    return HttpResponseRedirect(reverse("index"))


@login_required
def ss_user_settings(request):
    """跳转到资料编辑界面"""
    ss_user = request.user.ss_user
    methods = [m[0] for m in METHOD_CHOICES]
    protocols = [p[0] for p in PROTOCOL_CHOICES]
    obfss = [o[0] for o in OBFS_CHOICES]

    context = {
        "ss_user": ss_user,
        "methods": methods,
        "protocols": protocols,
        "obfss": obfss,
    }
    return render(request, "sspanel/ss_user_settings.html", context=context)


@login_required
def donate(request):
    """捐赠界面和支付宝当面付功能"""
    donatelist = Donate.objects.all()[:8]
    context = {"donatelist": donatelist}
    if settings.USE_ALIPAY is True:
        context["alipay"] = True
    else:
        # 关闭支付宝支付
        context["alipay"] = False
    return render(request, "sspanel/donate.html", context=context)


@login_required
def trafficlog(request):
    """跳转到流量记录的页面"""

    ss_user = request.user.ss_user
    nodes = Node.objects.filter(show=1)
    context = {"ss_user": ss_user, "nodes": nodes}
    return render(request, "sspanel/trafficlog.html", context=context)


@login_required
def shop(request):
    """跳转到商品界面"""
    ss_user = request.user
    goods = Goods.objects.filter(status=1)
    context = {"ss_user": ss_user, "goods": goods}
    return render(request, "sspanel/shop.html", context=context)


@login_required
def purchaselog(request):
    """用户购买记录页面"""

    records = PurchaseHistory.objects.filter(user=request.user)[:10]
    context = {"records": records}
    return render(request, "sspanel/purchaselog.html", context=context)


@login_required
def chargecenter(request):
    """充值界面的跳转"""
    user = request.user
    codelist = MoneyCode.objects.filter(user=user)

    context = {"user": user, "codelist": codelist}

    return render(request, "sspanel/chargecenter.html", context=context)


@login_required
def charge(request):
    user = request.user
    if request.method == "POST":
        input_code = request.POST.get("chargecode")
        # 在数据库里检索充值
        code = MoneyCode.objects.filter(code=input_code).first()
        # 判断充值码是否存在
        if not code:
            messages.error(request, "请重新获取充值码", extra_tags="充值码失效")
            return HttpResponseRedirect(reverse("sspanel:chargecenter"))
        else:
            # 判断充值码是否被使用
            if code.isused is True:
                # 当被使用的是时候
                messages.error(request, "请重新获取充值码", extra_tags="充值码失效")
                return HttpResponseRedirect(reverse("sspanel:chargecenter"))
            else:
                # 充值操作
                user.balance += code.number
                code.user = user.username
                code.isused = True
                user.save()
                code.save()
                # 将充值记录和捐赠绑定
                Donate.objects.create(user=user, money=code.number)
                messages.success(request, "请去商店购买商品！", extra_tags="充值成功！")
                return HttpResponseRedirect(reverse("sspanel:chargecenter"))


@login_required
def announcement(request):
    """网站公告列表"""
    anno = Announcement.objects.all()
    return render(request, "sspanel/announcement.html", {"anno": anno})


@login_required
def ticket(request):
    """工单系统"""
    ticket = Ticket.objects.filter(user=request.user)
    context = {"ticket": ticket}
    return render(request, "sspanel/ticket.html", context=context)


@login_required
def ticket_create(request):
    """工单提交"""
    if request.method == "POST":
        title = request.POST.get("title", "")
        body = request.POST.get("body", "")
        Ticket.objects.create(user=request.user, title=title, body=body)
        messages.success(request, "数据更新成功！", extra_tags="添加成功")
        return HttpResponseRedirect(reverse("sspanel:ticket"))
    else:
        return render(request, "sspanel/ticketcreate.html")


@login_required
def ticket_delete(request, pk):
    """删除指定"""
    ticket = Ticket.objects.get(pk=pk)
    ticket.delete()
    messages.success(request, "该工单已经删除", extra_tags="删除成功")
    return HttpResponseRedirect(reverse("sspanel:ticket"))


@login_required
def ticket_edit(request, pk):
    """工单编辑"""
    ticket = Ticket.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        title = request.POST.get("title", "")
        body = request.POST.get("body", "")
        ticket.title = title
        ticket.body = body
        ticket.save()
        messages.success(request, "数据更新成功", extra_tags="修改成功")
        return HttpResponseRedirect(reverse("sspanel:ticket"))
    else:
        context = {"ticket": ticket}
        return render(request, "sspanel/ticketedit.html", context=context)


# ==================================
# 网站后台界面
# ==================================


@permission_required("sspanel")
def system_status(request):
    """跳转到后台界面"""
    context = {"total_user_num": User.get_total_user_num()}
    return render(request, "backend/index.html", context=context)


@permission_required("sspanel")
def backend_node_info(request):
    """配置编辑界面"""
    nodes = Node.objects.all()
    context = {"nodes": nodes}
    return render(request, "backend/nodeinfo.html", context=context)


@permission_required("sspanel")
def node_delete(request, node_id):
    """删除节点"""
    node = Node.objects.filter(node_id=node_id)
    node.delete()
    messages.success(request, "成功啦", extra_tags="删除节点")
    return HttpResponseRedirect(reverse("sspanel:backend_node_info"))


@permission_required("sspanel")
def node_edit(request, node_id):
    """编辑节点"""
    node = Node.objects.get(node_id=node_id)
    # 当为post请求时，修改数据
    if request.method == "POST":
        form = NodeForm(request.POST, instance=node)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="修改成功")
            return HttpResponseRedirect(reverse("sspanel:backend_node_info"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form, "node": node}
            return render(request, "backend/nodeedit.html", context=context)
    # 当请求不是post时，渲染form
    else:
        form = NodeForm(
            instance=node, initial={"total_traffic": node.total_traffic // settings.GB}
        )
        context = {"form": form, "node": node}
        return render(request, "backend/nodeedit.html", context=context)


@permission_required("sspanel")
def node_create(request):
    """创建节点"""
    if request.method == "POST":
        form = NodeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功！", extra_tags="添加成功")
            return HttpResponseRedirect(reverse("sspanel:backend_node_info"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form}
            return render(request, "backend/nodecreate.html", context=context)

    else:
        form = NodeForm()
        return render(request, "backend/nodecreate.html", context={"form": form})


@permission_required("sspanel")
def backend_userlist(request):
    """返回所有用户的View"""
    obj = User.objects.all().order_by("-date_joined")
    page_num = 15
    context = Page_List_View(request, obj, page_num).get_page_context()
    return render(request, "backend/userlist.html", context)


@permission_required("sspanel")
def user_delete(request, pk):
    """删除user"""
    user = User.objects.get(pk=pk)
    user.delete()
    messages.success(request, "成功啦", extra_tags="删除用户")
    return HttpResponseRedirect(reverse("sspanel:user_list"))


@permission_required("sspanel")
def user_search(request):
    """用户搜索结果"""
    q = request.GET.get("q")
    contacts = User.objects.filter(
        Q(username__icontains=q) | Q(email__icontains=q) | Q(pk__icontains=q)
    )
    context = {"contacts": contacts}
    return render(request, "backend/userlist.html", context=context)


@permission_required("sspanel")
def user_status(request):
    """站内用户分析"""
    today_register_user = User.get_today_register_user().values()[:10]
    # find inviter
    for u in today_register_user:
        try:
            u["inviter"] = User.objects.get(pk=u["inviter_id"])
        except User.DoesNotExist:
            u["inviter"] = "None"

    context = {
        "total_user_num": User.get_total_user_num(),
        "alive_user_count": NodeOnlineLog.get_online_user_count(),
        "today_checked_user_count": Suser.get_today_checked_user_num(),
        "today_register_user_count": len(today_register_user),
        "traffic_users": Suser.get_user_order_by_traffic(count=10),
        "rich_users_data": Donate.get_most_donated_user_by_count(10),
        "today_register_user": today_register_user,
    }
    return render(request, "backend/userstatus.html", context=context)


@permission_required("sspanel")
def backend_invite(request):
    """邀请码生成"""
    # TODO 这里加入一些统计功能
    code_list = InviteCode.objects.filter(code_type=0, used=False, user_id=1)
    return render(request, "backend/invitecode.html", {"code_list": code_list})


@permission_required("sspanel")
def gen_invite_code(request):

    Num = request.GET.get("num")
    code_type = request.GET.get("type")
    for i in range(int(Num)):
        code = InviteCode(code_type=code_type)
        code.save()
    messages.success(request, "添加邀请码{}个".format(Num), extra_tags="成功")
    return HttpResponseRedirect(reverse("sspanel:backend_invite"))


@permission_required("sspanel")
def backend_charge(request):
    """后台充值码界面"""
    # 获取所有充值码记录
    obj = MoneyCode.objects.all()
    page_num = 10
    context = Page_List_View(request, obj, page_num).get_page_context()
    # 获取充值的金额和数量
    Num = request.GET.get("num")
    money = request.GET.get("money")
    if Num and money:
        for i in range(int(Num)):
            code = MoneyCode(number=money)
            code.save()
        messages.success(request, "添加{}元充值码{}个".format(money, Num), extra_tags="成功")
        return HttpResponseRedirect(reverse("sspanel:backend_charge"))
    return render(request, "backend/charge.html", context=context)


@permission_required("sspanel")
def backend_shop(request):
    """商品管理界面"""

    goods = Goods.objects.all()
    context = {"goods": goods}
    return render(request, "backend/shop.html", context=context)


@permission_required("sspanel")
def good_delete(request, pk):
    """删除商品"""
    good = Goods.objects.filter(pk=pk)
    good.delete()
    messages.success(request, "成功啦", extra_tags="删除商品")
    return HttpResponseRedirect(reverse("sspanel:backend_shop"))


@permission_required("sspanel")
def good_edit(request, pk):
    """商品编辑"""

    good = Goods.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        # 转换为GB
        data = request.POST.copy()
        data["transfer"] = eval(data["transfer"]) * settings.GB
        form = GoodsForm(data, instance=good)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="修改成功")
            return HttpResponseRedirect(reverse("sspanel:backend_shop"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form, "good": good}
            return render(request, "backend/goodedit.html", context=context)
    # 当请求不是post时，渲染form
    else:
        data = {"transfer": round(good.transfer / settings.GB)}
        form = GoodsForm(initial=data, instance=good)
        context = {"form": form, "good": good}
        return render(request, "backend/goodedit.html", context=context)


@permission_required("sspanel")
def good_create(request):
    """商品创建"""
    if request.method == "POST":
        # 转换为GB
        data = request.POST.copy()
        data["transfer"] = eval(data["transfer"]) * settings.GB
        form = GoodsForm(data)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功！", extra_tags="添加成功")
            return HttpResponseRedirect(reverse("sspanel:backend_shop"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form}
            return render(request, "backend/goodcreate.html", context=context)
    else:
        form = GoodsForm()
        return render(request, "backend/goodcreate.html", context={"form": form})


@permission_required("sspanel")
def purchase_history(request):
    """购买历史"""
    obj = PurchaseHistory.objects.all()
    page_num = 10
    context = Page_List_View(request, obj, page_num).get_page_context()
    return render(request, "backend/purchasehistory.html", context=context)


@permission_required("sspanel")
def backend_anno(request):
    """公告管理界面"""
    anno = Announcement.objects.all()
    context = {"anno": anno}
    return render(request, "backend/annolist.html", context=context)


@permission_required("sspanel")
def anno_delete(request, pk):
    """删除公告"""
    anno = Announcement.objects.filter(pk=pk)
    anno.delete()
    messages.success(request, "成功啦", extra_tags="删除公告")
    return HttpResponseRedirect(reverse("sspanel:backend_anno"))


@permission_required("sspanel")
def anno_create(request):
    """公告创建"""
    if request.method == "POST":
        form = AnnoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="添加成功")
            return HttpResponseRedirect(reverse("sspanel:backend_anno"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form}
            return render(request, "backend/annocreate.html", context=context)
    else:
        form = AnnoForm()
        return render(request, "backend/annocreate.html", context={"form": form})


@permission_required("sspanel")
def anno_edit(request, pk):
    """公告编辑"""
    anno = Announcement.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        form = AnnoForm(request.POST, instance=anno)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="修改成功")
            return HttpResponseRedirect(reverse("sspanel:backend_anno"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form, "anno": anno}
            return render(request, "backend/annoedit.html", context=context)
    # 当请求不是post时，渲染form
    else:
        anno.body = tomd.convert(anno.body)
        context = {"anno": anno}
        return render(request, "backend/annoedit.html", context=context)


@permission_required("sspanel")
def backend_ticket(request):
    """工单系统"""
    ticket = Ticket.objects.filter(status=1)
    context = {"ticket": ticket}
    return render(request, "backend/ticket.html", context=context)


@permission_required("sspanel")
def backend_ticketedit(request, pk):
    """后台工单编辑"""
    ticket = Ticket.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        title = request.POST.get("title", "")
        body = request.POST.get("body", "")
        status = request.POST.get("status", 1)
        ticket.title = title
        ticket.body = body
        ticket.status = status
        ticket.save()

        messages.success(request, "数据更新成功", extra_tags="修改成功")
        return HttpResponseRedirect(reverse("sspanel:backend_ticket"))
    # 当请求不是post时，渲染
    else:
        context = {"ticket": ticket}
        return render(request, "backend/ticketedit.html", context=context)


@permission_required("ssserver")
def backend_alive_user(request):
    user_list = []
    for node_id in Node.get_node_ids_by_show():
        user_list.extend(AliveIp.recent_alive(node_id))
    page_num = 15
    context = Page_List_View(request, user_list, page_num).get_page_context()

    return render(request, "backend/aliveuser.html", context=context)
