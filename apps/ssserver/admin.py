from django.contrib import admin
from . import models


class SUserAdmin(admin.ModelAdmin):
    list_display = ["user", "user_id", "port", "used_traffic", "total_transfer"]
    search_fields = ["user_id", "port"]
    list_filter = ["enable"]


class NodeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "node_id",
        "level",
        "traffic_rate",
        "order",
        "human_used_traffic",
        "human_total_traffic",
        "show",
    ]


# Register your models here.
admin.site.register(models.Node, NodeAdmin)
admin.site.register(models.Suser, SUserAdmin)
