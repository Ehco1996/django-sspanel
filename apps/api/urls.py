from django.urls import path, re_path
from . import views

app_name = "api"
urlpatterns = [
    path('user/data/', views.userData, name='userdata'),
    path('node/data/', views.nodeData, name='nodedata'),
    path('donate/data/', views.donateData, name='donatedata'),
    path('random/port/', views.change_ss_port, name='changessport'),
    path('gen/invitecode/', views.gen_invite_code, name='geninvitecode'),
    path('shop/', views.purchase, name='purchase'),
    path('pay/request/', views.pay_request, name='pay_request'),
    path('pay/query/', views.pay_query, name='pay_query'),
    path('traffic/query/', views.traffic_query, name='traffic_query'),
    path('change/theme/', views.change_theme, name='change_theme'),

    # 邀请码接口
    path('get/invitecode/', views.get_invitecode),
    # web api 接口
    path('nodes/<int:node_id>', views.node_api),
    path('nodes/online', views.node_online_api),
    path('users/nodes/<int:node_id>', views.user_api),
    path('traffic/upload', views.traffic_api),
    path('nodes/aliveip', views.alive_ip_api),
]
