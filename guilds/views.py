from rest_framework import viewsets, permissions
from .models import Guild
from .serializers import GuildSerializer

class GuildViewSet(viewsets.ModelViewSet):
    """
    Automatyczne API dla Gildii:
    GET /api/guilds/ - Lista wszystkich plemion
    POST /api/guilds/ - Załóż nowe plemię
    """
    queryset = Guild.objects.all().order_by('-created_at')
    serializer_class = GuildSerializer
    # Każdy może przeglądać gildie, ale tylko zalogowani mogą je tworzyć
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]