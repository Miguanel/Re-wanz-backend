from django.db import models
from django.conf import settings


class ForumPost(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    title = models.CharField(max_length=255)
    content = models.TextField()

    # USUNIĘTO: image (pole powodowało błąd bazy danych)
    # ZOSTAWIONO: images (jako relację ManyToMany do Twoich zdjęć)
    images = models.ManyToManyField(
        'users.SharedImage',
        blank=True,
        related_name='forum_posts',
        verbose_name="Dołączone zdjęcia"
    )

    # Pole tags zostawiamy jako JSONField, będzie świetnie współgrać z nowym serializatorem
    tags = models.JSONField(default=list, blank=True, help_text="Lista tagów, np. ['technologia', 'nauka']")

    created_at = models.DateTimeField(auto_now_add=True)

    # System Stack Overflow
    upvotes = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    bounty = models.IntegerField(default=0)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()

    # Dodane pole parent pozwalające na tworzenie zagnieżdżonych odpowiedzi na komentarze
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on: {self.post.title}"


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_votes')
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='votes')
    value = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_user_post_vote'),
        ]

    def __str__(self):
        return f"Vote ({self.value}) on: {self.post.title}"


# --- NOWY MODEL: Głosowanie na komentarze ---
class CommentVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_votes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='votes')
    value = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'comment'], name='unique_user_comment_vote'),
        ]

    def __str__(self):
        return f"Vote ({self.value}) on comment {self.comment.id} by {self.user.username}"


class Task(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Otwarte'),
        ('IN_PROGRESS', 'W trakcie'),
        ('COMPLETED', 'Zakończone'),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Współrzędne geograficzne dla zadań na mapie (MapTaskRequest)
    latitude = models.FloatField(help_text="Szerokość geograficzna")
    longitude = models.FloatField(help_text="Długość geograficzna")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)

    # Podobnie jak w postach, możemy dodać bounty za wykonanie zlecenia w terenie
    bounty = models.IntegerField(default=0)

    def __str__(self):
        return f"Task: {self.title} ({self.get_status_display()})"