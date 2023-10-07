from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.custom_views import AsyncPasswordResetView

urlpatterns = [
    path(
        "accounts/password_reset/",
        AsyncPasswordResetView.as_view(),
        name="password_reset",
    ),  # NOTE 重写了重置密码的逻辑 一定要在`django.contrib.auth.urls`之前注册，不然会被覆盖
    path("accounts/", include("django.contrib.auth.urls")),
]

# append sspanel template urls
urlpatterns.append(
    path("", include("apps.sspanel.urls", namespace="sspanel")),
)

# append proxy api urls
urlpatterns.append(
    path("api/", include("apps.api.urls", namespace="api")),
)

# append admin urls
urlpatterns.append(
    path("admin/", admin.site.urls, name="admin"),
)

# append prometheus urls
urlpatterns.append(
    path("prom/", include("django_prometheus.urls")),
)


# append openapi urls
urlpatterns.append(
    path("openapi/v1/", include("apps.openapi.urls", namespace="openapi"))
)


# append django debug toolbar urls TODO fix this
# if settings.DEBUG is True:
#     import debug_toolbar

#     urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))

# set admin title
admin.site.site_title = f"{settings.SITE_TITLE}管理"
admin.site.index_title = f"{settings.SITE_TITLE}管理"
admin.site.site_header = f"{settings.SITE_TITLE}管理"
