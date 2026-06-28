from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CustomUser
from .serializers import UserProfileSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API dla profili użytkowników.
    Używamy ReadOnlyModelViewSet, aby zablokować ręczne modyfikacje profilu z zewnątrz na tym etapie.
    GET /api/users/ -> Lista wszystkich wilków (np. do rankingu)
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Niestandardowy Endpoint "Mój Profil"
    @action(detail=False, methods=['get'])
    def me(self, request):
        """ GET /api/users/me/ -> Pobiera profil osoby aktualnie zalogowanej (na podstawie tokena JWT) """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)