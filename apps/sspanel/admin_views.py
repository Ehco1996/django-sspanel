import tomd
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from apps import utils
from apps.custom_views import PageListView
from apps.mixin import StaffRequiredMixin
from apps.proxy.models import ProxyNode, RelayNode, UserTrafficLog
from apps.sspanel.forms import AnnoForm, GoodsForm
from apps.sspanel.models import (
    Announcement,
    Donate,
    Goods,
    InviteCode,
    MoneyCode,
    PurchaseHistory,
    Ticket,
    User,
    UserCheckInLog,
)


class NodeListView(StaffRequiredMixin, View):
    def get(self, request):
        context = {
            "proxy_node_list": ProxyNode.objects.all(),
            "relay_node_list": RelayNode.objects.all(),
        }
        return render(request, "my_admin/node_list.html", context=context)


class NodeDeleteView(StaffRequiredMixin, View):
    def get(self, request, node_id):
        node = ProxyNode.get_or_none(node_id)
        node and node.delete()
        messages.success(request, "成功啦", extra_tags="删除节点")
        return HttpResponseRedirect(reverse("sspanel:admin_node_list"))


class UserStatusView(StaffRequiredMixin, View):
    def get(self, request):
        today_register_user = User.get_today_register_user().values()[:10]
        # find inviter
        for u in today_register_user:
            try:
                u["inviter"] = User.objects.get(pk=u["inviter_id"])
            except User.DoesNotExist:
                u["inviter"] = "None"

        context = {
            "total_user_num": User.get_total_user_num(),
            "alive_user_count": UserTrafficLog.get_all_node_online_user_count(),
            "today_checked_user_count": UserCheckInLog.get_checkin_user_count(
                utils.get_current_datetime().date()
            ),
            "today_register_user_count": len(today_register_user),
            "traffic_users": User.get_user_order_by_traffic(count=10),
            "rich_users_data": Donate.get_most_donated_user_by_count(10),
            "today_register_user": today_register_user,
        }
        return render(request, "my_admin/user_status.html", context=context)


class SystemStatusView(StaffRequiredMixin, View):
    def get(self, request):
        """跳转到后台界面"""
        context = {"total_user_num": User.get_total_user_num()}
        return render(request, "my_admin/index.html", context=context)


class InviteCodeView(StaffRequiredMixin, View):
    def get(self, request):
        """邀请码生成"""
        code_list = InviteCode.objects.filter(
            code_type=InviteCode.TYPE_PUBLIC, used=False
        )
        return render(request, "my_admin/invitecode.html", {"code_list": code_list})

    def post(self, request):
        num = int(request.POST.get("num", 0))
        for _ in range(num):
            code = InviteCode(code_type=request.POST.get("type"))
            code.save()
        messages.success(request, "添加邀请码{}个".format(num), extra_tags="成功")
        return HttpResponseRedirect(reverse("sspanel:admin_invite"))


class ChargeView(StaffRequiredMixin, View):
    def get(self, request):
        """后台充值码界面"""
        obj = MoneyCode.objects.all()
        page_num = 10
        context = PageListView(request, obj, page_num).get_page_context()
        return render(request, "my_admin/charge.html", context=context)

    def post(self, request):
        num = request.POST.get("num")
        money = request.POST.get("money")
        for _ in range(int(num)):
            code = MoneyCode(number=money)
            code.save()
        messages.success(request, "添加{}元充值码{}个".format(money, num), extra_tags="成功")
        return HttpResponseRedirect(reverse("sspanel:admin_charge"))


class PurchaseHistoryView(StaffRequiredMixin, View):
    def get(self, request):
        obj = PurchaseHistory.objects.all()
        context = PageListView(request, obj, 10).get_page_context()
        return render(request, "my_admin/purchasehistory.html", context=context)


class TicketsView(StaffRequiredMixin, View):
    def get(self, request):
        ticket = Ticket.objects.filter(status=1)
        context = {"ticket": ticket}
        return render(request, "my_admin/tickets.html", context=context)


