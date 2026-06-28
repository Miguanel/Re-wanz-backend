from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Endpointy dla Twoich aplikacji w Androidzie (Zwróć uwagę na przedrostek 'api/')
    path('api/forum/', include('forum.urls')),
    
    # Endpointy z innych aplikacji dodasz tutaj później:
    path('api/users/', include('users.urls')),
    path('api/guilds/', include('guilds.urls')),
    # path('api/tasks/', include('tasks.urls')),
]
