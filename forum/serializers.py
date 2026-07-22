from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Comment, ForumPost, CommentVote
from tasks.models import Task

User = get_user_model()

# Przykładowy filtr wulgaryzmów
PROFANITY_LIST = ['spam', 'obraźliwe_słowo1', 'obraźliwe_słowo2']


def filter_profanity(text):
    for word in PROFANITY_LIST:
        if word in text.lower():
            raise ValidationError(f"Treść zawiera niedozwolone słownictwo: {word}")
    return text


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'level']


class TaskSerializer(serializers.ModelSerializer):
    creator = AuthorSerializer(read_only=True) # Zmieniono author na creator
    assignee = AuthorSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'latitude', 'longitude',
            'bounty', 'status', 'creator', 'assignee' # Usunięto daty, dodano creator
        ]
        read_only_fields = ['id', 'status', 'creator', 'assignee']

    def create(self, validated_data):
        validated_data['status'] = 'OPEN'
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    parent_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    vote_count = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at', 'updated_at', 'is_deleted', 'parent_id', 'vote_count',
                  'user_vote']
        read_only_fields = ['created_at', 'updated_at', 'is_deleted']

    def validate_content(self, value):
        return filter_profanity(value)

    def validate_parent_id(self, value):
        """ Limitowanie głębokości zagnieżdżeń do maksymalnie 2 poziomów """
        if value:
            try:
                parent = Comment.objects.get(id=value)
                if parent.is_deleted:
                    raise ValidationError("Nie można odpowiedzieć na usunięty komentarz.")
                depth = 1
                current = parent
                while current.parent_id:
                    depth += 1
                    current = current.parent
                if depth >= 2:
                    raise ValidationError("Maksymalna głębokość odpowiedzi została osiągnięta.")
            except Comment.DoesNotExist:
                raise ValidationError("Wskazany komentarz nadrzędny nie istnieje.")
        return value

    def get_vote_count(self, obj):
        return sum(vote.value for vote in obj.votes.all())

    def get_user_vote(self, obj):
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
        child=serializers.CharField(max_length=30), write_only=True, required=False
    )

    class Meta:
        model = ForumPost
        fields = [
            'id', 'author', 'title', 'content', 'post_images',
            'uploaded_image_ids', 'uploaded_tags', 'tags',
            'comment_count', 'vote_count', 'user_vote',
            'upvotes', 'views', 'bounty', 'is_resolved', 'is_deleted', 'timeAgo', 'updated_at'
        ]
        read_only_fields = ['is_resolved', 'is_deleted', 'views', 'upvotes']

    def validate_content(self, value):
        return filter_profanity(value)

    def validate_uploaded_tags(self, value):
        if len(value) > 5:
            raise ValidationError("Możesz dodać maksymalnie 5 tagów.")
        return value

    def create(self, validated_data):
        image_ids = validated_data.pop('uploaded_image_ids', [])
        tags_data = validated_data.pop('uploaded_tags', [])

        post = ForumPost.objects.create(**validated_data)

        if image_ids:
            post.images.set(image_ids)
        if tags_data:
            post.tags = tags_data
            post.save()

        return post

    def update(self, instance, validated_data):
        """ Pełna obsługa edycji wpisu z aktualizacją zdjęć i tagów """
        image_ids = validated_data.pop('uploaded_image_ids', None)
        tags_data = validated_data.pop('uploaded_tags', None)

        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)

        if image_ids is not None:
            instance.images.set(image_ids)
        if tags_data is not None:
            instance.tags = tags_data

        instance.save()
        return instance

    def get_timeAgo(self, obj):
        return obj.created_at.strftime("%d/%m/%Y, %H:%M")

    def get_tags(self, obj):
        if isinstance(obj.tags, list):
            return obj.tags
        return []


class ForumPostListSerializer(ForumPostSerializerBase):
    class Meta(ForumPostSerializerBase.Meta):
        pass


class ForumPostSerializer(ForumPostSerializerBase):
    comments = serializers.SerializerMethodField()

    class Meta(ForumPostSerializerBase.Meta):
        fields = ForumPostSerializerBase.Meta.fields + ['comments']

    def get_comments(self, obj):
        # Pobieramy tylko nieusunięte komentarze najwyższego poziomu (resztę może doczytywać apka)
        comments = obj.comments.filter(is_deleted=False).order_by('created_at')
        return CommentSerializer(comments, many=True, context=self.context).data