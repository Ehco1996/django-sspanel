from django.urls import path
from . import views


app_name = "sspanel"
urlpatterns = [
    # 网站用户面板
    path("sshelp/", views.sshelp, name="sshelp"),
    path("ssclient/", views.ssclient, name="ssclient"),
    path("ssinvite/", views.ssinvite, name="ssinvite"),
    path("passinvite/(<invitecode>)/", views.pass_invitecode, name="passinvitecode"),
    # 注册/登录
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    # 节点
    path("nodeinfo/", views.nodeinfo, name="nodeinfo"),
    path("trafficlog/", views.trafficlog, name="trafficlog"),
    # 用户信息
    path("users/userinfo/", views.userinfo, name="userinfo"),
    path("users/userinfoedit/", views.userinfo_edit, name="userinfo_edit"),
    # 捐赠/充值
    path("donate/", views.donate, name="donate"),
    path("shop/", views.shop, name="shop"),
    path("purchaselog/", views.purchaselog, name="purchaselog"),
    path("chargecenter/", views.chargecenter, name="chargecenter"),
    path("charge/", views.charge, name="charge"),
    # 公告
    path("announcement/", views.announcement, name="announcement"),
    # 工单
    path("ticket/", views.ticket, name="ticket"),
    path("ticket/create/", views.ticket_create, name="ticket_create"),
    path("ticket/edit/(<int:pk>)/", views.ticket_edit, name="ticket_edit"),
    path("ticket/delete/<int:pk>)/", views.ticket_delete, name="ticket_delete"),
    # 推广相关
    path("affiliate/", views.affiliate, name="affiliate"),
    path("rebate/record/", views.rebate_record, name="rebate"),
    # 网站后台面板
    path("backend/", views.system_status, name="system_status"),
    # 邀请码相关
    path("backend/invite/", views.backend_invite, name="backend_invite"),
    path("invite_gen_code/", views.gen_invite_code, name="geninvitecode"),
    # 节点相关
    path("backend/nodeinfo/", views.backend_node_info, name="backend_node_info"),
    path("backend/node/delete/<int:node_id>/", views.node_delete, name="node_delete"),
    path("backend/node/edit/<int:node_id>/", views.node_edit, name="node_edit"),
    path("backend/node/create/", views.node_create, name="node_create"),
    # 用户相关
    path("backend/userlist/", views.backend_userlist, name="user_list"),
    path("backend/user/delete/<int:pk>/", views.user_delete, name="user_delete"),
    path("backend/user/search/", views.user_search, name="user_search"),
    path("backend/user/status/", views.user_status, name="user_status"),
    # 商品充值相关
    path("backend/charge/", views.backend_charge, name="backend_charge"),
    path("backend/shop/", views.backend_shop, name="backend_shop"),
    path("backend/shop/delete/<int:pk>/", views.good_delete, name="good_delete"),
    path("backend/good/create/", views.good_create, name="good_create"),
    path("backend/good/edit/<int:pk>/", views.good_edit, name="good_edit"),
    path("backend/purchase/history/", views.purchase_history, name="purchase_history"),
    # 公告管理相关
    path("backend/anno/", views.backend_anno, name="backend_anno"),
    path("backend/anno/delete/<int:pk>/", views.anno_delete, name="anno_delete"),
    path("backend/anno/create/", views.anno_create, name="anno_create"),
    path("backend/anno/edit/<int:pk>/", views.anno_edit, name="anno_edit"),
    # 工单相关
    path("backend/ticket/", views.backend_ticket, name="backend_ticket"),
    path(
        "backend/ticket/edit/<int:pk>/",
        views.backend_ticketedit,
        name="backend_ticketedit",
    ),
    # 在线ip
    path("backend/aliveuser/", views.backend_alive_user, name="alive_user"),
]
