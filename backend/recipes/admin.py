from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from users.models import Subscription

from .models import (
    FavoriteRecipe,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
        'favorite_count',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email')

    @admin.display(description='Кол-во добавлений в Избранное')
    def favorite_count(self, obj):
        return obj.favorite_set.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscriber', 'author')
    search_fields = ('subcriber', 'author')
    list_filter = ('subscriber', 'author')

    def save_model(self, request, obj, form, change):
        if obj.user == obj.author:
            raise ValueError('Нельзя подписаться на самого себя')
        super().save_model(request, obj, form, change)


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('name', 'slug')
    list_display = ('id', 'name', 'slug')
    list_display_links = ('id', 'name')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('id', 'name')
    list_filter = ('measurement_unit',)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('id', 'author', 'name', 'image', 'text')
    list_display_links = ('id', 'name')
    inlines = [
        IngredientRecipeInline,
    ]

    def save_model(self, request, obj, form, change):
        if not obj.recipeingredient_set.exists():
            raise ValueError('Рецепт должен иметь хотя бы один ингредиент')
        super().save_model(request, obj, form, change)


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'amount')
