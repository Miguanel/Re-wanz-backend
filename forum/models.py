from django.db import models
from django.conf import settings


class ForumPost(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    title = models.CharField(max_length=255)
    content = models.TextField()

    image = models.ImageField(upload_to='forum_images/', null=True, blank=True, verbose_name="Dołączone zdjęcie")
    images = models.ManyToManyField('users.SharedImage', blank=True, related_name='forum_posts', verbose_name="Dołączone zdjęcia")
    tags = models.JSONField(default=list, blank=True, help_text="Lista tagów, np. ['technologia', 'nauka']")

    created_at = models.DateTimeField(auto_now_add=True)

    # System Stack Overflow
    upvotes = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    bounty = models.IntegerField(default=0)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class ForumComment(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    upvotes = models.IntegerField(default=0)
    is_accepted_answer = models.BooleanField(default=False)

    def __str__(self):
        return f"Odpowiedź do: {self.post.title}"