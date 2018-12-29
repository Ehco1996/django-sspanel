from django.urls import path
from . import views

app_name = "api"
urlpatterns = [
    path("user/data/", views.userData, name="userdata"),
    path("node/data/", views.nodeData, name="nodedata"),
    path("donate/data/", views.donateData, name="donatedata"),
    path("random/port/", views.change_ss_port, name="changessport"),
    path("gen/invitecode/", views.gen_invite_code, name="geninvitecode"),
    path("shop/", views.purchase, name="purchase"),
    path("pay/request/", views.pay_request, name="pay_request"),
    path("pay/query/", views.pay_query, name="pay_query"),
    path("traffic/query/", views.traffic_query, name="traffic_query"),
    path("change/theme/", views.change_theme, name="change_theme"),
    path("checkin/", views.checkin, name="checkin"),
    # 邀请码接口
    path("get/invitecode/", views.get_invitecode, name="get_invitecode"),
    # web api 接口
    path("nodes/<int:node_id>", views.node_api, name="get_node_info"),
    path("nodes/online", views.node_online_api, name="post_onlineip"),
    path("users/nodes/<int:node_id>", views.user_api, name="get_userinfo"),
    path("traffic/upload", views.traffic_api, name="post_traffic"),
    path("nodes/aliveip", views.alive_ip_api, name="post_aliveip"),
]
