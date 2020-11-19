from django.conf import settings
from django.contrib import admin
from django.forms import ModelForm

from apps.proxy import models


class SSConfigInline(admin.StackedInline):
    model = models.SSConfig
    verbose_name = "SS配置"
    fields = [
        "proxy_node",
        "method",
        "multi_user_port",
    ]


class RelayRuleInline(admin.TabularInline):
    model = models.RelayRule
    verbose_name = "中转规则配置"
    extra = 0
    fields = ["proxy_node", "relay_node", "relay_port", "listen_type", "transport_type"]


class ProxyNodeAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        if "instance" in kwargs and kwargs["instance"]:
            # NOTE trans model traffic to GB
            kwargs["instance"].total_traffic = (
                kwargs["instance"].total_traffic // settings.GB
            )
            kwargs["instance"].used_traffic = (
                kwargs["instance"].used_traffic // settings.GB
            )

        super(ProxyNodeAdminForm, self).__init__(*args, **kwargs)
        self.fields["used_traffic"].help_text = (
            self.fields["used_traffic"].help_text + "单位GB"
        )
        self.fields["total_traffic"].help_text = (
            self.fields["total_traffic"].help_text + "单位GB"
        )

    def clean_used_traffic(self):
        used_traffic = self.cleaned_data.get("used_traffic")
        return used_traffic * settings.GB

    def clean_total_traffic(self):
        total_traffic = self.cleaned_data.get("total_traffic")
        return total_traffic * settings.GB


class ProxyNodeAdmin(admin.ModelAdmin):
    form = ProxyNodeAdminForm

    list_display = [
        "id",
        "name",
        "node_type",
        "country",
        "enable",
        "traffic",
        "sequence",
    ]
    inlines = [RelayRuleInline]
    all_inlines = [SSConfigInline, RelayRuleInline]
    list_editable = ["sequence"]

    def get_inlines(self, request, instance):
        if not instance:
            return self.all_inlines
        elif instance.node_type == models.ProxyNode.NODE_TYPE_SS:
            return [SSConfigInline] + self.inlines
        return self.inlines

    def traffic(self, instance):
        return f"{instance.human_used_traffic}/{instance.human_total_traffic}"

    traffic.short_description = "流量"


class RelayNodeAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "name",
        "server",
        "isp",
        "enable",
        "api_endpoint",
    ]

    def api_endpoint(self, instance):
        return instance.api_endpoint

    api_endpoint.short_description = "中转节点配置地址"


class RelayRuleAdmin(admin.ModelAdmin):
    list_display = [
        "proxy_node",
        "relay_node",
        "relay_host",
        "relay_port",
        "remark",
        "enable",
    ]
    search_fields = []
    list_filter = []
    inlines = []


class SSConfigAdmin(admin.ModelAdmin):

    list_display = [
        "proxy_node",
        "method",
        "multi_user_port",
    ]
    search_fields = []
    list_filter = []


class NodeOnlineLogAdmin(admin.ModelAdmin):
    list_display = [
        "proxy_node",
        "online_user_count",
        "tcp_connections_count",
        "created_at",
    ]
    list_filter = ["proxy_node"]


class UserTrafficLogAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "proxy_node",
        "total_traffic",
        "created_at",
    ]
    list_filter = ["proxy_node", "user"]

    def total_traffic(self, instance):
        return instance.total_traffic

    total_traffic.short_description = "流量"


class UserOnLineIpLogAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "proxy_node",
        "ip",
    ]
    list_filter = ["proxy_node", "user"]


# Register your models here.
admin.site.register(models.ProxyNode, ProxyNodeAdmin)
admin.site.register(models.SSConfig, SSConfigAdmin)

admin.site.register(models.RelayNode, RelayNodeAdmin)
admin.site.register(models.RelayRule, RelayRuleAdmin)

admin.site.register(models.NodeOnlineLog, NodeOnlineLogAdmin)
admin.site.register(models.UserTrafficLog, UserTrafficLogAdmin)
admin.site.register(models.UserOnLineIpLog, UserOnLineIpLogAdmin)
