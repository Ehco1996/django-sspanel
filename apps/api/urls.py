from django.urls import path
from . import views

app_name = "api"
urlpatterns = [
    path("system_status/", views.SystemStatusView.as_view(), name="system_status"),
    path("user/settings/", views.UserSettingsView.as_view(), name="user_settings"),
    path("subscribe/", views.SubscribeView.as_view(), name="subscribe"),
    path("reset_ss_port/", views.ReSetSSPortView.as_view(), name="reset_ss_port"),
    path("gen/invitecode/", views.gen_invite_code, name="geninvitecode"),
    path("shop/", views.purchase, name="purchase"),
    path("change/theme/", views.change_theme, name="change_theme"),
    path("change/sub_type/", views.change_sub_type, name="change_sub_type"),
    path("checkin/", views.UserCheckInView.as_view(), name="checkin"),
    # web api 接口
    path(
        "user_ss_config/<int:node_id>/",
        views.UserSSConfigView.as_view(),
        name="user_ss_config",
    ),
    path(
        "user_vmess_config/<int:node_id>/",
        views.UserVmessConfigView.as_view(),
        name="user_vmess_config",
    ),
    path(
        "vmess_server_config/<int:node_id>/",
        views.VmessServerConfigView.as_view(),
        name="vmess_server_config",
    ),
    path(
        "relay_server_config/<int:node_id>/",
        views.RelayServerConfigView.as_view(),
        name="relay_server_config",
    ),
    # 支付
    path("orders", views.OrderView.as_view(), name="order"),
    path("callback/alipay", views.ailpay_callback, name="alipay_callback"),
    # user stats
    path(
        "user/stats/ref_chart", views.UserRefChartView.as_view(), name="user_ref_chart"
    ),
    path(
        "user/stats/traffic_chart",
        views.UserTrafficChartView.as_view(),
        name="user_traffic_chart",
    ),
]
