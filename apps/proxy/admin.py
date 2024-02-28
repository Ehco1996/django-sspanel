from django import forms
from django.contrib import admin, messages
from django.db.models import F
from django.utils.safestring import mark_safe

from apps import utils
from apps.proxy import models
from apps.sspanel.models import User
from apps.utils import traffic_format


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


class OccupancyConfigInline(admin.StackedInline):
    model = models.OccupancyConfig
    verbose_name = "占用配置"
    fields = [
        "proxy_node",
        "occupancy_price",
        "occupancy_traffic",
        "occupancy_user_limit",
        "color",
        "status",
        "remark",
    ]

    def get_formset(self, request, obj=None, **kwargs):
        if obj:
            try:
                traffic = traffic_format(obj.occupancy_config.occupancy_traffic)
                help_texts = {
                    "occupancy_traffic": f"={traffic}",
                }
                kwargs.update({"help_texts": help_texts})
            except models.OccupancyConfig.DoesNotExist:
                pass
        return super().get_formset(request, obj, **kwargs)


class ProxyNodeAdmin(admin.ModelAdmin):
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
    inlines = [OccupancyConfigInline]
    all_inlines = [
        TrojanConfigInline,
        SSConfigInline,
        OccupancyConfigInline,
    ]
    list_filter = ["provider_remark", "country"]
    actions = ["clear_traffic_logs", "toggle_enable", "reset_port", "duplicate"]
    list_editable = ["sequence"]
    search_fields = ["name", "provider_remark"]

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            help_texts = {
                "total_traffic": f"={obj.human_total_traffic}",
                "used_traffic": f"={obj.human_used_traffic}",
            }
            kwargs.update({"help_texts": help_texts})
        return super().get_form(request, obj, **kwargs)

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

    def clear_traffic_logs(self, request, queryset):
        for node in queryset:
            query = models.UserTrafficLog.objects.filter(proxy_node=node)
            query.delete()
            count = query._raw_delete(query.db)
            messages.add_message(
                request,
                messages.SUCCESS,
                f"{node}:'s traffic logs cleared count={count}",
            )

    clear_traffic_logs.short_description = "清除流量记录"
    clear_traffic_logs.type = "danger"

    def toggle_enable(self, request, queryset):
        for node in queryset:
            node.enable = not node.enable
            node.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                f"{node}:'s enable is {node.enable}",
            )

    toggle_enable.short_description = "启用/禁用"
    toggle_enable.type = "danger"

    def duplicate(self, request, queryset):
        for node in queryset:
            node.duplicate()
            messages.add_message(
                request,
                messages.SUCCESS,
                f"{node}:'s duplicate success",
            )

    duplicate.short_description = "复制"
    duplicate.type = "warning"


class RelayRuleInline(admin.TabularInline):
    model = models.RelayRule
    verbose_name = "中转规则配置"
    extra = 0
    fields = [
        "name",
        "relay_node",
        "relay_port",
        "proxy_nodes",
        "listen_type",
        "transport_type",
    ]


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
    actions = ["toggle_enable"]

    @admin.display(description="对接地址")
    def api_endpoint(self, instance):
        div = f"""
        <input readonly class="el-input" value="{instance.api_endpoint}">
        """
        return mark_safe(div)

    def toggle_enable(self, request, queryset):
        for node in queryset:
            node.enable = not node.enable
            node.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                f"{node}:'s enable is {node.enable}",
            )

    toggle_enable.short_description = "启用/禁用"
    toggle_enable.type = "danger"


class RelayRuleAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "relay_node",
        "relay_port",
        "listen_type",
        "transport_type",
        "traffic_info",
    ]
    list_filter = ["relay_node"]
    list_per_page = 10
    show_full_result_count = False

    @admin.display(description="流量")
    def traffic_info(self, instance):
        return f"up:{traffic_format(instance.up_traffic) }/down:{traffic_format(instance.down_traffic)}"


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


class OccupancyConfigAdmin(admin.ModelAdmin):
    list_display = [
        "proxy_node",
        "occupancy_price",
        "traffic_info",
        "limit_info",
    ]
    list_filter = ["proxy_node"]
    list_per_page = 10
    show_full_result_count = False

    @admin.display(description="流量")
    def traffic_info(self, instance):
        return f"{traffic_format(instance.occupancy_traffic)}"

    @admin.display(description="已购/总人数")
    def limit_info(self, instance):
        return f"{instance.active_user_count()}/{instance.occupancy_user_limit}"

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            help_texts = {
                "occupancy_traffic": f"={traffic_format(obj.occupancy_traffic)}",
            }
            kwargs.update({"help_texts": help_texts})
        return super().get_form(request, obj, **kwargs)


class UserProxyNodeOccupancyAdmin(admin.ModelAdmin):
    class UserProxyNodeOccupancyForm(forms.ModelForm):
        used_traffic = utils.BytesToGigabytesField(label="已用流量(GB)")
        total_traffic = utils.BytesToGigabytesField(label="总流量(GB)")

        class Meta:
            model = models.UserProxyNodeOccupancy
            fields = "__all__"

    class StatusFilter(admin.SimpleListFilter):
        title = "状态"
        parameter_name = "status"

        def lookups(self, request, model_admin):
            return (
                ("valid", "正常"),
                ("invalid", "失效"),
            )

        def queryset(self, request, queryset):
            value = self.value()
            if value == "valid":
                return queryset.filter(
                    end_time__gt=utils.get_current_datetime()
                ).filter(used_traffic__lt=F("total_traffic"))
            elif value == "invalid":
                return queryset.exclude(
                    end_time__gt=utils.get_current_datetime()
                ).filter(used_traffic__lt=F("total_traffic"))
            return queryset

    form = UserProxyNodeOccupancyForm
    list_display = [
        "proxy_node",
        "user",
        "start_time",
        "end_time",
        "traffic_info",
        "status",
    ]
    search_fields = ["user__username"]
    list_filter = ["proxy_node", "user", StatusFilter]
    list_per_page = 10
    show_full_result_count = False
    autocomplete_fields = ["user", "proxy_node"]

    @admin.display(description="已用/总流量")
    def traffic_info(self, instance):
        return f"{traffic_format(instance.used_traffic)}/{traffic_format(instance.total_traffic)}"

    @admin.display(description="状态")
    def status(self, instance):
        if instance.out_of_usage():
            return "失效"
        else:
            return "正常"

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            help_texts = {
                "total_traffic": f"={traffic_format(obj.total_traffic)}",
                "used_traffic": f"={traffic_format(obj.used_traffic)}",
            }
            kwargs.update({"help_texts": help_texts})
        return super().get_form(request, obj, **kwargs)


# Register your models here.
admin.site.register(models.ProxyNode, ProxyNodeAdmin)
admin.site.register(models.RelayNode, RelayNodeAdmin)
admin.site.register(models.RelayRule, RelayRuleAdmin)

admin.site.register(models.UserTrafficLog, UserTrafficLogAdmin)
admin.site.register(models.UserProxyNodeOccupancy, UserProxyNodeOccupancyAdmin)
admin.site.register(models.OccupancyConfig, OccupancyConfigAdmin)
