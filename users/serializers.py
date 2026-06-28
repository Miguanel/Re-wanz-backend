from rest_framework import serializers
from .models import CustomUser, SharedImage


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


class SharedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedImage
        fields = ['id', 'image', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at']  # Android nie może tego sfałszować
