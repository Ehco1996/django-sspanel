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
    path("checkin/", views.UserCheckInView.as_view(), name="checkin"),
    # web api 接口
    path(
        "proxy_configs/<int:node_id>/",
        views.ProxyConfigsView.as_view(),
        name="proxy_configs",
    ),
    path(
        "ehco_relay_config/<int:node_id>/",
        views.EhcoRelayConfigView.as_view(),
        name="ehco_relay_config",
    ),
    path(
        "ehco_server_config/<int:node_id>/",
        views.EhcoServerConfigView.as_view(),
        name="ehco_server_config",
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
