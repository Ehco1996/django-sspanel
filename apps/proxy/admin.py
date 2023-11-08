from django.conf import settings
from django.contrib import admin, messages
from django.forms import ModelForm
from django.utils.safestring import mark_safe

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


class TrojanConfigInline(admin.StackedInline):
    model = models.TrojanConfig
    verbose_name = "Trojan配置"
    fields = ["proxy_node", "multi_user_port", "fallback_addr"]


class RelayRuleInline(admin.TabularInline):
    model = models.RelayRule
    verbose_name = "中转规则配置"
    extra = 0
    fields = [
        "rule_name",
        "proxy_node",
        "relay_node",
        "relay_port",
        "listen_type",
        "transport_type",
    ]


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
        "__str__",
        "link_addr",
        "country",
        "enable",
        "traffic",
        "human_used_current_traffic_rate",
        "mix_info",
        "provider_remark",
        "sequence",
        "api_endpoint",
    ]
    inlines = [RelayRuleInline]
    all_inlines = [TrojanConfigInline, SSConfigInline, RelayRuleInline]
    list_editable = ["sequence"]
    list_filter = ["node_type", "country", "provider_remark"]
    actions = ["reset_port"]

    def get_inlines(self, request, instance):
        if not instance:
            return self.all_inlines
        elif instance.node_type == models.ProxyNode.NODE_TYPE_SS:
            return [SSConfigInline] + self.inlines
        elif instance.node_type == models.ProxyNode.NODE_TYPE_TROJAN:
            return [TrojanConfigInline] + self.inlines
        return self.inlines

    @admin.display(description="等级/中转数量/在线")
    def mix_info(self, instance):
        online = instance.online_info["online_user_count"]
        return f"{instance.level}/{instance.relay_count}/{online}"

    @admin.display(description="流量", ordering="used_traffic")
    def traffic(self, instance):
        return f"{instance.human_used_traffic}/{instance.human_total_traffic}"

    @admin.display(description="连接地址")
    def link_addr(self, instance):
        return f"{instance.server}:{instance.get_user_port()}"

    @admin.display(description="对接地址")
    def api_endpoint(self, instance):
        div = f"""
        <input readonly class="el-input" value="{instance.api_endpoint}">
        """
        return mark_safe(div)

    @admin.display(description="带宽")
    def human_used_current_traffic_rate(self, instance):
        return instance.human_used_current_traffic_rate

    def reset_port(self, request, queryset):
        for node in queryset:
            new_port = node.reset_random_multi_user_port()
            messages.add_message(
                request, messages.SUCCESS, f"{node}:'s new port is :{new_port}"
            )

    reset_port.short_description = "重置端口"
    reset_port.type = "warning"


class RelayNodeAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "server",
        "isp",
        "enable",
        "remark",
        "api_endpoint",
    ]

    inlines = [RelayRuleInline]
    list_filter = [
        "isp",
        "remark",
    ]

    @admin.display(description="对接地址")
    def api_endpoint(self, instance):
        div = f"""
        <input readonly class="el-input" value="{instance.api_endpoint}">
        """
        return mark_safe(div)


class UserTrafficLogAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "nodename",
        "total_traffic",
        "ip_list",
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


# Register your models here.
admin.site.register(models.ProxyNode, ProxyNodeAdmin)
admin.site.register(models.RelayNode, RelayNodeAdmin)
admin.site.register(models.UserTrafficLog, UserTrafficLogAdmin)
