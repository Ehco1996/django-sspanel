from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.custom_views import AsyncPasswordResetView

urlpatterns = [
    path("", include("apps.sspanel.urls", namespace="sspanel")),
    path("api/", include("apps.api.urls", namespace="api")),
    path(
        "accounts/password_reset/",
        AsyncPasswordResetView.as_view(),
        name="password_reset",
    ),  # NOTE 重写了重置密码的逻辑 一定要在`django.contrib.auth.urls`之前注册，不然会被覆盖
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls, name="admin"),
    path("prom/", include("django_prometheus.urls")),
]

if settings.DEBUG is True:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))

# set admin title
admin.site.site_title = f"{settings.TITLE}管理"
admin.site.index_title = f"{settings.TITLE}管理"
admin.site.site_header = f"{settings.TITLE}管理"
