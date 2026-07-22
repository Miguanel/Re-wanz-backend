from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, SharedImageViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'images', SharedImageViewSet, basename='sharedimage')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]