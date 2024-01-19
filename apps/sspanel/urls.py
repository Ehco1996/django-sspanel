from django.urls import path

from apps.sspanel import views

app_name = "sspanel"

urlpatterns = [
    # 网站用户面板
    path("", views.UserLogInView.as_view(), name="index"),
    path("help/", views.HelpView.as_view(), name="help"),
    # 邀请
    path("invitecode/", views.InviteCodeView.as_view(), name="invite_code"),
    # 注册/登录
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.UserLogInView.as_view(), name="login"),
    path(
        "login-with-telegram/", views.TelegramLoginView.as_view(), name="telegram_login"
    ),
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
]
