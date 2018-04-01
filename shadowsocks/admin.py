from django.contrib import admin
from . import models


class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'level', 'balance', ]
    search_fields = ['username', 'email', 'pk']
    list_filter = ['level', ]


class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ['info', 'user', 'money', 'purchtime', ]
    search_fields = ['user', ]
    list_filter = ['info', 'purchtime']


class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'time_created', 'isused', 'type']
    search_fields = ['code']


class MoneyCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'isused']


class AlipayAdmin(admin.ModelAdmin):
    list_display = ['username', 'info_code', 'amount', 'money_code', 'time', ]
    search_fields = ['info_code', ]
    list_filter = ['time', 'amount', ]


class AlipayRequestAdmin(admin.ModelAdmin):
    list_display = ['username', 'amount', 'info_code', 'time', ]
    search_fields = ['info_code', ]
    list_filter = ['time', 'amount', ]


class DonateAdmin(admin.ModelAdmin):
    list_display = ['user', 'money', 'time', ]
    list_filter = ['time', 'money', ]


class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'transfer', 'money', 'level', ]


# Register your models here.
admin.site.register(models.User, UserAdmin)
admin.site.register(models.InviteCode, InviteCodeAdmin)
admin.site.register(models.Donate, DonateAdmin)
admin.site.register(models.MoneyCode, MoneyCodeAdmin)
admin.site.register(models.Shop, ShopAdmin)
admin.site.register(models.PurchaseHistory, PurchaseHistoryAdmin)
admin.site.register(models.PayRecord, AlipayAdmin)
admin.site.register(models.PayRequest, AlipayRequestAdmin)
admin.site.register(models.Announcement)
admin.site.register(models.Ticket)
