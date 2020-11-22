from django.contrib import admin
from django.contrib.auth.models import Group

from . import models


class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "id", "level", "balance", "used_percentage", "sub_link"]
    search_fields = ["username", "email", "id"]
    list_filter = ["level"]


class UserOrderAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "status",
        "out_trade_no",
        "amount",
        "created_at",
        "expired_at",
    ]
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
    list_display = ["name", "transfer", "money", "level"]


class EmailSendLogAdmin(admin.ModelAdmin):
    list_display = ["user", "subject", "created_at"]
    list_filter = ["subject", "created_at"]
    search_fields = ["user__username", "subject"]


class RebateRecordAdmin(admin.ModelAdmin):
    list_display = ["user", "consumer_id", "money", "created_at"]
    search_fields = ["user_id", "consumer_id"]


class TicketAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "status"]
    search_fields = ["title", "user__id"]


class UserSubLogAdmin(admin.ModelAdmin):
    list_display = ["user", "sub_type", "ip", "created_at"]
    list_filter = ["user", "sub_type"]


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
admin.site.register(models.UserSubLog, UserSubLogAdmin)


admin.site.unregister(Group)
