from django.contrib import admin

from apps.proxy import models


class ProxyNodeAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "name",
        "node_type",
        "country",
        "enable",
        "sequence",
    ]
    search_fields = []
    list_filter = []


class SSConfigAdmin(admin.ModelAdmin):

    list_display = [
        "node",
        "method",
        "multi_user_port",
    ]
    search_fields = []
    list_filter = []


# Register your models here.
admin.site.register(models.ProxyNode, ProxyNodeAdmin)
admin.site.register(models.SSConfig, SSConfigAdmin)
