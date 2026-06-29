from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ForumPost
from .serializers import CommentSerializer, ForumPostSerializer

class ForumPostViewSet(viewsets.ModelViewSet):
    """
    Automatycznie generuje pełne API dla Forum:
    - GET /api/forum/posts/ -> Lista wszystkich postów
    - POST /api/forum/posts/ -> Dodaj nowy post
    - GET /api/forum/posts/{id}/ -> Pobierz konkretny post
    """
    queryset = ForumPost.objects.all().order_by('-created_at') # Domyślnie sortuje od najnowszych
    serializer_class = ForumPostSerializer
    # Na ten moment pozwalamy każdemu (nawet niezalogowanym z Androida) czytać posty,
    # ale do dodawania wymagamy logowania.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Kiedy Android przysyła POST z nowym zadaniem,
        # automatycznie przypisz zalogowanego użytkownika (z tokena) jako autora.
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """GET/POST /api/forum/posts/{id}/comments/"""
        post = self.get_object()

        if request.method == 'GET':
            comments = post.comments.all().order_by('created_at')
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user, post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Niestandardowy Endpoint dla mechaniki z Twojego Androida
    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        """ POST /api/forum/posts/{id}/upvote/ """
        post = self.get_object()
        post.upvotes += 1
        post.save()
        return Response({'status': 'upvoted', 'total_votes': post.upvotes})