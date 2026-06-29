from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Comment, ForumPost

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'level']


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at']
        read_only_fields = ['created_at']


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
