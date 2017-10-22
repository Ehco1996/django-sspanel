from django.conf.urls import url
from .import views


app_name = "api"
urlpatterns = [
    url(r'^test/$', views.test, name='test'),
    url(r'^user/data/$', views.userData, name='userdata'),
    url(r'^node/data/$', views.nodeData, name='nodedata'),
    url(r'^donate/data/$', views.donateData, name='donatedata'),
]
