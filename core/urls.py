import os

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autoryzacja JWT (Logowanie z aplikacji Android)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpointy dla Twoich aplikacji w Androidzie
    path('api/forum/', include('forum.urls')),
    path('api/guilds/', include('guilds.urls')),
    # path('api/tasks/', include('tasks.urls')),
    path('api/users/', include('users.urls')),
]

# NOWOŚĆ: Pozwala serwerowi zwracać wgrane pliki (Media) pod dedykowanym URL
if settings.DEBUG or 'RENDER' not in os.environ:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)