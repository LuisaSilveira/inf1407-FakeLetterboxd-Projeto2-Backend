"""
Modelos do app accounts.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    :param data_nascimento: data de nascimento do usuario
    :param bio: texto de apresentacao do usuario
    :param foto_perfil: foto de perfil do usuario
    """

    data_nascimento = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    foto_perfil = models.ImageField(
        upload_to='accounts/img/perfil-fotos/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username
