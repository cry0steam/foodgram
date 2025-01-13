from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=64)


class Tag(models.Model):
    slug = models.SlugField(max_length=32)
    name = models.CharField(max_length=32, unique=True)


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
    )
    ingredients = models.ManyToManyField(Ingredient)
    name = models.CharField(max_length=256)
    text = models.TextField()
    image = models.ImageField(
        upload_to='recipes/images',
        null=True,
        default=None,
    )
    cooking_time = models.PositiveIntegerField()
