from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


class Topic(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Newspaper(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    published_date = models.DateField(auto_now_add=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    publishers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="newspapers"
    )

    class Meta:
        ordering = ["-published_date", "title"]

    def __str__(self):
        return self.title


class Redactor(AbstractUser):
    years_of_experience = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0
    )

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"
