from rest_framework import serializers
from .models import ForumPost, ForumComment
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthorSerializer(serializers.ModelSerializer):
    """Zwraca tylko nazwę autora, żeby nie wysyłać całego konta z hasłami!"""
    class Meta:
        model = User
        fields = ['username', 'level']

class ForumPostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True) # Zagnieżdżamy informacje o autorze
    # Zwraca string np. "2 godz. temu" (na razie uproszczone do daty)
    timeAgo = serializers.SerializerMethodField()

    class Meta:
        model = ForumPost
        # Pola muszą zgadzać się z tymi, których oczekuje Twój Android w klasie ForumPost.kt!
        fields = ['id', 'author', 'title', 'content', 'tags', 'upvotes', 'views', 'bounty', 'is_resolved', 'timeAgo']

    def get_timeAgo(self, obj):
        # W przyszłości tu napiszemy logikę obliczającą czas od publikacji,
        # teraz na potrzeby testów zwracamy prostą datę z bazy.
        return obj.created_at.strftime("%d/%m/%Y, %H:%M")