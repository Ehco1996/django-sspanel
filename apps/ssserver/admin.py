from django.contrib import admin
from . import models


class SSUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'port', 'traffic', 'fulltraffic', ]

    def fulltraffic(self, obj):
        return obj.get_transfer()
    fulltraffic.short_description = '总流量'

    def traffic(self, obj):
        return obj.get_traffic()
    traffic.short_description = '使用流量'

    search_fields = ['user__username', 'user__email', 'port', 'user__pk']
    list_filter = ['level', 'enable', ]


class SUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'port', ]
    search_fields = ['user__username', 'user__email', 'port', 'user_id']
    list_filter = ['enable', ]


class TrafficLogAdmin(admin.ModelAdmin):
    search_fields = ['user_id', 'node_id']
    list_display = ['user_id', 'node_id', 'traffic', 'log_date', ]


class NodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'node_id', 'level', 'traffic_rate', 'order',
                    'human_used_traffic', 'human_total_traffic', 'show']


class NodeOnlineAdmin(admin.ModelAdmin):
    list_display = ['node_id', 'online_user']


class NodeInfoAdmin(admin.ModelAdmin):
    list_display = ['node_id', 'load']


class AliveIpAdmin(admin.ModelAdmin):
    list_display = ['node_id', 'user', 'ip', 'log_time']
    list_filter = ['node_id', 'log_time']


# Register your models here.
admin.site.register(models.SSUser, SSUserAdmin)
admin.site.register(models.Suser, SUserAdmin)
admin.site.register(models.TrafficLog, TrafficLogAdmin)
admin.site.register(models.Node, NodeAdmin)
admin.site.register(models.NodeOnlineLog, NodeOnlineAdmin)
admin.site.register(models.NodeInfoLog, NodeInfoAdmin)
admin.site.register(models.AliveIp, AliveIpAdmin)
