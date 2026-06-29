from django.db.models import Sum
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ForumPost, Vote
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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        """POST /api/forum/posts/{id}/vote/  body: {"value": 1|-1|0, ...}"""
        post = self.get_object()

        try:
            value = int(request.data.get('value'))
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Pole "value" musi być liczbą całkowitą: 1, -1 lub 0.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if value not in (-1, 0, 1):
            return Response(
                {'detail': 'Dozwolone wartości "value": 1 (up), -1 (down), 0 (usuń głos).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vote_obj = Vote.objects.filter(user=request.user, post=post).first()

        if value == 0:
            if vote_obj:
                vote_obj.delete()
        elif vote_obj:
            vote_obj.value = value
            vote_obj.save(update_fields=['value'])
        else:
            Vote.objects.create(user=request.user, post=post, value=value)

        vote_count = post.votes.aggregate(total=Sum('value'))['total'] or 0
        user_vote = Vote.objects.filter(user=request.user, post=post).values_list('value', flat=True).first() or 0

        return Response({
            'vote_count': vote_count,
            'user_vote': user_vote,
            'target_id': post.id,
            'is_post': True,
        })

    # Niestandardowy Endpoint dla mechaniki z Twojego Androida
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upvote(self, request, pk=None):
        """ POST /api/forum/posts/{id}/upvote/ """
        post = self.get_object()
        post.upvotes += 1
        post.save()
        return Response({'status': 'upvoted', 'total_votes': post.upvotes})