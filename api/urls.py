from django.conf.urls import url
from .import views


app_name = "api"
urlpatterns = [
    url(r'^test/$', views.test, name='test'),
    url(r'^user/data/$', views.userData, name='userdata'),
    url(r'^node/data/$', views.nodeData, name='nodedata'),
    url(r'^donate/data/$', views.donateData, name='donatedata'),
    url(r'^random/port/$', views.change_ss_port, name='changessport'),
    url(r'^gen/invitecode/$', views.gen_invite_code, name='geninvitecode'),
    url(r'^shop/$', views.purchase, name='purchase'),
    url(r'^pay/request/$', views.pay_request, name='pay_request'),
    url(r'^pay/query/$', views.pay_query, name='pay_query'),
    url(r'^traffic/query/$', views.traffic_query, name='traffic_query'),                                            
]
