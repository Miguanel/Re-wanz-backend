from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ForumPostViewSet, CommentViewSet

router = DefaultRouter()
router.register(r'posts', ForumPostViewSet, basename='forumpost')
# DODANO: Rejestracja nowego widoku dla komentarzy
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
]