from django.contrib import admin
from django.contrib.auth.models import Group

from . import models


class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "id", "level", "balance", "level_expire_time"]
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
    list_filter = ["user", "amount", "status", "created_at"]
    ordering = ("-created_at",)


class UserOnLineIpLogAdmin(admin.ModelAdmin):
    list_display = ["user", "user_id", "node_id", "ip", "created_at"]

    search_fields = ["user_id"]


class UserTrafficLogAdmin(admin.ModelAdmin):

    list_display = ["user", "user_id", "node_id", "total_traffic", "date"]
    search_fields = ["user_id", "node_id"]
    list_filter = ["date"]


class UserSSConfigAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "user_id",
        "port",
        "password",
        "method",
        "speed_limit",
        "human_used_traffic",
        "human_total_traffic",
        "enable",
    ]
    search_fields = ["user_id", "port"]
    list_filter = ["enable"]


class UserCheckInAdmin(admin.ModelAdmin):
    list_display = ["user", "user_id", "increased_traffic", "date"]
    search_fields = ["user_id", "date"]
    list_filter = ["date"]


class UserTrafficAdmin(admin.ModelAdmin):
    list_display = ["user", "user_id", "used_traffic", "used_percentage", "overflow"]
    search_fields = ["user_id", "date"]


class SSNodeOnlineLogAdmin(admin.ModelAdmin):
    list_display = ["node_id", "online_user_count", "created_at"]


class SSNodeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "node_id",
        "level",
        "server",
        "human_used_traffic",
        "human_total_traffic",
        "enable",
    ]


class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ["good", "user", "money", "purchtime"]
    search_fields = ["user"]
    list_filter = ["good", "purchtime"]


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


# Register your models here.
admin.site.register(models.User, UserAdmin)
admin.site.register(models.UserOrder, UserOrderAdmin)
admin.site.register(models.UserOnLineIpLog, UserOnLineIpLogAdmin)
admin.site.register(models.UserTrafficLog, UserTrafficLogAdmin)
admin.site.register(models.UserSSConfig, UserSSConfigAdmin)
admin.site.register(models.UserCheckInLog, UserCheckInAdmin)
admin.site.register(models.UserTraffic, UserTrafficAdmin)
admin.site.register(models.SSNodeOnlineLog, SSNodeOnlineLogAdmin)
admin.site.register(models.SSNode, SSNodeAdmin)

admin.site.register(models.InviteCode, InviteCodeAdmin)
admin.site.register(models.Donate, DonateAdmin)
admin.site.register(models.MoneyCode, MoneyCodeAdmin)
admin.site.register(models.Goods, GoodsAdmin)
admin.site.register(models.PurchaseHistory, PurchaseHistoryAdmin)
admin.site.register(models.Announcement)
admin.site.register(models.Ticket)


admin.site.unregister(Group)
