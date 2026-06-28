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

    # NOWOŚĆ: Mówimy Django, żeby spodziewało się listy stringów z Androida
    tags = serializers.ListField(
        child=serializers.CharField(), required=False
    )

    class Meta:
        model = ForumPost
        fields = ['id', 'author', 'title', 'content', 'images', 'uploaded_image_ids', 'tags', 'upvotes', 'views',
                  'bounty', 'is_resolved', 'timeAgo']

    def create(self, validated_data):
        # 1. WYCIĄGAMY ID zdjęć oraz Tagi ZANIM stworzymy posta!
        image_ids = validated_data.pop('uploaded_image_ids', [])
        tags_data = validated_data.pop('tags', [])

        # 2. Tworzymy "czystego" posta (z samym tytułem i treścią)
        post = ForumPost.objects.create(**validated_data)

        # 3. Dodajemy zdjęcia (jeśli są)
        if image_ids:
            post.images.set(image_ids)

        # 4. Dodajemy tagi (jeśli są) - TERAZ post ma już swoje ID w bazie, więc to zadziała
        if tags_data:
            # Jeśli używasz biblioteki django-taggit, to poniższa linijka wystarczy:
            post.tags.add(*tags_data)

            # (Uwaga: Jeśli masz własny model Tag, odkomentuj to i zakomentuj linijkę wyżej)
            # for tag_name in tags_data:
            #     tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
            #     post.tags.add(tag_obj)

        return post

    def get_timeAgo(self, obj):
        return obj.created_at.strftime("%d/%m/%Y, %H:%M")
