from django.urls import path
from apps.sspanel import views, admin_views


app_name = "sspanel"
urlpatterns = [
    # 网站用户面板
    path("", views.IndexView.as_view(), name="index"),
    path("help/", views.HelpView.as_view(), name="help"),
    path("client/", views.ClientView.as_view(), name="client"),
    # 邀请
    path("invitecode/", views.InviteCodeView.as_view(), name="invite_code"),
    # 注册/登录
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.UserLogInView.as_view(), name="login"),
    path("logout/", views.UserLogOutView.as_view(), name="logout"),
    # 节点
    path("nodeinfo/", views.NodeInfoView.as_view(), name="nodeinfo"),
    path("user_traffic_log/", views.UserTrafficLog.as_view(), name="user_traffic_log"),
    # 用户信息
    path("users/userinfo/", views.UserInfoView.as_view(), name="userinfo"),
    # 捐赠/充值
    path("donate/", views.DonateView.as_view(), name="donate"),
    path("shop/", views.ShopView.as_view(), name="shop"),
    path("purchaselog/", views.PurchaseLogView.as_view(), name="purchaselog"),
    path("chargecenter/", views.ChargeView.as_view(), name="chargecenter"),
    # 公告
    path("announcement/", views.AnnouncementView.as_view(), name="announcement"),
    # 工单
    path("tickets/", views.TicketsView.as_view(), name="tickets"),
    path("tickets/(<int:pk>)/", views.TicketDetailView.as_view(), name="ticket_detail"),
    path("ticket_create/", views.TicketCreateView.as_view(), name="ticket_create"),
    path(
        "ticket_delete/<int:pk>)/",
        views.TicketDeleteView.as_view(),
        name="ticket_delete",
    ),
    # 推广相关
    path("aff/invite/", views.AffInviteView.as_view(), name="aff_invite"),
    path("aff/status/", views.AffStatusView.as_view(), name="aff_status"),
    # ====================================================================
    # 网站后台界面
    # ====================================================================
    path(
        "my_admin/user_online_ip_log/",
        admin_views.UserOnlineIpLogView.as_view(),
        name="user_online_ip_log",
    ),
    path("my_admin/", admin_views.SystemStatusView.as_view(), name="system_status"),
    # 邀请码相关
    path("my_admin/invite/", admin_views.InviteCodeView.as_view(), name="admin_invite"),
    # 节点相关
    path(
        "my_admin/node_list/",
        admin_views.NodeListView.as_view(),
        name="admin_node_list",
    ),
    path(
        "my_admin/node/<str:node_type>/",
        admin_views.NodeView.as_view(),
        name="admin_node",
    ),
    path(
        "my_admin/node_delete/<str:node_type>/<int:node_id>/",
        admin_views.NodeDeleteView.as_view(),
        name="admin_node_delete",
    ),
    path(
        "my_admin/ss_node/<str:node_type>/<int:node_id>/",
        admin_views.NodeDetailView.as_view(),
        name="admin_node_detail",
    ),
    # 用户相关
    path(
        "my_admin/user_list/",
        admin_views.UserListView.as_view(),
        name="admin_user_list",
    ),
    path(
        "my_admin/user/delete/<int:pk>/",
        admin_views.UserDeleteView.as_view(),
        name="admin_user_delete",
    ),
    path(
        "my_admin/user/search/",
        admin_views.UserSearchView.as_view(),
        name="admin_user_search",
    ),
    path(
        "my_admin/user/<int:pk>/",
        admin_views.UserDetailView.as_view(),
        name="admin_user_detail",
    ),
    path(
        "my_admin/user_status/",
        admin_views.UserStatusView.as_view(),
        name="admin_user_status",
    ),
    # 商品充值相关
    path("my_admin/charge/", admin_views.ChargeView.as_view(), name="admin_charge"),
    path("my_admin/goods/", admin_views.GoodsView.as_view(), name="admin_goods"),
    path(
        "my_admin/goods/<int:pk>/",
        admin_views.GoodDetailView.as_view(),
        name="good_detail",
    ),
    path(
        "my_admin/good_delete/<int:pk>/",
        admin_views.GoodDeleteView.as_view(),
        name="good_delete",
    ),
    path(
        "my_admin/good_create/",
        admin_views.GoodsCreateView.as_view(),
        name="good_create",
    ),
    path(
        "my_admin/purchase/history/",
        admin_views.PurchaseHistoryView.as_view(),
        name="purchase_history",
    ),
    # 公告管理相关
    path(
        "my_admin/announcements/",
        admin_views.AnnouncementsView.as_view(),
        name="admin_announcements",
    ),
    path(
        "my_admin/announcements/<int:pk>/",
        admin_views.AnnouncementDetailView.as_view(),
        name="announcement_detail",
    ),
    path(
        "my_admin/announcement_delete/<int:pk>/",
        admin_views.AnnouncementDeleteView.as_view(),
        name="announcement_delete",
    ),
    path(
        "my_admin/announcement_create/",
        admin_views.AnnouncementCreateView.as_view(),
        name="announcement_create",
    ),
    # 工单相关
    path("my_admin/tickets/", admin_views.TicketsView.as_view(), name="admin_tickets"),
    path(
        "my_admin/tickets/<int:pk>/",
        admin_views.TicketDetailView.as_view(),
        name="admin_ticket_detail",
    ),
]
