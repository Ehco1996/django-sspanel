from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # path("", index, name="index"),
    path("", include("apps.sspanel.urls", namespace="sspanel")),
    path("api/", include("apps.api.urls", namespace="api")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls, name="admin"),
    # deprecated
    path("prom/", include("django_prometheus.urls")),
]
