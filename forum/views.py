from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ForumPost
from .serializers import ForumPostSerializer

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

    # Niestandardowy Endpoint dla mechaniki z Twojego Androida
    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        """ POST /api/forum/posts/{id}/upvote/ """
        post = self.get_object()
        post.upvotes += 1
        post.save()
        return Response({'status': 'upvoted', 'total_votes': post.upvotes})