from django.urls import path
from . import views

app_name = "api"
urlpatterns = [
    path("system_status/", views.SystemStatusView.as_view(), name="system_status"),
    path(
        "ss_user/settings/", views.SSUserSettingsView.as_view(), name="ss_user_settings"
    ),
    path("subscribe/", views.SubscribeView.as_view(), name="subscribe"),
    path("random/port/", views.change_ss_port, name="changessport"),
    path("gen/invitecode/", views.gen_invite_code, name="geninvitecode"),
    path("shop/", views.purchase, name="purchase"),
    path("traffic/query/", views.traffic_query, name="traffic_query"),
    path("change/theme/", views.change_theme, name="change_theme"),
    path("change/sub_type/", views.change_sub_type, name="change_sub_type"),
    path("checkin/", views.checkin, name="checkin"),
    # 邀请码接口
    path("get/invitecode/", views.get_invitecode, name="get_invitecode"),
    # web api 接口
    path("nodes/<int:node_id>", views.node_api, name="get_node_info"),
    path("nodes/online", views.node_online_api, name="post_onlineip"),
    path(
        "users/nodes/<int:node_id>", views.node_user_configs, name="node_user_configs"
    ),
    path("traffic/upload", views.traffic_api, name="post_traffic"),
    path("nodes/aliveip", views.alive_ip_api, name="post_aliveip"),
    # 支付
    path("orders", views.OrderView.as_view(), name="order"),
    path("callback/alipay", views.ailpay_callback, name="alipay_callback"),
]
