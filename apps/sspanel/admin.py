from django.contrib import admin
from django.contrib.auth.models import Group

from . import models


class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "id", "level", "balance", "level_expire_time"]
    search_fields = ["username", "email", "id"]
    list_filter = ["level"]


class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ["good", "user", "money", "purchtime"]
    search_fields = ["user"]
    list_filter = ["good", "purchtime"]


class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "time_created", "isused", "code_type"]
    search_fields = ["code"]


class MoneyCodeAdmin(admin.ModelAdmin):
    list_display = ["user", "code", "isused"]


class DonateAdmin(admin.ModelAdmin):
    list_display = ["user", "money", "time"]
    list_filter = ["time", "money"]


class GoodsAdmin(admin.ModelAdmin):
    list_display = ["name", "transfer", "money", "level"]


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
    list_filter = ["user", "amount", "status"]
    ordering = ("-created_at",)


# Register your models here.
admin.site.register(models.User, UserAdmin)
admin.site.register(models.InviteCode, InviteCodeAdmin)
admin.site.register(models.Donate, DonateAdmin)
admin.site.register(models.MoneyCode, MoneyCodeAdmin)
admin.site.register(models.Goods, GoodsAdmin)
admin.site.register(models.PurchaseHistory, PurchaseHistoryAdmin)
admin.site.register(models.Announcement)
admin.site.register(models.Ticket)
admin.site.register(models.UserOrder, UserOrderAdmin)

admin.site.unregister(Group)
