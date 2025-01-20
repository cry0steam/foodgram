from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.serializers import (
    SubscriberCreateSerializer,
    SubscriberDetailSerializer,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import Subscription

from .pagination import PageLimitPaginator
from .serializers import (
    AvatarSerializer,
    CustomUserSerializer,
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
        deleted_count, _ = Subscription.objects.filter(
            subscriber=request.user, author=user_to_follow
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Вы не подписаны на данного пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
