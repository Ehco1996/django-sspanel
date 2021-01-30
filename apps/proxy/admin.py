from django.conf import settings
from django.contrib import admin
from django.forms import ModelForm

from apps.proxy import models
from apps.sspanel.models import User


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
    list_filter = ["proxy_node", "relay_node"]
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
    list_select_related = ["proxy_node"]


class UserTrafficLogAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "nodename",
        "total_traffic",
        "created_at",
    ]
    search_fields = ["user__username"]
    list_filter = ["proxy_node", "created_at"]
    list_per_page = 10
    show_full_result_count = False

    def username(self, instance):
        return User.get_by_id_with_cache(instance.user_id).username

    def nodename(self, instance):
        return models.ProxyNode.get_by_id_with_cache(instance.proxy_node_id).name

    def total_traffic(self, instance):
        return instance.total_traffic

    username.short_description = "用户名"
    nodename.short_description = "节点名"
    total_traffic.short_description = "流量"


class UserOnLineIpLogAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "proxy_node",
        "ip",
    ]
    search_fields = ["ip"]
    list_filter = ["user", "proxy_node"]
    list_per_page = 10
    show_full_result_count = False


# Register your models here.
admin.site.register(models.ProxyNode, ProxyNodeAdmin)
admin.site.register(models.SSConfig, SSConfigAdmin)

admin.site.register(models.RelayNode, RelayNodeAdmin)
admin.site.register(models.RelayRule, RelayRuleAdmin)

admin.site.register(models.NodeOnlineLog, NodeOnlineLogAdmin)
admin.site.register(models.UserTrafficLog, UserTrafficLogAdmin)
admin.site.register(models.UserOnLineIpLog, UserOnLineIpLogAdmin)
