from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Comment, ForumPost, Task, CommentVote

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'level']


class TaskSerializer(serializers.ModelSerializer):
    """
    Tłumacz dla Zadań Terenowych (Field Tasks).
    Odbiera dane z MapTaskRequest z Androida.
    """
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'latitude', 'longitude',
            'bounty', 'status', 'author', 'created_at'
        ]
        # Zabezpieczenie: Android nie może sam ustawić sobie statusu na "COMPLETED" podczas tworzenia
        read_only_fields = ['id', 'status', 'author', 'created_at']

    def create(self, validated_data):
        # Automatycznie ustawia status początkowy na 'OPEN' (zgodnie z modelem)
        validated_data['status'] = 'OPEN'
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    # Jawna deklaracja parent_id dla zapytań POST (tworzenie odpowiedzi na komentarz z Androida)
    parent_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    # Dodane pola dla systemu oceniania komentarzy
    vote_count = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at', 'parent_id', 'vote_count', 'user_vote']
        read_only_fields = ['created_at']

    def get_vote_count(self, obj):
        # Zlicza sumę głosów przypisanych do tego komentarza
        return sum(vote.value for vote in obj.votes.all())

    def get_user_vote(self, obj):
        # Sprawdza, czy zalogowany użytkownik (wysyłający request) zagłosował na ten komentarz
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = obj.votes.filter(user=request.user).first()
            if vote:
                return vote.value
        return 0


class ForumPostSerializerBase(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    vote_count = serializers.IntegerField(read_only=True)
    user_vote = serializers.IntegerField(read_only=True)
    timeAgo = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

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
        fields = [
            'id', 'author', 'title', 'content', 'post_images',
            'uploaded_image_ids', 'uploaded_tags', 'tags',
            'comment_count', 'vote_count', 'user_vote',
            'upvotes', 'views', 'bounty', 'is_resolved', 'timeAgo',
        ]

    def create(self, validated_data):
        image_ids = validated_data.pop('uploaded_image_ids', [])
        tags_data = validated_data.pop('uploaded_tags', [])

        post = ForumPost.objects.create(**validated_data)

        if image_ids:
            post.images.set(image_ids)

        if tags_data:
            if hasattr(post.tags, 'add'):
                post.tags.add(*tags_data)
            else:
                post.tags = tags_data
                post.save()

        return post

    def get_timeAgo(self, obj):
        return obj.created_at.strftime("%d/%m/%Y, %H:%M")

    def get_tags(self, obj):
        if hasattr(obj, 'tags') and hasattr(obj.tags, 'names'):
            return list(obj.tags.names())
        return []


class ForumPostListSerializer(ForumPostSerializerBase):
    """Lekka odpowiedź dla feedu — bez pełnej listy komentarzy."""

    class Meta(ForumPostSerializerBase.Meta):
        pass


class ForumPostSerializer(ForumPostSerializerBase):
    """Pełna odpowiedź dla pojedynczego posta — z zagnieżdżonymi komentarzami."""

    comments = CommentSerializer(many=True, read_only=True)

    class Meta(ForumPostSerializerBase.Meta):
        fields = ForumPostSerializerBase.Meta.fields + ['comments']