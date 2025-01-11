from django.contrib.auth.models import AbstractUser
from django.db.models import CharField


class CustomUser(AbstractUser):
    username = CharField(
        verbose_name="Юзернейм",
        max_length=128,
        unique=True,
        # validators=[RegexValidator(regex=r'^[\w.@+-]+$')],
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username"]

    def __str__(self):
        return self.username
