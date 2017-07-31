from django.conf.urls import url
from .import views


app_name = "ssserver"
urlpatterns = [
    url(r'^changesspass/$', views.ChangeSsPass, name='changesspass'),


]
