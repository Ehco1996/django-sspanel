from django.urls import path

from apps.sspanel import admin_views, views

app_name = "sspanel"
urlpatterns = [
    # 网站用户面板
    path("", views.IndexView.as_view(), name="index"),
    path("help/", views.HelpView.as_view(), name="help"),
    # 邀请
    path("invitecode/", views.InviteCodeView.as_view(), name="invite_code"),
    # 注册/登录
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.UserLogInView.as_view(), name="login"),
    path("login/telegram/", views.TelegramLoginView.as_view(), name="telegram_login"),
    path("logout/", views.UserLogOutView.as_view(), name="logout"),
    path(
        "user_traffic_log/", views.UserTrafficLogView.as_view(), name="user_traffic_log"
    ),
    # 用户信息
    path("users/userinfo/", views.UserInfoView.as_view(), name="userinfo"),
    # 捐赠/充值
    path("shop/", views.ShopView.as_view(), name="shop"),
    path("chargecenter/", views.ChargeView.as_view(), name="chargecenter"),
    # 独享节点
    path(
        "node_occupancy/", views.ProxyNodeOccupancyView.as_view(), name="node_occupancy"
    ),
    # 公告
    path("announcement/", views.AnnouncementView.as_view(), name="announcement"),
    # 工单
    path("tickets/", views.TicketListView.as_view(), name="ticket_list"),
    path("tickets/<int:pk>/", views.TicketDetailView.as_view(), name="ticket_detail"),
    path("ticket_create/", views.TicketCreateView.as_view(), name="ticket_create"),
    path(
        "ticket_delete/<int:pk>/",
        views.TicketDeleteView.as_view(),
        name="ticket_delete",
    ),
    # 推广相关
    path("aff/invite/", views.AffInviteView.as_view(), name="aff_invite"),
    # ====================================================================
    # 网站后台界面
    # ====================================================================
    path("my_admin/", admin_views.SystemStatusView.as_view(), name="system_status"),
    # 邀请码相关
    path("my_admin/invite/", admin_views.InviteCodeView.as_view(), name="admin_invite"),
    # 用户相关
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
]
