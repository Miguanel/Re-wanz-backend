from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import CustomUser, SharedImage
from .serializers import UserProfileSerializer, SharedImageSerializer


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


class SharedImageViewSet(viewsets.ModelViewSet):
    """
    Endpoint do wgrywania zdjęć z telefonu (np. do Zadań Terenowych lub Postów)
    """
    queryset = SharedImage.objects.all()
    serializer_class = SharedImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Mówi Django, jak ma odczytać plik ze strumienia danych HTTP (form-data)
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        # Zabezpieczenie: Zdjęcie zawsze jest przypisywane do użytkownika, który wysłał token JWT
        serializer.save(uploaded_by=self.request.user)