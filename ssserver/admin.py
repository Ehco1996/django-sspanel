from django.contrib import admin
from . import models


class SSUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'traffic', 'fulltraffic', ]

    def fulltraffic(self, obj):
        return '{} GB'.format(obj.transfer_enable / 1024 / 1024 / 1024)

    def traffic(self, obj):
        return '{} MB'.format(obj.get_traffic())
    traffic.short_description = '总流量'

    search_fields = ['user__username']


# Register your models here.
admin.site.register(models.SSUser,SSUserAdmin)