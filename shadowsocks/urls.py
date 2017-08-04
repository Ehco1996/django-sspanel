from django.conf.urls import url
from .import views


app_name = "shadowsocks"
urlpatterns = [

    # 网站用户面板
    url(r'^$', views.index, name='index'),
    url(r'^nodeinfo/$', views.nodeinfo, name='nodeinfo'),
    url(r'^sshelp/$', views.sshelp, name='sshelp'),
    url(r'^ssclient/$', views.ssclient, name='ssclient'),
    url(r'^ssinvite/$', views.ssinvite, name='ssinvite'),
    # 前期调试使用，后期会加入权限
    url(r'^ssinvite_gen_code/(?P<Num>[0-9]{1,2})/$',
        views.gen_invite_code, name='geninvitecode'),
    url(r'^passinvite/(?P<invitecode>[\S]+)/$',
        views.pass_invitecode, name='passinvitecode'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.Login_view, name='login'),
    url(r'^logout/$', views.Logout_view, name='logout'),
    url(r'^users/userinfo/$', views.userinfo, name='userinfo'),
    url(r'^users/userinfo_edit/$', views.userinfo_edit, name='userinfo_edit'),
    url(r'^checkin/$', views.checkin, name='checkin'),
    url(r'qrcode/(?P<node_id>[0-9]+)$', views.get_ss_qrcode, name='qrcode'),
    url(r'^donate/$', views.donate, name='donate'),
    url(r'^shop/$', views.shop, name='shop'),
    url(r'purchase/(?P<goods_id>[0-9]+)$', views.purchase, name='purchase'),
    url(r'^chargecenter/$', views.chargecenter, name='chargecenter'),
    url(r'^charge/$', views.charge, name='charge'),

    # 网站后台面板
    url(r'^backend/$',views.backend_index,name='backend_index'),
    url(r'^backend/nodeinfo$',views.backend_node_info,name='backend_node_info'),
    url(r'^backend/node/delete/(?P<node_id>[0-9]+)$', views.node_delete, name='node_delete'),
    url(r'^backend/node/edit/(?P<node_id>[0-9]+)$', views.node_edit, name='node_edit'),
    url(r'^backend/nodecreate/$',views.node_create,name='node_create'),
    url(r'^backend/aliveuser/$',views.backend_alive_user,name='alive_user'),
    
    
    
    
    
    
    
]
