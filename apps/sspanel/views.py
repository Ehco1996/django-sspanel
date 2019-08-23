from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from apps.constants import METHOD_CHOICES, THEME_CHOICES
from apps.sspanel.forms import LoginForm, RegisterForm
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
    SSNode,
    VmessNode,
)
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
        user_ss_config = user.user_ss_config
        user_traffic = user_ss_config.user_traffic
        # 获取公告
        anno = Announcement.objects.first()
        min_traffic = traffic_format(settings.MIN_CHECKIN_TRAFFIC)
        max_traffic = traffic_format(settings.MAX_CHECKIN_TRAFFIC)
        remain_traffic = "{:.2f}".format(100 - user_traffic.used_percentage)
        context = {
            "user": user,
            "user_traffic": user_traffic,
            "anno": anno,
            "remain_traffic": remain_traffic,
            "min_traffic": min_traffic,
            "max_traffic": max_traffic,
            "import_links": user_ss_config.get_import_links(),
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
        user_ss_config = user.user_ss_config
        # ss node
        ss_node_list = [
            node.to_dict_with_extra_info(user_ss_config)
            for node in SSNode.get_active_nodes()
        ]

        # vmess node
        vmess_node_list = [
            node.to_dict_with_extra_info(user) for node in VmessNode.get_active_nodes()
        ]

        context = {
            "ss_node_list": ss_node_list,
            "vmess_node_list": vmess_node_list,
            "user": user,
            "sub_link": user.sub_link,
        }
        return render(request, "sspanel/nodeinfo.html", context=context)


class UserTrafficLog(View):
    @method_decorator(login_required)
    def get(self, request):
        node_list = SSNode.get_active_nodes()
        context = {"user": request.user, "node_list": node_list}
        return render(request, "sspanel/user_traffic_log.html", context=context)


class UserSSNodeConfigView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        user_ss_config = user.user_ss_config
        configs = [
            node.to_dict_with_user_ss_config(user_ss_config)
            for node in SSNode.get_user_active_nodes(user)
        ]
        return JsonResponse({"configs": configs})


class UserSettingView(View):
    @method_decorator(login_required)
    def get(self, request):
        methods = [m[0] for m in METHOD_CHOICES]
        context = {"user_ss_config": request.user.user_ss_config, "methods": methods}
        return render(request, "sspanel/user_settings.html", context=context)


class ShopView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        goods = Goods.objects.filter(status=1)
        context = {"user": user, "goods": goods}
        return render(request, "sspanel/shop.html", context=context)


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
