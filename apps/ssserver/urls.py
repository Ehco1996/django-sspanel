from django.urls import path
from . import views


app_name = "ssserver"
urlpatterns = [
    path("user/edit/<int:user_id>/", views.user_edit, name="user_edit"),
    path("changesspass/", views.change_ss_pass, name="changesspass"),
    path("changessmethod/", views.change_ss_method, name="changessmethod"),
    path("changessprotocol/", views.change_ss_protocol, name="changessprotocol"),
    path("changessobfs/", views.change_ss_obfs, name="changessobfs"),
    path("subscribe/", views.subscribe, name="subscribe"),
    path("node/config/", views.node_config, name="node_config"),
]
