from django.conf.urls import url
from .import views


app_name = "ssserver"
urlpatterns = [
    url(r'^changesspass/$', views.ChangeSsPass, name='changesspass'),
    url(r'^user/edit/(?P<pk>[0-9]+)$', views.User_edit, name='user_edit'),
    url(r'^changessmethod/$', views.ChangeSsMethod, name='changessmethod'),
    url(r'^changessprotocol/$', views.ChangeSsProtocol, name='changessprotocol'),
    url(r'^changessobfs/$', views.ChangeSsObfs, name='changessobfs'),
    url(r'^test/$', views.testcheck, name='test'),
    url(r'^clean/zombie/user$', views.clean_zombie_user, name='clean_zombie_user'),
    url(r'subscribe/(?P<token>.+)/$', views.Subscribe, name='subscribe')
]
