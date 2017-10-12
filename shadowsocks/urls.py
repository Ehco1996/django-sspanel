from django.conf.urls import url
from .import views


app_name = "shadowsocks"
urlpatterns = [

    # 网站用户面板
    url(r'^$', views.index, name='index'),
    url(r'^nodeinfo/$', views.nodeinfo, name='nodeinfo'),
    url(r'^trafficlog/$', views.trafficlog, name='trafficlog'),
    url(r'^sshelp/$', views.sshelp, name='sshelp'),
    url(r'^ssclient/$', views.ssclient, name='ssclient'),
    url(r'^ssinvite/$', views.ssinvite, name='ssinvite'),
    url(r'^passinvite/(?P<invitecode>[\S]+)/$',
        views.pass_invitecode, name='passinvitecode'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.Login_view, name='login'),
    url(r'^logout/$', views.Logout_view, name='logout'),
    url(r'^users/userinfo/$', views.userinfo, name='userinfo'),
    url(r'^users/userinfoedit/$', views.userinfo_edit, name='userinfo_edit'),
    url(r'^checkin/$', views.checkin, name='checkin'),
    url(r'qrcode/ssr/(?P<node_id>[0-9]+)$',
        views.get_ssr_qrcode, name='ssrqrcode'),
    url(r'qrcode/ss/(?P<node_id>[0-9]+)$',
        views.get_ss_qrcode, name='ssqrcode'),

    url(r'^donate/$', views.donate, name='donate'),
    url(r'^shop/$', views.shop, name='shop'),
    url(r'^purchaselog/$', views.purchaselog, name='purchaselog'),
    url(r'purchase/(?P<goods_id>[0-9]+)$', views.purchase, name='purchase'),
    url(r'^chargecenter/$', views.chargecenter, name='chargecenter'),
    url(r'^charge/$', views.charge, name='charge'),
    url(r'^announcement/$', views.announcement, name='announcement'),
    url(r'^ticket/$', views.ticket, name='ticket'),
    url(r'^ticket/create/$', views.ticket_create, name='ticket_create'),
    url(r'^ticket/edit/(?P<pk>[0-9]+)$',
        views.ticket_edit, name='ticket_edit'),
    url(r'^ticket/delete/(?P<pk>[0-9]+)$',
        views.ticket_delete, name='ticket_delete'),



    # 网站后台面板
    url(r'^backend/$', views.backend_index, name='backend_index'),
    # 邀请码相关
    url(r'^backend/invite/$', views.backend_invite, name='backend_invite'),
    url(r'^invite_gen_code/$', views.gen_invite_code, name='geninvitecode'),
    # 节点相关
    url(r'^backend/nodeinfo$', views.backend_node_info, name='backend_node_info'),
    url(r'^backend/node/delete/(?P<node_id>[0-9]+)$',
        views.node_delete, name='node_delete'),
    url(r'^backend/node/edit/(?P<node_id>[0-9]+)$',
        views.node_edit, name='node_edit'),
    url(r'^backend/node/create/$', views.node_create, name='node_create'),
    # 用户相关
    url(r'^backend/aliveuser/$', views.backend_Aliveuser, name='alive_user'),
    url(r'^backend/userlist/$', views.backend_UserList, name='user_list'),
    url(r'^backend/user/delete/(?P<pk>[0-9]+)$',
        views.user_delete, name='user_delete'),
    url(r'^backend/user/search/$', views.user_search, name='user_search'),
    # 商品充值相关
    url(r'^backend/charge/$', views.backend_charge, name='backend_charge'),
    url(r'^backend/shop$', views.backend_shop, name='backend_shop'),
    url(r'^backend/shop/delete/(?P<pk>[0-9]+)$',
        views.good_delete, name='good_delete'),
    url(r'^backend/good/create/$', views.good_create, name='good_create'),
    url(r'^backend/good/edit/(?P<pk>[0-9]+)$',
        views.good_edit, name='good_edit'),
    url(r'^backend/purchase/history/$',
        views.purchase_history, name='purchase_history'),

    # 支付宝当面付相关:
    url(r'facepay/qrcode/$', views.gen_face_pay_qrcode, name='facepay_qrcode'),
    # 购买处理逻辑
    url(r'facepay/(?P<out_trade_no>[0-9]+)',
        views.Face_pay_view, name='facepay_view'),
    # 公告管理相关
    url(r'^backend/anno/$', views.backend_anno, name='backend_anno'),
    url(r'^backend/anno/delete/(?P<pk>[0-9]+)$',
        views.anno_delete, name='anno_delete'),
    url(r'^backend/anno/create/$', views.anno_create, name='anno_create'),
    url(r'^backend/anno/edit/(?P<pk>[0-9]+)$',
        views.anno_edit, name='anno_edit'),
    url(r'^backend/ticket/$', views.backend_ticket, name='backend_ticket'),
    url(r'^backend/ticket/edit/(?P<pk>[0-9]+)$',
        views.backend_ticketedit, name='backend_ticketedit'),




]
