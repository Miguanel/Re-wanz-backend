from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CustomUser
from .serializers import UserProfileSerializer

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API dla profili użytkowników.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer

    # AKTUALIZACJA: Dynamiczne uprawnienia
    def get_permissions(self):
        # Jeśli to zapytanie o rejestrację, pozwól wejść każdemu (AllowAny)
        if self.action == 'register':
            return [permissions.AllowAny()]
        # W każdym innym przypadku (np. oglądanie profili), wymagaj logowania
        return [permissions.IsAuthenticated()]

    # Niestandardowy Endpoint "Mój Profil"
    @action(detail=False, methods=['get'])
    def me(self, request):
        """ GET /api/users/me/ """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    # NOWOŚĆ: Endpoint Rejestracji
    @action(detail=False, methods=['post'])
    def register(self, request):
        """ POST /api/users/register/ """
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if not username or not password or not email:
            return Response({'error': 'Wypełnij wszystkie pola'}, status=status.HTTP_400_BAD_REQUEST)

        # Sprawdzamy, czy nazwa nie jest już zajęta
        if CustomUser.objects.filter(username=username).exists():
            return Response({'error': 'Taki wilk już istnieje. Wybierz inną nazwę.'}, status=status.HTTP_400_BAD_REQUEST)

        # Tworzymy nowe konto w bazie
        user = CustomUser.objects.create(
            username=username,
            email=email
        )
        # BARDZO WAŻNE: Funkcja set_password szyfruje hasło.
        # Bez niej hasło byłoby jawnym tekstem i logowanie JWT nie zadziała!
        user.set_password(password)
        user.save()

        return Response({'message': 'Konto utworzone pomyślnie!'}, status=status.HTTP_201_CREATED)
