from django.db import models


class Guild(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nazwa Gildii")
    description = models.TextField(blank=True, verbose_name="Opis")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gildia"
        verbose_name_plural = "Gildie"

    def __str__(self):
        return self.name