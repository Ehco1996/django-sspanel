from django.contrib import admin

from apps.openapi.models import UserOpenAPIKey


class UserOpenAPIKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "key"]
    list_filter = ["user"]
    search_fields = ["user__username", "name", "key"]


admin.site.register(UserOpenAPIKey, UserOpenAPIKeyAdmin)
