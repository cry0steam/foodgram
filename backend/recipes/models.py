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
    ingredients = models.ManyToManyField(Ingredient)
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=256)
    text = models.TextField()
    image = models.ImageField(
        upload_to='recipes/images',
        null=True,
        default=None,
    )
    cooking_time = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipes',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredients',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField()


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        related_name='shopping_cart_users',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart_recipes',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_list_model',
            )
        ]


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favorite_recipe_users',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite_recipes',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe_model',
            )
        ]
