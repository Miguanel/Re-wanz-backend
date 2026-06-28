from django.db import models
from django.conf import settings


class Task(models.Model):
    TASK_TYPES = [
        ('FIELD', 'Terenowe'),
        ('SCHEDULE', 'Harmonogramowe')
    ]
    STATUS_CHOICES = [
        ('AVAILABLE', 'Dostępne'),
        ('IN_PROGRESS', 'W trakcie'),
        ('VERIFYING', 'Weryfikacja'),
        ('COMPLETED', 'Zakończone')
    ]

    title = models.CharField(max_length=200, verbose_name="Tytuł zadania")
    description = models.TextField(verbose_name="Opis")
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, verbose_name="Typ zadania")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')

    # Kto zlecił i kto wykonuje
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='assigned_tasks')

    bounty = models.IntegerField(default=0, verbose_name="Nagroda (Dobroty)")

    # GPS (dla Zadań Terenowych)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"