from django.urls import path, include
from django.contrib import admin

from apps.sspanel.views import index

urlpatterns = [
    path('', index, name="index"),
    path('', include('django.contrib.auth.urls')),
    path('api/', include('apps.api.urls', namespace='api')),
    path('sspanel/', include('apps.sspanel.urls', namespace='sspanel')),
    path('server/', include('apps.ssserver.urls', namespace='ssserver')),

    path('admin/', admin.site.urls),
    path('jet/', include('jet.urls', 'jet'))
]
