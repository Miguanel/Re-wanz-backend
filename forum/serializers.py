from rest_framework import serializers
from .models import ForumPost, ForumComment
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    """Zwraca tylko nazwę autora, żeby nie wysyłać całego konta z hasłami!"""

    class Meta:
        model = User
        fields = ['username', 'level']


# Importujemy tłumacz zdjęć, aby API ładnie formatowało linki do obrazków
from users.serializers import SharedImageSerializer


class ForumPostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    timeAgo = serializers.SerializerMethodField()

    # Zwraca gotowe obiekty obrazków (z linkiem URL) przy pobieraniu postów
    images = SharedImageSerializer(many=True, read_only=True)

    # Służy do odbierania listy ID obrazków (np. [1, 2]) podczas tworzenia posta przez Androida
    uploaded_image_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = ForumPost
        # AKTUALIZACJA: Dodajemy 'images' oraz 'uploaded_image_ids'
        fields = ['id', 'author', 'title', 'content', 'images', 'uploaded_image_ids', 'tags', 'upvotes', 'views',
                  'bounty', 'is_resolved', 'timeAgo']

    # Nadpisujemy logikę tworzenia posta, aby połączyć przesłane ID zdjęć z nowym postem
    def create(self, validated_data):
        image_ids = validated_data.pop('uploaded_image_ids', [])
        post = ForumPost.objects.create(**validated_data)
        if image_ids:
            post.images.set(image_ids)  # Przypina wybrane zdjęcia do posta
        return post

    def get_timeAgo(self, obj):
        # W przyszłości tu napiszemy logikę obliczającą czas od publikacji,
        # teraz na potrzeby testów zwracamy prostą datę z bazy.
        return obj.created_at.strftime("%d/%m/%Y, %H:%M")