from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),    
    path('jet/', include('jet.urls', 'jet')),    
    path('', include('django.contrib.auth.urls')),    
    
    path('', include('shadowsocks.urls', namespace='shadowsocks')),
    path('server/', include('ssserver.urls', namespace='ssserver')),
    path('api/', include('api.urls', namespace='api')),
]
