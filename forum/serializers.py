from rest_framework import serializers
from .models import ForumPost
from django.contrib.auth import get_user_model
from users.serializers import SharedImageSerializer

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'level']


class ForumPostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    timeAgo = serializers.SerializerMethodField()
    images = SharedImageSerializer(many=True, read_only=True)

    # 1. WŁAŚCIWY ODCZYT (GET) - Metoda gwarantująca brak błędu 500
    tags = serializers.SerializerMethodField()

    # 2. WŁAŚCIWY ZAPIS (POST) - Zbieranie tagów z formularza Androida
    uploaded_tags = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    uploaded_image_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = ForumPost
        fields = ['id', 'author', 'title', 'content', 'images', 'uploaded_image_ids', 'uploaded_tags', 'tags',
                  'upvotes', 'views', 'bounty', 'is_resolved', 'timeAgo']

    def create(self, validated_data):
        image_ids = validated_data.pop('uploaded_image_ids', [])
        tags_data = validated_data.pop('uploaded_tags', [])

        post = ForumPost.objects.create(**validated_data)

        if image_ids:
            post.images.set(image_ids)

        if tags_data:
            post.tags.add(*tags_data)

        return post

    def get_timeAgo(self, obj):
        return obj.created_at.strftime("%d/%m/%Y, %H:%M")

    # Bezpieczne wydobywanie tagów (jako zwykłe stringi)
    def get_tags(self, obj):
        # Sprawdzamy, czy model faktycznie ma pole 'tags', by uniknąć błędu AttributeError
        if hasattr(obj, 'tags'):
            # Funkcja names() działa, jeśli używasz django-taggit
            if hasattr(obj.tags, 'names'):
                return list(obj.tags.names())
            # Jeśli używasz własnego modelu Tag(name=CharField())
            elif hasattr(obj.tags, 'all'):
                return [tag.name for tag in obj.tags.all()]
        return []