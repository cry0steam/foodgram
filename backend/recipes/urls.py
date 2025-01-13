from django.urls import include, path
from rest_framework import routers

from .views import IngredientViewSet, TagViewSet

router = routers.DefaultRouter()
router.register(r'ingredients', IngredientViewSet)
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
