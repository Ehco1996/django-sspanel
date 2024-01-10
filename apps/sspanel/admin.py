from django.contrib import admin
from django.contrib.auth.models import Group

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


class MoneyCodeAdmin(admin.ModelAdmin):
    list_display = ["user", "code", "isused"]


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


class TicketAdmin(admin.ModelAdmin):
    inlines = [TicketMessageInline]
    list_display = ["user", "title", "status_with_message_count", "updated_at"]
    search_fields = ["title", "user"]
    readonly_fields = ["updated_at"]


# Register your models here.
admin.site.register(models.User, UserAdmin)
admin.site.register(models.UserOrder, UserOrderAdmin)
admin.site.register(models.UserCheckInLog, UserCheckInAdmin)
admin.site.register(models.UserRefLog, UserRefLogAdmin)
admin.site.register(models.InviteCode, InviteCodeAdmin)
admin.site.register(models.Donate, DonateAdmin)
admin.site.register(models.MoneyCode, MoneyCodeAdmin)
admin.site.register(models.Goods, GoodsAdmin)
admin.site.register(models.PurchaseHistory, PurchaseHistoryAdmin)
admin.site.register(models.Announcement)
admin.site.register(models.Ticket, TicketAdmin)
admin.site.register(models.EmailSendLog, EmailSendLogAdmin)
admin.site.register(models.RebateRecord, RebateRecordAdmin)
admin.site.register(models.UserSocialProfile, UserSocialProfileAdmin)


admin.site.unregister(Group)
