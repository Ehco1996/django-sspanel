from rest_framework import routers

from apps.openapi import views

app_name = "openapi"

router = routers.DefaultRouter()
router.register(r"proxy_nodes", views.ProxyNodeViewSet, basename="proxy_nodes")
router.register(r"users", views.UserViewSet, basename="users")
