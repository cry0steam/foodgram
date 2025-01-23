from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .constants import (
    EMAIL_LENGTH,
    FIRSTNAME_LENGTH,
    LASTNAME_LENGTH,
    USERNAME_LENGTH,
)


class CustomUser(AbstractUser):
    username = models.CharField(
        'Юзернейм',
        max_length=USERNAME_LENGTH,
        unique=True,
        validators=[RegexValidator(regex=r'^[\w.@+-]+$')],
    )
    first_name = models.CharField(
        'Имя',
        max_length=FIRSTNAME_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=LASTNAME_LENGTH,
    )
    email = models.EmailField(
        'email',
        max_length=EMAIL_LENGTH,
        unique=True,
    )
    avatar = models.ImageField(
        blank=True,
        null=True,
        upload_to='media/avatars/',
        verbose_name='Аватар',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    author = models.ForeignKey(
        CustomUser,
        related_name='author',
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )
    subscriber = models.ForeignKey(
        CustomUser,
        related_name='subscriber',
        verbose_name='Подписчики',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('author',)
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'subscriber'),
                name='unique_follow',
            ),
        )

    def __str__(self):
        return f'{self.author} {self.subscriber}'
