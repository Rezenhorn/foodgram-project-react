from django.contrib.auth import get_user_model
from django.core.files import File
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (FavoriteRecipe, Ingredients, RecipeInShoppingCart,
                            Recipes, Tags)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                     ReadOnlyModelViewSet)
from users.models import Subscription

from .filters import RecipeFilter
from .permissions import AdminOwnerOrReadOnly
from .serializers import (IngredientSerializer, RecipeSerializer,
                          ShortRecipeSerializer, SubscriptionSerializer,
                          TagSerializer)

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ("^name",)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipes.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter
    permission_classes = (AdminOwnerOrReadOnly,)

    @action(detail=True,
            methods=["post", "delete"],
            url_path="favorite",
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipes, pk=pk)
        serializer = ShortRecipeSerializer(recipe)
        user = request.user
        favorite_recipe = FavoriteRecipe.objects.filter(user=user,
                                                        recipe=recipe)
        if request.method == "DELETE":
            if favorite_recipe.exists():
                favorite_recipe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data={"error": "This recipe is not in your favorite list"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if favorite_recipe.exists():
            return Response(
                data={"error": "This recipe is already your favorite one"},
                status=status.HTTP_400_BAD_REQUEST
            )
        FavoriteRecipe.objects.create(user=user, recipe=recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True,
            methods=["post", "delete"],
            url_path="shopping_cart",
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipes, pk=pk)
        serializer = ShortRecipeSerializer(recipe)
        user = request.user
        cart_recipe = RecipeInShoppingCart.objects.filter(user=user,
                                                          recipe=recipe)
        if request.method == "DELETE":
            if cart_recipe.exists():
                cart_recipe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data={"error": "This recipe is not in your shopping cart"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if cart_recipe.exists():
            return Response(
                data={"error": "This recipe is already in your shopping cart"},
                status=status.HTTP_400_BAD_REQUEST
            )
        RecipeInShoppingCart.objects.create(user=user, recipe=recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False,
            methods=["get"],
            url_path="download_shopping_cart",
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        with open("shopping_list.txt", "w", encoding="utf-8") as file:
            myfile = File(file)
            shopping_list = dict()

            for ingredient in request.user.cart_user.values_list(
                    "recipe__recipeingredient__ingredient__name",
                    "recipe__recipeingredient__ingredient__measurement_unit",
                    "recipe__recipeingredient__amount"):
                if ingredient[0] not in shopping_list:
                    shopping_list[ingredient[0]] = [ingredient[1],
                                                    ingredient[2]]
                else:
                    shopping_list[ingredient[0]][1] += ingredient[2]
            for ingredient in shopping_list:
                myfile.write(f"{ingredient} ({shopping_list[ingredient][0]}) "
                             f"— {shopping_list[ingredient][1]}\n")
            myfile.write("______________________________\n"
                         "Продуктовый помощник Foodgram")
        with open("shopping_list.txt", "r", encoding="utf-8") as file:
            response = HttpResponse(
                file, content_type="text/plain; charset=utf-8"
            )
            response["Content-Disposition"] = ("attachment;"
                                               " filename='shopping_cart.txt'")
            return response


class SubscribtionViewSet(GenericViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)

    @action(detail=False,
            methods=["get"],
            url_path="subscriptions")
    def subscribtions(self, request):
        page = self.paginate_queryset(self.get_queryset())
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=True,
            methods=["post", "delete"],
            url_path="subscribe")
    def subscribe(self, request, pk):
        user = request.user
        user_to_follow = get_object_or_404(User, pk=pk)
        subscription = Subscription.objects.filter(user=user,
                                                   author=user_to_follow)
        if request.method == "DELETE":
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(data={"error": "Subscription doesn't exist"},
                            status=status.HTTP_400_BAD_REQUEST)
        if user == user_to_follow:
            return Response(data={"error": "You can't subscribe to yourself"},
                            status=status.HTTP_400_BAD_REQUEST)
        if subscription.exists():
            return Response(
                data={"error": "You've already subscribed to this user"},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription = Subscription.objects.create(user=user,
                                                   author=user_to_follow)
        serializer = self.get_serializer(subscription.author)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)