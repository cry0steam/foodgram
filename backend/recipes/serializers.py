from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from users.models import Subscription
from users.serializers import CustomUserSerializer

from .models import (
    FavoriteRecipe,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = IngredientRecipe
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount',
        ]


class IngrediendRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Ингредиентов не может быть меньше одного'
            )
        return value


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class BaseRecipeSerializer(ShortRecipeSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        source='recipe_ingredients',
        many=True,
    )

    class Meta(ShortRecipeSerializer.Meta):
        fields = ShortRecipeSerializer.Meta.fields + [
            'author',
            'text',
            'ingredients',
            'tags',
        ]


class FullRecipeSerializer(BaseRecipeSerializer):
    tags = TagSerializer(read_only=True, many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta(BaseRecipeSerializer.Meta):
        fields = BaseRecipeSerializer.Meta.fields + [
            'is_in_shopping_cart',
            'is_favorited',
        ]

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shopping_cart.filter(user=request.user).exists()
        return False

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False


class CreateRecipeSerializer(BaseRecipeSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = IngrediendRecipeWriteSerializer(many=True)
    image = Base64ImageField()

    @staticmethod
    def create_ingredient_in_recipe(instance, ingredients):
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    recipe=instance,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'],
                )
                for ingredient in ingredients
            ]
        )

    def validate(self, attrs):
        if not attrs.get('image'):
            raise serializers.ValidationError(
                {'image': 'This field is required.'},
            )
        return attrs

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше единицы'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым'
            )
        # Check for duplicate ingredient ids
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Ингредиенты не могут повторяться')
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Список тегов не может быть пустым')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не могут повторяться')
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        user = self.context.get('request').user
        instance = Recipe.objects.create(**validated_data, author=user)
        instance.tags.set(tags)
        self.create_ingredient_in_recipe(instance, ingredients)
        return instance

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        instance.tags.set(tags)
        self.create_ingredient_in_recipe(instance, ingredients)
        return super().update(instance, validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        if user.shopping_cart.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError('Уже в корзине.')
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(ShoppingCartSerializer):
    class Meta(ShoppingCartSerializer.Meta):
        model = FavoriteRecipe

    def validate(self, data):
        user = data['user']
        if user.favorites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError('Уже добавлен в избранные.')
        return data


class SubscriberDetailSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = CustomUserSerializer.Meta.fields + (
            'recipes_count',
            'recipes',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        queryset = Recipe.objects.filter(author=obj)
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        try:
            if recipes_limit is not None:
                recipes_limit = int(recipes_limit)
                if recipes_limit > 0:
                    queryset = queryset[:recipes_limit]
        except (ValueError, TypeError):
            pass

        return ShortRecipeSerializer(
            queryset,
            many=True,
            context=self.context,
        ).data


class SubscriberCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('subscriber', 'author')

    def validate(self, data):
        subscriber = data['subscriber']
        author = data['author']
        if subscriber == author:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        if Subscription.objects.filter(
            subscriber=subscriber,
            author=author,
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного пользователя.'
            )

        return data

    def to_representation(self, instance):
        return SubscriberDetailSerializer(
            instance.author,
            context=self.context,
        ).data
