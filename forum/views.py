from django.db.models import Count, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Zaktualizowane importy modeli (dodano Comment i CommentVote)
from .models import ForumPost, Vote, Comment, CommentVote
from .serializers import (
    CommentSerializer,
    ForumPostListSerializer,
    ForumPostSerializer,
)

# Import naszego nowego strażnika uprawnień
from .permissions import IsAuthorOrAdminOrReadOnly


class ForumPostViewSet(viewsets.ModelViewSet):
    """
    Automatycznie generuje pełne API dla Forum:
    - GET /api/forum/posts/ -> Lista wszystkich postów
    - POST /api/forum/posts/ -> Dodaj nowy post
    - GET /api/forum/posts/{id}/ -> Pobierz konkretny post (z listą komentarzy)
    - DELETE /api/forum/posts/{id}/ -> Usuń post (tylko autor lub admin)
    """
    serializer_class = ForumPostSerializer

    # DODANO: IsAuthorOrAdminOrReadOnly
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]

    def get_queryset(self):
        queryset = ForumPost.objects.annotate(
            comment_count=Count('comments', distinct=True),
            vote_count=Coalesce(Sum('votes__value'), Value(0)),
        ).order_by('-created_at')

        user = self.request.user
        if user.is_authenticated:
            user_vote_subquery = Vote.objects.filter(
                post=OuterRef('pk'),
                user=user,
            ).values('value')[:1]
            queryset = queryset.annotate(
                user_vote=Coalesce(Subquery(user_vote_subquery), Value(0)),
            )
        else:
            queryset = queryset.annotate(user_vote=Value(0))

        if self.action == 'retrieve':
            # Optymalizacja zapytań dla komentarzy
            queryset = queryset.prefetch_related('comments__author', 'comments__votes', 'images')
        elif self.action == 'list':
            queryset = queryset.prefetch_related('images')

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ForumPostListSerializer
        return ForumPostSerializer

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        serializer.instance = self.get_queryset().get(pk=post.pk)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """GET/POST /api/forum/posts/{id}/comments/"""
        post = self.get_object()

        if request.method == 'GET':
            # Optymalizacja N+1 dla głosów przy komentarzach
            comments = post.comments.select_related('author').prefetch_related('votes').order_by('created_at')
            serializer = CommentSerializer(comments, many=True, context={'request': request})
            return Response(serializer.data)

        # Context potrzebny aby pobrać user_vote dla nowo utworzonego komentarza
        serializer = CommentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user, post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        """POST /api/forum/posts/{id}/vote/  body: {"value": 1|-1|0}"""
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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upvote(self, request, pk=None):
        """ POST /api/forum/posts/{id}/upvote/ """
        post = self.get_object()
        post.upvotes += 1
        post.save()
        return Response({'status': 'upvoted', 'total_votes': post.upvotes})


# --- NOWY WIDOK: Zarządzanie komentarzami (usuwanie, głosowanie) ---
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        """POST /api/forum/comments/{id}/vote/  body: {"value": 1|-1|0}"""
        comment = self.get_object()

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

        vote_obj = CommentVote.objects.filter(user=request.user, comment=comment).first()

        if value == 0:
            if vote_obj:
                vote_obj.delete()
        elif vote_obj:
            vote_obj.value = value
            vote_obj.save(update_fields=['value'])
        else:
            CommentVote.objects.create(user=request.user, comment=comment, value=value)

        vote_count = comment.votes.aggregate(total=Sum('value'))['total'] or 0
        user_vote = CommentVote.objects.filter(user=request.user, comment=comment).values_list('value',
                                                                                               flat=True).first() or 0

        return Response({
            'vote_count': vote_count,
            'user_vote': user_vote,
            'target_id': comment.id,
            'is_post': False,
        })