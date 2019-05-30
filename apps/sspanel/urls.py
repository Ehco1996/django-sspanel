from django.urls import path
from apps.sspanel import views, admin_views


app_name = "sspanel"
urlpatterns = [
    # 网站用户面板
    path("sshelp/", views.sshelp, name="sshelp"),
    path("ssclient/", views.ssclient, name="ssclient"),
    path("invitecode/", views.InviteCodeView.as_view(), name="invite_code"),
    # 注册/登录
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    # 节点
    path("nodeinfo/", views.NodeInfoView.as_view(), name="nodeinfo"),
    path("user_traffic_log/", views.UserTrafficLog.as_view(), name="user_traffic_log"),
    # 用户信息
    path("users/userinfo/", views.UserInfoView.as_view(), name="userinfo"),
    path("users/settings/", views.ss_user_settings, name="ss_user_settings"),
    path(
        "users/ss_node_config/",
        views.UserSSNodeConfigView.as_view(),
        name="ss_node_config",
    ),
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
    path("aff/invite/", views.AffInviteView.as_view(), name="aff_invite"),
    path("aff/status/", views.AffStatusView.as_view(), name="aff_status"),
    # ====================================================================
    # 网站后台界面
    # ====================================================================
    path(
        "backend/user_online_ip_log/",
        admin_views.UserOnlineIpLogView.as_view(),
        name="user_online_ip_log",
    ),
    path("backend/", admin_views.system_status, name="system_status"),
    # 邀请码相关
    path("backend/invite/", admin_views.backend_invite, name="backend_invite"),
    path("invite_gen_code/", admin_views.gen_invite_code, name="geninvitecode"),
    # 节点相关
    path(
        "backend/ss_node_list/",
        admin_views.SSNodeListView.as_view(),
        name="backend_ss_node_list",
    ),
    path("backend/ss_node/", admin_views.SSNodeView.as_view(), name="backend_ss_node"),
    path(
        "backend/ss_node_delete/<int:node_id>/",
        admin_views.SSNodeDeleteView.as_view(),
        name="backend_ss_node_delete",
    ),
    path(
        "backend/ss_node/<int:node_id>/",
        admin_views.SSNodeDetailView.as_view(),
        name="backend_ss_node_detail",
    ),
    # 用户相关
    path("backend/userlist/", admin_views.backend_userlist, name="user_list"),
    path("backend/user/delete/<int:pk>/", admin_views.user_delete, name="user_delete"),
    path("backend/user/search/", admin_views.user_search, name="user_search"),
    path("backend/user/status/", admin_views.user_status, name="user_status"),
    # 商品充值相关
    path("backend/charge/", admin_views.backend_charge, name="backend_charge"),
    path("backend/shop/", admin_views.backend_shop, name="backend_shop"),
    path("backend/shop/delete/<int:pk>/", admin_views.good_delete, name="good_delete"),
    path("backend/good/create/", admin_views.good_create, name="good_create"),
    path("backend/good/edit/<int:pk>/", admin_views.good_edit, name="good_edit"),
    path(
        "backend/purchase/history/",
        admin_views.purchase_history,
        name="purchase_history",
    ),
    # 公告管理相关
    path("backend/anno/", admin_views.backend_anno, name="backend_anno"),
    path("backend/anno/delete/<int:pk>/", admin_views.anno_delete, name="anno_delete"),
    path("backend/anno/create/", admin_views.anno_create, name="anno_create"),
    path("backend/anno/edit/<int:pk>/", admin_views.anno_edit, name="anno_edit"),
    # 工单相关
    path("backend/ticket/", admin_views.backend_ticket, name="backend_ticket"),
    path(
        "backend/ticket/edit/<int:pk>/",
        admin_views.backend_ticketedit,
        name="backend_ticketedit",
    ),
]
