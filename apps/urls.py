from django.urls import path, include
from django.contrib import admin

from apps.sspanel.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('django.contrib.auth.urls')),

    path('jet/', include('jet.urls', 'jet')),
    path('prom/', include('django_prometheus.urls')),

    path('', index, name="index"),
    path('api/', include('apps.api.urls', namespace='api')),
    path('sspanel/', include('apps.sspanel.urls', namespace='sspanel')),
    path('server/', include('apps.ssserver.urls', namespace='ssserver')),

]
