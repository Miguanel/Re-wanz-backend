from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ForumPostViewSet, CommentViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'posts', ForumPostViewSet, basename='forumpost')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'tasks', TaskViewSet, basename='task') # Zaktualizowano: Dodano Zadania Terenowe

urlpatterns = [
    path('', include(router.urls)),
]