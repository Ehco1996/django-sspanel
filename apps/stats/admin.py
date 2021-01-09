from django.contrib import admin

from apps import utils
from apps.stats import models


class DailyStatsAdmin(admin.ModelAdmin):

    list_display = [
        "updated_at",
        "new_user_count",
        "active_user_count",
        "checkin_user_count",
        "order_count",
        "order_amount",
        "used_traffic",
    ]

    def used_traffic(self, instance):
        return utils.traffic_format(instance.total_used_traffic)

    used_traffic.short_description = "使用流量"


# Register your models here.
admin.site.register(models.DailyStats, DailyStatsAdmin)
