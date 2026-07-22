from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from core import settings
from .skills_config import AVAILABLE_SKILLS


class CustomUser(AbstractUser):
    # --- PROFIL I TOŻSAMOŚĆ ---
    avatar = models.ForeignKey(
        'SharedImage', on_delete=models.SET_NULL, null=True, blank=True, related_name='avatar_users'
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name="O mnie")
    is_verified = models.BooleanField(default=False, verbose_name="Konto zweryfikowane")
    last_active = models.DateTimeField(default=timezone.now, verbose_name="Ostatnio aktywny")
    last_daily_reward = models.DateTimeField(null=True, blank=True, verbose_name="Ostatnia dzienna nagroda")

    # --- EKONOMIA I PROGRESJA ---
    dobroty = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Dobroty")
    experience = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Doświadczenie")
    level = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Poziom")
    reputation = models.IntegerField(default=0, verbose_name="Reputacja")
    skill_points = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Punkty umiejętności")

    guild = models.ForeignKey('guilds.Guild', on_delete=models.SET_NULL, null=True, blank=True, related_name='members',
                              verbose_name="Gildia")
    guild_role = models.CharField(max_length=50, default="Nowicjusz", verbose_name="Rola w Gildii")

    skills = models.JSONField(default=dict, blank=True, verbose_name="Umiejętności")

    def __str__(self):
        return self.username

    # --- METODY BIZNESOWE MODELU ---
    def add_experience(self, amount):
        if amount <= 0: return False
        self.experience += amount

        leveled_up = False
        threshold = self.level * 100
        while self.experience >= threshold:
            self.experience -= threshold
            self.level += 1
            self.skill_points += 1
            threshold = self.level * 100
            leveled_up = True

        self.save(update_fields=['experience', 'level', 'skill_points'])
        return leveled_up

    def spend_dobroty(self, amount):
        if amount <= 0: return False
        if self.dobroty >= amount:
            self.dobroty -= amount
            self.save(update_fields=['dobroty'])
            return True
        return False

    def unlock_skill(self, skill_key):
        if skill_key not in AVAILABLE_SKILLS:
            raise ValueError("Taka umiejętność nie istnieje.")

        config = AVAILABLE_SKILLS[skill_key]
        current_level = self.skills.get(skill_key, 0)

        if current_level >= config['max_level']:
            raise ValueError("Osiągnięto maksymalny poziom tej umiejętności.")

        cost = config['cost_per_level']
        if self.skill_points < cost:
            raise ValueError("Brak wystarczającej liczby punktów umiejętności.")

        self.skill_points -= cost
        self.skills[skill_key] = current_level + 1
        self.save(update_fields=['skill_points', 'skills'])


class UserRelationship(models.Model):
    """ Model obsługujący znajomych oraz blokowanie graczy """
    RELATION_CHOICES = [
        ('FRIEND', 'Znajomy'),
        ('BLOCKED', 'Zablokowany')
    ]
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='relationships_from', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='relationships_to', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=RELATION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} -> {self.status} -> {self.to_user.username}"


class Notification(models.Model):
    """ Model powiadomień dla gracza (Push / In-app) """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Powiadomienie dla {self.user.username}: {self.title}"


class SharedImage(models.Model):
    image = models.ImageField(upload_to='shared_images/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_images')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Zdjęcie {self.id} (Wgrał: {self.uploaded_by.username})"