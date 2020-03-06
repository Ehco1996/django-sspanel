from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
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


class IndexView(View):
    def get(self, request):
        """跳转到首页"""
        return render(request, "sspanel/index.html")


class HelpView(View):
    def get(self, request):
        """跳转到帮助界面"""
        return render(request, "sspanel/help.html")


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
        if not settings.ALLOW_REGISTER:
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


class UserLogInView(View):
    def post(self, request):
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

        context = {"form": LoginForm()}
        return render(request, "sspanel/login.html", context=context)

    def get(self, request):
        context = {"form": LoginForm()}
        return render(request, "sspanel/login.html", context=context)


class UserLogOutView(View):
    def get(self, request):
        logout(request)
        messages.warning(request, "欢迎下次再来", extra_tags="注销成功")
        return HttpResponseRedirect(reverse("sspanel:index"))


class InviteCodeView(View):
    def get(self, request):
        code_list = InviteCode.list_by_code_type(InviteCode.TYPE_PUBLIC)
        return render(request, "sspanel/invite.html", context={"code_list": code_list})


class AffInviteView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        context = {
            "code_list": InviteCode.list_by_user_id(user.pk),
            "invite_percent": settings.INVITE_PERCENT * 100,
            "invitecode_num": InviteCode.calc_num_by_user(user),
            "ref_link": user.ref_link,
        }
        return render(request, "sspanel/aff_invite.html", context=context)


class AffStatusView(LoginRequiredMixin, View):
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


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        # 获取公告
        anno = Announcement.objects.first()
        min_traffic = traffic_format(settings.MIN_CHECKIN_TRAFFIC)
        max_traffic = traffic_format(settings.MAX_CHECKIN_TRAFFIC)
        context = {
            "user": user,
            "anno": anno,
            "min_traffic": min_traffic,
            "max_traffic": max_traffic,
            "themes": THEME_CHOICES,
            "sub_link": user.sub_link,
            "sub_types": User.SUB_TYPES,
            "user_sub_type": user.get_sub_type_display(),
            "methods": [m[0] for m in METHOD_CHOICES],
        }
        return render(request, "sspanel/userinfo.html", context=context)


class NodeInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        # ss node
        ss_node_list = [
            node.to_dict_with_extra_info(user) for node in SSNode.get_active_nodes()
        ]
        # vmess node
        vmess_node_list = [
            node.to_dict_with_extra_info(user) for node in VmessNode.get_active_nodes()
        ]
        context = {
            "ss_node_list": ss_node_list,
            "vmess_node_list": vmess_node_list,
            "user": user,
        }
        Announcement.send_first_visit_msg(request)
        return render(request, "sspanel/nodeinfo.html", context=context)


class UserTrafficLog(LoginRequiredMixin, View):
    def get(self, request):
        ss_node_list = SSNode.get_active_nodes()
        vmess_node_list = VmessNode.get_active_nodes()
        context = {
            "user": request.user,
            "ss_node_list": ss_node_list,
            "vmess_node_list": vmess_node_list,
        }
        return render(request, "sspanel/user_traffic_log.html", context=context)


class ShopView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        goods = Goods.objects.filter(status=1)
        context = {"user": user, "goods": goods}
        return render(request, "sspanel/shop.html", context=context)


class ClientView(LoginRequiredMixin, View):
    def get(self, request):
        """跳转到客户端界面"""
        return render(request, "sspanel/client.html")


class DonateView(LoginRequiredMixin, View):
    def get(self, request):
        """捐赠界面和支付宝当面付功能"""
        donatelist = Donate.objects.all()[:8]
        context = {"donatelist": donatelist}
        return render(request, "sspanel/donate.html", context=context)


class PurchaseLogView(LoginRequiredMixin, View):
    def get(self, request):
        """用户购买记录页面"""

        records = PurchaseHistory.objects.filter(user=request.user)[:10]
        context = {"records": records}
        return render(request, "sspanel/purchaselog.html", context=context)


class ChargeView(LoginRequiredMixin, View):
    def get(self, request):
        """充值界面的跳转"""
        user = request.user
        codelist = MoneyCode.objects.filter(user=user)
        context = {"user": user, "codelist": codelist}
        return render(request, "sspanel/chargecenter.html", context=context)

    def post(self, request):
        user = request.user
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


class AnnouncementView(LoginRequiredMixin, View):
    def get(self, request):
        """网站公告列表"""
        anno = Announcement.objects.all()
        return render(request, "sspanel/announcement.html", {"anno": anno})


class TicketsView(LoginRequiredMixin, View):
    def get(self, request):
        """工单系统"""
        ticket = Ticket.objects.filter(user=request.user)
        context = {"ticket": ticket}
        return render(request, "sspanel/ticket.html", context=context)


class TicketCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "sspanel/ticketcreate.html")

    def post(self, request):
        """工单提交"""
        title = request.POST.get("title", "")
        body = request.POST.get("body", "")
        Ticket.objects.create(user=request.user, title=title, body=body)
        messages.success(request, "数据更新成功！", extra_tags="添加成功")
        return HttpResponseRedirect(reverse("sspanel:tickets"))


class TicketDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """工单编辑"""
        ticket = Ticket.objects.get(pk=pk)
        context = {"ticket": ticket}
        return render(request, "sspanel/ticketedit.html", context=context)

    def post(self, request, pk):
        ticket = Ticket.objects.get(pk=pk)
        ticket.title = request.POST.get("title", "")
        ticket.body = request.POST.get("body", "")
        ticket.save()
        messages.success(request, "数据更新成功", extra_tags="修改成功")
        return HttpResponseRedirect(reverse("sspanel:tickets"))


class TicketDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """删除指定"""
        ticket = Ticket.objects.filter(pk=pk, user=request.user).first()
        if ticket:
            ticket.delete()
            messages.success(request, "该工单已经删除", extra_tags="删除成功")
        else:
            messages.error(request, "该工单不存在", extra_tags="删除失败")
        return HttpResponseRedirect(reverse("sspanel:tickets"))