class TicketDetailView(StaffRequiredMixin, View):
    def get(self, request, pk):
        ticket = Ticket.objects.get(pk=pk)
        context = {"ticket": ticket}
        return render(request, "my_admin/ticket_detail.html", context=context)

    def post(self, request, pk):
        ticket = Ticket.objects.get(pk=pk)
        ticket.title = request.POST.get("title", "")
        ticket.body = request.POST.get("body", "")
        ticket.status = request.POST.get("status", 1)
        ticket.save()
        messages.success(request, "数据更新成功", extra_tags="修改成功")
        return HttpResponseRedirect(reverse("sspanel:admin_tickets"))


class GoodsView(StaffRequiredMixin, View):
    def get(self, request):
        goods = Goods.objects.all()
        context = {"goods": goods}
        return render(request, "my_admin/goods.html", context=context)


class GoodDeleteView(StaffRequiredMixin, View):
    def get(self, request, pk):
        good = Goods.objects.filter(pk=pk).first()
        good.delete()
        messages.success(request, "成功啦", extra_tags="删除商品")
        return HttpResponseRedirect(reverse("sspanel:admin_goods"))


class GoodsCreateView(StaffRequiredMixin, View):
    def get(self, request):
        form = GoodsForm()
        return render(request, "my_admin/good_create.html", context={"form": form})

    def post(self, request):
        data = request.POST.copy()
        data["transfer"] = eval(data["transfer"]) * settings.GB
        form = GoodsForm(data)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功！", extra_tags="添加成功")
            return HttpResponseRedirect(reverse("sspanel:admin_goods"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form}
            return render(request, "my_admin/good_create.html", context=context)


class GoodDetailView(StaffRequiredMixin, View):
    def get(self, request, pk):
        good = Goods.objects.get(pk=pk)
        data = {"transfer": round(good.transfer / settings.GB)}
        form = GoodsForm(initial=data, instance=good)
        context = {"form": form, "good": good}
        return render(request, "my_admin/good_detail.html", context=context)

    def post(self, request, pk):
        good = Goods.objects.get(pk=pk)
        data = request.POST.copy()
        data["transfer"] = eval(data["transfer"]) * settings.GB
        form = GoodsForm(data, instance=good)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="修改成功")
            return HttpResponseRedirect(reverse("sspanel:admin_goods"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form, "good": good}
            return render(request, "my_admin/good_detail.html", context=context)


class AnnouncementsView(StaffRequiredMixin, View):
    def get(self, request):
        anno = Announcement.objects.all()
        context = {"anno": anno}
        return render(request, "my_admin/announcements.html", context=context)


class AnnouncementDetailView(StaffRequiredMixin, View):
    def get(self, request, pk):
        anno = Announcement.objects.get(pk=pk)
        anno.body = tomd.convert(anno.body)
        context = {"anno": anno}
        return render(request, "my_admin/announcement_detail.html", context=context)

    def post(self, request, pk):
        anno = Announcement.objects.get(pk=pk)
        form = AnnoForm(request.POST, instance=anno)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="修改成功")
            return HttpResponseRedirect(reverse("sspanel:admin_announcements"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form, "anno": anno}
            return render(request, "my_admin/announcement_detail.html", context=context)


class AnnouncementDeleteView(StaffRequiredMixin, View):
    def get(self, request, pk):
        anno = Announcement.objects.filter(pk=pk).first()
        anno.delete()
        messages.success(request, "成功啦", extra_tags="删除公告")
        return HttpResponseRedirect(reverse("sspanel:admin_announcements"))


class AnnouncementCreateView(StaffRequiredMixin, View):
    def get(self, request):
        form = AnnoForm()
        return render(
            request, "my_admin/announcement_create.html", context={"form": form}
        )

    def post(self, request):
        form = AnnoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "数据更新成功", extra_tags="添加成功")
            return HttpResponseRedirect(reverse("sspanel:admin_announcements"))
        else:
            messages.error(request, "数据填写错误", extra_tags="错误")
            context = {"form": form}
            return render(request, "my_admin/announcement_create.html", context=context)
