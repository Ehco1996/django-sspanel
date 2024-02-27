from typing import Any

from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.utils.html import format_html

from apps.sub import UserSubManager

from . import models


class UserAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "id",
        "level",
        "balance",
        "used_percentage",
        "date_joined",
        "uid",
    ]
    search_fields = ["username", "email", "id", "uid"]
    list_filter = ["level"]
    list_per_page = 31


class UserSocialProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user_id",
        "platform",
        "platform_username",
        "created_at",
    ]
    list_per_page = 31
    search_fields = ["user__username", "user_id"]
    list_filter = ["user_id", "platform", "created_at"]
    ordering = ("-created_at",)


class UserOrderAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "status",
        "out_trade_no",
        "amount",
        "created_at",
        "user_date_joined",
        "inviter",
    ]
    list_per_page = 31

    def user_date_joined(self, obj):
        return obj.user.date_joined

    def inviter(self, obj):
        if obj.user.inviter_id:
            return models.User.get_by_id_with_cache(obj.user.inviter_id)
        return "无邀请人"

    user_date_joined.short_description = "用户注册时间"
    inviter.short_description = "邀请人"

    search_fields = ["user__username", "user__id"]
    list_filter = ["amount", "status", "created_at"]
    ordering = ("-created_at",)


class UserCheckInAdmin(admin.ModelAdmin):
    list_display = ["user", "user_id", "increased_traffic", "date"]
    search_fields = ["user_id", "date"]
    list_filter = ["date"]


class UserRefLogAdmin(admin.ModelAdmin):
    list_display = ["user", "user_id", "register_count", "date"]
    search_fields = ["user_id", "date"]
    list_filter = ["date"]


class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ["good_name", "user", "money", "created_at"]
    search_fields = ["user"]
    list_filter = ["good_name", "created_at"]


class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "created_at", "used", "code_type"]
    search_fields = ["code"]
    list_per_page = 10
    actions = ["batch_add"]
    list_filter = ["used"]

    def batch_add(self, request, queryset):
        # todo support params
        amount = request.POST.get("amount", 10)
        number = request.POST.get("number", 10)
        messages.add_message(
            request,
            messages.SUCCESS,
            f"create code:{amount} x {number}",
        )
        models.InviteCode.batch_create(number, 1)

    batch_add.short_description = "批量添加"
    batch_add.type = "danger"


class MoneyCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "number", "isused", "user"]
    list_per_page = 10
    actions = ["batch_add"]
    list_filter = ["isused"]

    def batch_add(self, request, queryset):
        # todo support params
        amount = request.POST.get("amount", 10)
        number = request.POST.get("number", 10)
        messages.add_message(
            request,
            messages.SUCCESS,
            f"create code:={amount}x{number}",
        )
        models.MoneyCode.batch_create(amount, number)

    batch_add.short_description = "批量添加"
    batch_add.type = "danger"


class DonateAdmin(admin.ModelAdmin):
    list_display = ["user", "money", "time"]
    list_filter = ["time", "money"]


class GoodsAdmin(admin.ModelAdmin):
    list_display = ["name", "transfer", "money", "status_cn", "level"]


class EmailSendLogAdmin(admin.ModelAdmin):
    list_display = ["user", "subject", "created_at"]
    list_filter = ["subject", "created_at"]
    search_fields = ["user", "subject"]
    list_select_related = ["user"]


class RebateRecordAdmin(admin.ModelAdmin):
    list_display = ["user", "consumer_id", "money", "created_at"]
    search_fields = ["user_id", "consumer_id"]


class TicketMessageInline(admin.TabularInline):
    model = models.TicketMessage
    verbose_name = "回复"
    fields = [
        "user",
        "message",
        "created_at",
    ]
    readonly_fields = [
        "created_at",
    ]
    extra = 0
    raw_id_fields = ["user"]


class TicketAdmin(admin.ModelAdmin):
    ALREADY_REPLIED = " | 已回复"

    inlines = [TicketMessageInline]
    list_display = ["user_info", "title", "status_info", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title", "user"]
    readonly_fields = ["user_details"]
    list_per_page = 10

    @admin.display(description="状态")
    def status_info(self, instance):
        res = instance.status_with_message_count
        last_reply = instance.messages.last()
        if not last_reply:
            res += " | 未读"
        elif not last_reply.user.is_staff:
            res += " | 未读"
        return res

    @admin.display(description="用户-等级-余额")
    def user_info(self, instance):
        user = instance.user
        return f"{user.username}-{user.level}-{user.balance}"

    @admin.display(description="用户详细信息")
    def user_details(self, instance):
        user = instance.user
        base_sub_link = user.sub_link
        html = '<table class="table">'
        html += "<thead><tr><th>Client</th><th>Link</th></tr></thead>"
        html += "<tbody>"
        for client in UserSubManager.CLIENT_SET:
            link = f"{base_sub_link}&client={client}"
            html += format_html(f"<tr><td>{client}</td><td>{link}</td>")
        html += "</tbody>"
        html += "</table>"
        return format_html(html)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request).prefetch_related("messages__user", "user")
        return qs

    def save_model(
        self, request: Any, obj: models.Ticket, form: Any, change: Any
    ) -> None:
        if self.ALREADY_REPLIED not in obj.title:
            obj.title += self.ALREADY_REPLIED
        return super().save_model(request, obj, form, change)


# Register your models here.
admin.site.register(models.MoneyCode, MoneyCodeAdmin)
admin.site.register(models.InviteCode, InviteCodeAdmin)


admin.site.register(models.User, UserAdmin)
admin.site.register(models.UserOrder, UserOrderAdmin)
admin.site.register(models.UserCheckInLog, UserCheckInAdmin)
admin.site.register(models.UserRefLog, UserRefLogAdmin)
admin.site.register(models.Donate, DonateAdmin)
admin.site.register(models.Goods, GoodsAdmin)
admin.site.register(models.PurchaseHistory, PurchaseHistoryAdmin)
admin.site.register(models.Announcement)
admin.site.register(models.Ticket, TicketAdmin)
admin.site.register(models.EmailSendLog, EmailSendLogAdmin)
admin.site.register(models.RebateRecord, RebateRecordAdmin)
admin.site.register(models.UserSocialProfile, UserSocialProfileAdmin)


admin.site.unregister(Group)
