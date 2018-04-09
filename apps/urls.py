from django.urls import path, include
from django.contrib import admin

from apps.shadowsocks.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('jet/', include('jet.urls', 'jet')),

    path('', include('django.contrib.auth.urls')),
    path('', index),
    path('sspanel/', include('apps.shadowsocks.urls', namespace='shadowsocks')),
    path('server/', include('apps.ssserver.urls', namespace='ssserver')),
    path('api/', include('apps.api.urls', namespace='api')),
]
