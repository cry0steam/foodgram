from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .filters import RecipeFilter
from .pagination import PageLimitPaginator
from .permissions import AuthorOrAdminOrReadOnly
from .serializers import (
    AvatarSerializer,
    CreateRecipeSerializer,
    CustomUserSerializer,
    FavoriteSerializer,
    FullRecipeSerializer,
    IngredientSerializer,
    ShoppingCartSerializer,
    SubscriberCreateSerializer,
    SubscriberDetailSerializer,
    TagSerializer,
)
from recipes.models import (
    Ingredient,
    IngredientRecipe,
    Recipe,
    Tag,
)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]
    pagination_class = PageLimitPaginator

    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = CustomUserSerializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['PUT'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def set_avatar(self, request):
        serializer = AvatarSerializer(
            instance=request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete()
        request.user.save()
        return Response(
            {'message': 'Фото успешно удалено.'},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(author__subscriber=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriberDetailSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
    )
    def subscribe(self, request, id=None):
        user_to_sub = get_object_or_404(User, id=id)
        serializer = SubscriberCreateSerializer(
            data={'subscriber': request.user.id, 'author': user_to_sub.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def remove_subscription(self, request, id=None):
        user_to_follow = get_object_or_404(User, id=id)
        deleted_count, _ = request.user.subscriber.filter(
            author=user_to_follow
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Вы не подписаны на данного пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'ingredients',
        'tags',
    )
    pagination_class = PageLimitPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [AuthorOrAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return FullRecipeSerializer
        return CreateRecipeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        read_serializer = FullRecipeSerializer(
            recipe, context=self.get_serializer_context()
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        updated_recipe = serializer.save()

        read_serializer = FullRecipeSerializer(
            updated_recipe, context=self.get_serializer_context()
        )
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = reverse('short_url', kwargs={'pk': recipe.pk})
        return Response(
            {'short-link': request.build_absolute_uri(short_link)},
            status=status.HTTP_200_OK,
        )

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
        deleted_count, _ = request.user.user_shopping_cart.filter(
            recipe=recipe
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
        recipes_in_cart = user.user_shopping_cart.values_list(
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
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
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
        favorite_item_deleted, _ = request.user.user_favorite.filter(
            recipe=recipe
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


@require_GET
def short_url(request, pk):
    if not Recipe.objects.filter(pk=pk).exists():
        raise ValidationError(f'Рецепт {pk} не существует.')
    return redirect(f'/recipes/{pk}/')
