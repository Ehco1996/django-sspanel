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


class UserOnLineIpLogAdmin(admin.ModelAdmin):
    list_display = ["user", "user_id", "node_id", "ip", "created_at"]
    search_fields = ["user_id"]
    list_filter = ["user_id", "node_id"]


class UserTrafficLogAdmin(admin.ModelAdmin):

    list_display = ["user", "user_id", "node_id", "total_traffic", "date"]
    search_fields = ["user_id"]
    list_filter = ["date", "node_type", "node_id"]


class UserCheckInAdmin(admin.ModelAdmin):
    list_display = ["user", "user_id", "increased_traffic", "date"]
    search_fields = ["user_id", "date"]
    list_filter = ["date"]


class UserRefLogAdmin(admin.ModelAdmin):
    list_display = ["user", "user_id", "register_count", "date"]
    search_fields = ["user_id", "date"]
    list_filter = ["date"]


class NodeOnlineLogAdmin(admin.ModelAdmin):
    list_display = [
        "node_id",
        "node_type",
        "online_user_count",
        "active_tcp_connections",
        "created_at",
    ]
    list_filter = ["node_id", "node_type"]


class SSNodeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "port",
        "node_id",
        "level",
        "server",
        "enlarge_scale",
        "human_used_traffic",
        "human_total_traffic",
        "enable",
    ]


class VmessNodeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "node_id",
        "level",
        "server",
        "enlarge_scale",
        "human_used_traffic",
        "human_total_traffic",
        "enable",
    ]


class TrojanNodeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "node_id",
        "level",
        "server",
        "enlarge_scale",
        "human_used_traffic",
        "human_total_traffic",
        "enable",
    ]


class RelayNodeAdmin(admin.ModelAdmin):

    list_display = [
        "node_id",
        "name",
        "isp",
        "server",
        "rules_count",
        "enable",
        "api_endpoint",
    ]


class VmessRelayRuleAdmin(admin.ModelAdmin):
    list_display = [
        "vmess_node",
        "relay_node",
        "relay_host",
        "relay_port",
        "remark",
        "enable",
    ]
    ordering = ["vmess_node"]


class TrojanRelayRuleAdmin(admin.ModelAdmin):
    list_display = [
        "trojan_node",
        "relay_node",
        "relay_host",
        "relay_port",
        "remark",
        "enable",
    ]
    ordering = ["trojan_node"]


class SSRelayRuleAdmin(admin.ModelAdmin):
    list_display = [
        "ss_node",
        "relay_node",
        "relay_host",
        "relay_port",
        "remark",
        "enable",
    ]
    ordering = ["ss_node"]


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


# Register your models here.
admin.site.register(models.User, UserAdmin)
admin.site.register(models.UserOrder, UserOrderAdmin)
admin.site.register(models.UserOnLineIpLog, UserOnLineIpLogAdmin)
admin.site.register(models.UserTrafficLog, UserTrafficLogAdmin)
admin.site.register(models.UserCheckInLog, UserCheckInAdmin)
admin.site.register(models.UserRefLog, UserRefLogAdmin)
admin.site.register(models.NodeOnlineLog, NodeOnlineLogAdmin)
admin.site.register(models.SSNode, SSNodeAdmin)
admin.site.register(models.VmessNode, VmessNodeAdmin)
admin.site.register(models.TrojanNode, TrojanNodeAdmin)
admin.site.register(models.RelayNode, RelayNodeAdmin)
admin.site.register(models.VmessRelayRule, VmessRelayRuleAdmin)
admin.site.register(models.TrojanRelayRule, TrojanRelayRuleAdmin)
admin.site.register(models.SSRelayRule, SSRelayRuleAdmin)

admin.site.register(models.InviteCode, InviteCodeAdmin)
admin.site.register(models.Donate, DonateAdmin)
admin.site.register(models.MoneyCode, MoneyCodeAdmin)
admin.site.register(models.Goods, GoodsAdmin)
admin.site.register(models.PurchaseHistory, PurchaseHistoryAdmin)
admin.site.register(models.Announcement)
admin.site.register(models.Ticket, TicketAdmin)
admin.site.register(models.EmailSendLog, EmailSendLogAdmin)
admin.site.register(models.RebateRecord, RebateRecordAdmin)


admin.site.unregister(Group)
