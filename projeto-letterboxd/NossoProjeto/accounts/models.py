"""
Modelos do app accounts.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone  


class CustomUser(AbstractUser):
    """
    :param data_nascimento: data de nascimento do usuario
    :param bio: texto de apresentacao do usuario
    """

    email = models.EmailField(unique=True)
    data_nascimento = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)


    def __str__(self):
        return self.username

class PasswordResetCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.code}"

    def is_expired(self):
        # Considera o código expirado após 15 minutos
        return timezone.now() > self.created_at + timezone.timedelta(minutes=15)


