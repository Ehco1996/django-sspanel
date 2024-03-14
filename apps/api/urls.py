from django.urls import path

from . import views

app_name = "api"
urlpatterns = [
    path("system_status/", views.SystemStatusView.as_view(), name="system_status"),
    path("user/settings/", views.UserSettingsView.as_view(), name="user_settings"),
    path("subscribe/", views.SubscribeView.as_view(), name="subscribe"),
    path(
        "subscribe/clash/proxy_providers/",
        views.ClashProxyProviderView.as_view(),
        name="proxy_providers",
    ),
    path(
        "subscribe/clash/direct_domain_rule_set/",
        views.ClashDirectDomainRuleSetView.as_view(),
        name="direct_domain_rule_set",
    ),
    path(
        "subscribe/clash/direct_ip_rule_set/",
        views.ClashDirectIPRuleSetView.as_view(),
        name="direct_domain_rule_set",
    ),
    path("shop/", views.purchase, name="purchase"),
    path("change/theme/", views.change_theme, name="change_theme"),
    path("checkin/", views.UserCheckInView.as_view(), name="checkin"),
    path("rest_sub_uid/", views.reset_sub_uid, name="rest_sub_uid"),
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
