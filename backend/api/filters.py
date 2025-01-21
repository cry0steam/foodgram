from django_filters import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart',
    )
    is_favorited = filters.NumberFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart', 'tags']

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=user)
        return queryset


class IngredientFilter(SearchFilter):
    search_param = 'name'
