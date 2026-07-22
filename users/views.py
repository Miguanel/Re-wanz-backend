from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import CustomUser, SharedImage, Notification, UserRelationship
from .serializers import (
    UserProfileSerializer, SharedImageSerializer,
    ChangePasswordSerializer, NotificationSerializer
)
from .skills_config import AVAILABLE_SKILLS


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomUser.objects.all().order_by('-level')
    serializer_class = UserProfileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'id', 'guild__name']

    def get_queryset(self):
        queryset = super().get_queryset()
        skill_param = self.request.query_params.get('skill', None)

        if skill_param and skill_param in AVAILABLE_SKILLS:
            queryset = queryset.filter(skills__has_key=skill_param)

        # Ochrona Społecznościowa: Ukryj graczy, których zalogowany użytkownik zablokował
        # oraz tych, którzy zablokowali zalogowanego użytkownika
        user = self.request.user
        if user.is_authenticated:
            blocked_users = UserRelationship.objects.filter(
                from_user=user, status='BLOCKED'
            ).values_list('to_user_id', flat=True)

            blockers = UserRelationship.objects.filter(
                to_user=user, status='BLOCKED'
            ).values_list('from_user_id', flat=True)

            queryset = queryset.exclude(id__in=list(blocked_users) + list(blockers))

        return queryset

    def get_permissions(self):
        if self.action == 'register':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        request.user.last_active = timezone.now()
        request.user.save(update_fields=['last_active'])
        return Response(self.get_serializer(request.user).data)

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """ Bezpieczna zmiana hasła dla zalogowanego gracza """
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not check_password(serializer.validated_data['old_password'], user.password):
            return Response({"error": "Stare hasło jest nieprawidłowe."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Hasło zostało pomyślnie zmienione."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def daily_reward(self, request):
        """ Endpoint przyznający nagrodę za codzienne logowanie """
        user = request.user
        now = timezone.now()

        if user.last_daily_reward and now - user.last_daily_reward < timedelta(days=1):
            return Response({"error": "Dzisiejsza nagroda została już odebrana."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(id=user.id)
            user.last_daily_reward = now
            user.dobroty += 25  # Przykład: 25 waluty za wejście
            leveled_up = user.add_experience(50)  # Przykład: 50 expa za wejście
            user.save()

            msg = "Odebrano dzienna nagrodę: 25 Dobrotów i 50 Punktów Doświadczenia!"
            if leveled_up:
                msg += " Awansowałeś na nowy poziom!"

            Notification.objects.create(user=user, title="Codzienna Nagroda", message=msg)

        return Response({"message": msg, "dobroty": user.dobroty, "experience": user.experience})

    @action(detail=True, methods=['post'])
    def add_friend(self, request, pk=None):
        """ Dodawanie innego gracza do znajomych """
        target_user = self.get_object()
        if target_user == request.user:
            return Response({"error": "Nie możesz dodać samego siebie."}, status=status.HTTP_400_BAD_REQUEST)

        rel, created = UserRelationship.objects.update_or_create(
            from_user=request.user, to_user=target_user,
            defaults={'status': 'FRIEND'}
        )
        Notification.objects.create(
            user=target_user, title="Nowy znajomy",
            message=f"Gracz {request.user.username} dodał Cię do znajomych."
        )
        return Response({"message": f"Dodano {target_user.username} do znajomych."})

    @action(detail=True, methods=['post'])
    def block_user(self, request, pk=None):
        """ Blokowanie toksycznego gracza """
        target_user = self.get_object()
        if target_user == request.user:
            return Response({"error": "Nie możesz zablokować samego siebie."}, status=status.HTTP_400_BAD_REQUEST)

        UserRelationship.objects.update_or_create(
            from_user=request.user, to_user=target_user,
            defaults={'status': 'BLOCKED'}
        )
        return Response({"message": f"Zablokowano gracza {target_user.username}."})


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ Widok do pobierania i odczytywania powiadomień gracza """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"status": "Oznaczono jako przeczytane."})


class SharedImageViewSet(viewsets.ModelViewSet):
    queryset = SharedImage.objects.all()
    serializer_class = SharedImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)