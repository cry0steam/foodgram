from django.db.models import Sum
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404

# from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.pagination import PageLimitPaginator

from .models import (
    FavoriteRecipe,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from .permissions import AdminOrReadOnly, AuthorOrAdminOrReadOnly
from .serializers import (
    CreateRecipeSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None
    # filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None
    http_method_names = [
        'get',
    ]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related(
        'recipe_ingredients__ingredient',
        'tags',
    )
    serializer_class = CreateRecipeSerializer
    pagination_class = PageLimitPaginator
    # filter_backends = (DjangoFilterBackend,)
    # filterset_class = RecipeFilterSet
    permission_classes = [AuthorOrAdminOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(
        detail=True,
        methods=['GET'],
        url_path='get-link',
        permission_classes=[permissions.AllowAny],
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        short_link = request.build_absolute_uri(recipe.get_short_url())
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = ShoppingCartSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Рецепт отсутствует в корзине пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Рецепт был успешно удалён из корзины.'},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Список покупок"""
        user = request.user
        recipes_in_cart = ShoppingCart.objects.filter(user=user).values_list(
            'recipe', flat=True
        )
        ingredients = (
            IngredientRecipe.objects.filter(recipe__in=recipes_in_cart)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )
        response_content = '\n'.join(
            f'{item["ingredient__name"]}'
            f'({item["ingredient__measurement_unit"]}) - '
            f'{item["total_amount"]}'
            for item in ingredients
        )
        response = HttpResponse(response_content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Избранные рецепты"""
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = FavoriteSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Удаление рецепта из избранного"""
        recipe = get_object_or_404(Recipe, id=pk)
        favorite_item_deleted, _ = FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not favorite_item_deleted:
            return Response(
                {'detail': 'Рецепт не найден в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Рецепт был успешно удалён из избранного.'},
            status=status.HTTP_204_NO_CONTENT,
        )
