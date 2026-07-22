from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class ForumPost(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    title = models.CharField(max_length=255)
    content = models.TextField()

    images = models.ManyToManyField(
        'users.SharedImage',
        blank=True,
        related_name='forum_posts',
        verbose_name="Dołączone zdjęcia"
    )

    tags = models.JSONField(default=list, blank=True, help_text="Lista tagów, np. ['technologia', 'nauka']")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Zaktualizowano: śledzenie edycji
    is_deleted = models.BooleanField(default=False) # Zaktualizowano: miękkie usuwanie

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

    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Zaktualizowano: śledzenie edycji
    is_deleted = models.BooleanField(default=False) # Zaktualizowano: miękkie usuwanie

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



# --- SYGNAŁY (Podstawa pod system reputacji) ---
@receiver(post_save, sender=Vote)
@receiver(post_save, sender=CommentVote)
def update_reputation_on_vote(sender, instance, created, **kwargs):
    """ Miejsce na podpięcie logiki dodawania EXP/poziomów za otrzymane głosy. """
    pass