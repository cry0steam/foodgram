from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, EmailField


class CustomUser(AbstractUser):
    username = CharField(
        'Юзернейм',
        max_length=150,
        unique=True,
        # validators=[RegexValidator(regex=r'^[\w.@+-]+$')],
    )
    first_name = CharField(
        'Имя',
        max_length=150,
    )
    last_name = CharField(
        'Фамилия',
        max_length=150,
    )
    email = EmailField(
        'email',
        max_length=254,
        unique=True,
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
