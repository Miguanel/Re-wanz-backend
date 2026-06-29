from rest_framework import serializers
from .models import ForumPost
from django.contrib.auth import get_user_model
# Import niepotrzebny, jeśli go nie używasz wewnątrz klasy
# from users.serializers import SharedImageSerializer

User = get_user_model()

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'level']

class ForumPostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    timeAgo = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    # Zmiana: zamieniamy 'post_images' na 'images' (zgodnie z tym co masz w metodzie create)
    # Jeśli chcesz, żeby w JSONie z API pole nazywało się 'post_images',
    # użyj source='images'
    post_images = serializers.PrimaryKeyRelatedField(
        source='images', many=True, read_only=True
    )

    uploaded_image_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    uploaded_tags = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = ForumPost
        # Używamy poprawnej nazwy pola 'post_images' zdefiniowanej wyżej
        fields = [
            'id', 'author', 'title', 'content', 'post_images',
            'uploaded_image_ids', 'uploaded_tags', 'tags',
            'upvotes', 'views', 'bounty', 'is_resolved', 'timeAgo'
        ]

    def create(self, validated_data):
        image_ids = validated_data.pop('uploaded_image_ids', [])
        tags_data = validated_data.pop('uploaded_tags', [])

        post = ForumPost.objects.create(**validated_data)

        # Obsługa zdjęć (Many-to-Many)
        if image_ids:
            post.images.set(image_ids)

        # Obsługa tagów
        if tags_data:
            # SPRAWDZAMY TYP POLA:
            # Jeśli tags to TaggableManager (django-taggit), używamy .add()
            # Jeśli to JSONField (list), musimy przypisać listę bezpośrednio
            if hasattr(post.tags, 'add'):
                post.tags.add(*tags_data)
            else:
                # Jeśli to zwykłe pole (np. JSONField), przypisujemy listę:
                post.tags = tags_data
                post.save()

        return post

    def get_timeAgo(self, obj):
        return obj.created_at.strftime("%d/%m/%Y, %H:%M")

    def get_tags(self, obj):
        # Sprawdzenie, czy pole istnieje, żeby nie wywalało błędu
        if hasattr(obj, 'tags'):
            # Dla django-taggit:
            if hasattr(obj.tags, 'names'):
                return list(obj.tags.names())
        return []