from django.contrib import admin

from apps.stats import models


class DailyStatsAdmin(admin.ModelAdmin):

    list_display = [
        "date",
        "new_user_count",
        "active_user_count",
        "checkin_user_count",
        "order_count",
        "order_amount",
        "total_used_traffic",
    ]
    list_per_page = 31
    list_filter = ["date"]


# Register your models here.
admin.site.register(models.DailyStats, DailyStatsAdmin)
