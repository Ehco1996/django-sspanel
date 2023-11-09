from django.urls import path

from . import views

app_name = "openapi"
urlpatterns = [
    path("proxy_nodes/search/", views.ProxyNodeSearchView.as_view()),
    path("proxy_nodes/<int:node_id>/", views.ProxyNodeDetailView.as_view()),
    path(
        "proxy_nodes/<int:node_id>/reset_multi_user_port/",
        views.ProxyNodeResetMultiUserPortView.as_view(),
    ),
]
