from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import (
    INGREDIENT_LENGTH,
    MAX_AMOUNT,
    MAX_TIME,
    MIN_AMOUNT,
    MIN_TIME,
    TAG_NAME_LENGTH,
    TAG_SLUG_LENGTH,
    UNIT_LENGTH,
)

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=INGREDIENT_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=UNIT_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Tag(models.Model):
    slug = models.SlugField('Слаг', max_length=TAG_SLUG_LENGTH, unique=True)
    name = models.CharField(
        'Название', max_length=TAG_NAME_LENGTH, unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='ingredient_recipes',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='recipes',
        on_delete=models.CASCADE,
    )
    name = models.CharField('Название', max_length=256)
    text = models.TextField('Описание')
    image = models.ImageField(
        'Фото',
        upload_to='recipes/images',
        null=False,
        default=None,
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(MIN_TIME), MaxValueValidator(MAX_TIME)],
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT),
        ],
    )

    class Meta:
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        ordering = ('recipe',)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]

    def __str__(self):
        return f'{self.amount} {self.ingredient}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='user_shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
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

    def __str__(self):
        return f'Рецепт - {self.recipe.name}, добавлен в корзину'


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='user_favorite',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='in_user_favorite',
    )

    class Meta:
        default_related_name = 'favorites'
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe_model',
            )
        ]

    def __str__(self):
        return f'Рецепт - {self.recipe.name}, добавлен в избранное'
