from rest_framework import serializers
from .models import CustomUser

class UserProfileSerializer(serializers.ModelSerializer):
    # Pobieramy nazwę gildii, żeby nie zwracać Androidowi tylko suchego ID (np. "1")
    guild_name = serializers.CharField(source='guild.name', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'dobroty', 'experience', 'level',
            'reputation', 'guild', 'guild_name', 'guild_role', 'skills'
        ]
        # Zabezpieczenie (ReadOnly): Android nie może sam sobie wysłać modyfikacji tych pól.
        # Tylko serwer może przyznawać Dobroty i poziomy!
        read_only_fields = ['dobroty', 'experience', 'level', 'reputation']