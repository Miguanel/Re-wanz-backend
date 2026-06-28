from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GuildViewSet

router = DefaultRouter()
router.register(r'', GuildViewSet, basename='guild')

urlpatterns = [
    path('', include(router.urls)),
]