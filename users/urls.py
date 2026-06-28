from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, SharedImageViewSet

router = DefaultRouter()
# Rejestrujemy nowy endpoint: /api/users/images/
router.register(r'images', SharedImageViewSet, basename='sharedimage')
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]