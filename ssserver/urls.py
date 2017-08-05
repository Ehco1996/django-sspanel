from django.conf.urls import url
from .import views


app_name = "ssserver"
urlpatterns = [
    url(r'^changesspass/$', views.ChangeSsPass, name='changesspass'),
    url(r'^user/edit/(?P<pk>[0-9]+)$', views.User_edit, name='user_edit'),
    


]
