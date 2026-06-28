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
    images = SharedImageSerializer(many=True, read_only=True)

    uploaded_image_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    # 1. POLE DO ODCZYTU: Gdy Android robi GET, wysyłamy ładną listę stringów
    tags = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='name'
    )

    # 2. POLE DO ZAPISU: Zmieniamy nazwę na 'uploaded_tags', żeby nie gryzło się z oryginałem
    uploaded_tags = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = ForumPost
        # Zamieniamy miejscami pola wejściowe
        fields = ['id', 'author', 'title', 'content', 'images', 'uploaded_image_ids', 'uploaded_tags', 'tags',
                  'upvotes', 'views', 'bounty', 'is_resolved', 'timeAgo']

    def create(self, validated_data):
        # 3. Wyciągamy dane z odpowiednich pół "write_only"
        image_ids = validated_data.pop('uploaded_image_ids', [])
        tags_data = validated_data.pop('uploaded_tags', [])

        post = ForumPost.objects.create(**validated_data)

        if image_ids:
            post.images.set(image_ids)

        if tags_data:
            # Jeśli używasz django-taggit:
            post.tags.add(*tags_data)

        return post

    def get_timeAgo(self, obj):
        return obj.created_at.strftime("%d/%m/%Y, %H:%M")
