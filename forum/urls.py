from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ForumPostViewSet

router = DefaultRouter()
router.register(r'posts', ForumPostViewSet, basename='forumpost')

urlpatterns = [
    path('', include(router.urls)),
]