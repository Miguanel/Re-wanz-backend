from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # <-- Czy tutaj na pewno jest 'api/'?
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpointy dla Twoich aplikacji w Androidzie (Zwróć uwagę na przedrostek 'api/')
    path('api/forum/', include('forum.urls')),
    
    # Endpointy z innych aplikacji dodasz tutaj później:
    path('api/users/', include('users.urls')),
    path('api/guilds/', include('guilds.urls')),
    # path('api/tasks/', include('tasks.urls')),
]
