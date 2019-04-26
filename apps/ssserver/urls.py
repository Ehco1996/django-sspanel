from django.urls import path
from . import views


app_name = "ssserver"
urlpatterns = [
    path("user/edit/<int:user_id>/", views.user_edit, name="user_edit"),
    path("node/config/", views.node_config, name="node_config"),
]
