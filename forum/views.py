from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, Sum, Value, Q
from django.db.models.functions import Coalesce
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import ForumPost, Vote, Comment, CommentVote
from tasks.models import Task
from .serializers import (
    CommentSerializer,
    ForumPostListSerializer,
    ForumPostSerializer,
    TaskSerializer
)
from .permissions import IsAuthorOrAdminOrReadOnly


class BurstRateThrottle(UserRateThrottle):
    rate = '10/min'


class ForumPostViewSet(viewsets.ModelViewSet):
    serializer_class = ForumPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    throttle_classes = [AnonRateThrottle, BurstRateThrottle]

    def get_queryset(self):
        # Filtrowanie tylko nieusuniętych postów (Soft Delete)
        queryset = ForumPost.objects.filter(is_deleted=False).annotate(
            comment_count=Count('comments', filter=Q(comments__is_deleted=False), distinct=True),
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
            queryset = queryset.prefetch_related('comments__author', 'comments__votes', 'images')
        elif self.action == 'list':
            queryset = queryset.prefetch_related('images')

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ForumPostListSerializer
        return ForumPostSerializer

    def perform_create(self, serializer):
        # Walidacja środków na koncie dla Bounty (wymaga modelu z systemem punktów)
        bounty = self.request.data.get('bounty', 0)
        if int(bounty) > 0:
            user = self.request.user
            # Jeśli w przyszłości dodasz wallet/points do Usera:
            if getattr(user, 'points', 0) < int(bounty):
                raise ValidationError("Niewystarczająca ilość punktów na koncie.")
            user.points -= int(bounty)
            user.save()

        post = serializer.save(author=self.request.user)
        serializer.instance = self.get_queryset().get(pk=post.pk)

    def perform_destroy(self, instance):
        """ Implementacja Soft Delete """
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])
        # Ewentualny zwrot zamrożonego bounty do autora

    def retrieve(self, request, *args, **kwargs):
        """ Zliczanie wyświetleń (View Counter) """
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def resolve(self, request, pk=None):
        """ Akceptacja najlepszej odpowiedzi (Bounty Payout & Resolve logic) """
        post = self.get_object()

        if post.author != request.user and not request.user.is_staff:
            raise PermissionDenied("Tylko autor może zaakceptować rozwiązanie.")

        if post.is_resolved:
            raise ValidationError("Ten problem został już rozwiązany.")

        comment_id = request.data.get('comment_id')
        try:
            comment = post.comments.get(id=comment_id, is_deleted=False)
        except Comment.DoesNotExist:
            raise ValidationError("Wybrany komentarz nie istnieje.")

        with transaction.atomic():
            post.is_resolved = True
            post.save(update_fields=['is_resolved'])

            # Wypłata nagrody (Bounty Transfer)
            if post.bounty > 0:
                author_to_reward = comment.author
                # author_to_reward.points += post.bounty
                # author_to_reward.save()

        return Response({"status": "resolved", "bounty_awarded": post.bounty})

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == 'GET':
            comments = post.comments.filter(is_deleted=False).select_related('author').prefetch_related(
                'votes').order_by('created_at')
            serializer = CommentSerializer(comments, many=True, context={'request': request})
            return Response(serializer.data)

        if post.is_resolved:
            raise ValidationError("Nie można komentować rozwiązanego problemu.")

        serializer = CommentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user, post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        post = self.get_object()

        if post.author == request.user:
            raise ValidationError("Nie możesz oceniać własnego wpisu.")

        try:
            value = int(request.data.get('value'))
        except (TypeError, ValueError):
            return Response({'detail': 'Wartość musi być: 1, -1 lub 0.'}, status=status.HTTP_400_BAD_REQUEST)

        if value not in (-1, 0, 1):
            return Response({'detail': 'Niedozwolona wartość głosu.'}, status=status.HTTP_400_BAD_REQUEST)

        vote_obj = Vote.objects.filter(user=request.user, post=post).first()

        if value == 0:
            if vote_obj: vote_obj.delete()
        elif vote_obj:
            vote_obj.value = value
            vote_obj.save(update_fields=['value'])
        else:
            Vote.objects.create(user=request.user, post=post, value=value)

        vote_count = post.votes.aggregate(total=Sum('value'))['total'] or 0
        user_vote = Vote.objects.filter(user=request.user, post=post).values_list('value', flat=True).first() or 0

        return Response({'vote_count': vote_count, 'user_vote': user_vote, 'target_id': post.id, 'is_post': True})


class CommentViewSet(viewsets.ModelViewSet):
    # Ograniczenie widoczności na poziomie QuerySetu
    queryset = Comment.objects.filter(is_deleted=False)
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    throttle_classes = [AnonRateThrottle, BurstRateThrottle]

    def perform_destroy(self, instance):
        """ Miękkie usuwanie komentarza zapobiega zniszczeniu drzewa odpowiedzi """
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        comment = self.get_object()

        if comment.author == request.user:
            raise ValidationError("Nie możesz oceniać własnego komentarza.")

        try:
            value = int(request.data.get('value'))
        except (TypeError, ValueError):
            return Response({'detail': 'Wartość musi być: 1, -1 lub 0.'}, status=status.HTTP_400_BAD_REQUEST)

        vote_obj = CommentVote.objects.filter(user=request.user, comment=comment).first()

        if value == 0:
            if vote_obj: vote_obj.delete()
        elif vote_obj:
            vote_obj.value = value
            vote_obj.save(update_fields=['value'])
        else:
            CommentVote.objects.create(user=request.user, comment=comment, value=value)

        vote_count = comment.votes.aggregate(total=Sum('value'))['total'] or 0
        user_vote = CommentVote.objects.filter(user=request.user, comment=comment).values_list('value',
                                                                                               flat=True).first() or 0

        return Response({'vote_count': vote_count, 'user_vote': user_vote, 'target_id': comment.id, 'is_post': False})


class TaskViewSet(viewsets.ModelViewSet):
    # Sortujemy po ID zamiast created_at (najwyższe ID = najnowsze)
    queryset = Task.objects.all().order_by('-id')
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)  # Zmieniono author na creator

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def assign(self, request, pk=None):
        task = self.get_object()
        if task.status != 'OPEN':
            raise ValidationError("To zadanie nie jest już otwarte.")
        if task.creator == request.user:  # Zmieniono author na creator
            raise ValidationError("Nie możesz przypisać się do własnego zadania.")

        task.assignee = request.user
        task.status = 'IN_PROGRESS'
        task.save(update_fields=['assignee', 'status'])
        return Response({"status": "assigned"})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def complete(self, request, pk=None):
        task = self.get_object()
        if task.creator != request.user and not request.user.is_staff:  # Zmieniono author na creator
            raise PermissionDenied("Tylko twórca zlecenia może potwierdzić jego wykonanie.")
        if task.status != 'IN_PROGRESS':
            raise ValidationError("Zadanie musi być w trakcie realizacji, aby je zakończyć.")

        with transaction.atomic():
            task.status = 'COMPLETED'
            task.save(update_fields=['status'])

        return Response({"status": "completed"})