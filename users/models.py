from django.contrib.auth.models import AbstractUser
from django.db import models

from core import settings


class CustomUser(AbstractUser):
    dobroty = models.IntegerField(default=0)
    experience = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    reputation = models.IntegerField(default=0)

    # DODANE POLA:
    guild = models.ForeignKey('guilds.Guild', on_delete=models.SET_NULL, null=True, blank=True, related_name='members',
                              verbose_name="Gildia")
    guild_role = models.CharField(max_length=50, default="Nowicjusz", verbose_name="Rola w Gildii")

    def __str__(self):
        return self.username

class SharedImage(models.Model):
    image = models.ImageField(upload_to='shared_images/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_images')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Zdjęcie {self.id} (Wgrał: {self.uploaded_by.username})"