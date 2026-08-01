from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from .models import Category, Game, Review
from .serializers import CategorySerializer, GameSerializer, ReviewSerializer
from api.permissions import IsAdminUser, IsOwnerOrAdmin
from django.db.models import Avg, Prefetch


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('id').prefetch_related(
        Prefetch(
            'games',
            queryset=Game.objects.annotate(avg_rating=Avg('reviews__rating')).order_by('id'),
            to_attr='prefetched_games'
        )
    )
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'games']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_summary="List all categories",
        operation_description="Retrieve a list of all game categories. Publicly accessible.",
        responses={200: CategorySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific category by ID",
        operation_description="Get detailed information about a specific category.",
        responses={200: CategorySerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new category",
        operation_description="Create a new category. Requires admin authentication.",
        request_body=CategorySerializer,
        responses={201: CategorySerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update an existing category (full update)",
        operation_description="Update all fields of a category. Requires admin authentication.",
        request_body=CategorySerializer,
        responses={200: CategorySerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update of a category",
        operation_description="Update one or more fields of a category. Requires admin authentication.",
        request_body=CategorySerializer,
        responses={200: CategorySerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a category",
        operation_description="Delete a category by ID. Requires admin authentication.",
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="List active games under a category",
        operation_description=(
            "Retrieve all active games associated with the specified category. "
            "If no active games exist, returns an empty list."
        ),
        responses={200: GameSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def games(self, request, pk=None):
        category = self.get_object()
        # Get only active games that were prefetched
        games = getattr(category, 'prefetched_games', [])
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)


class GameViewSet(viewsets.ModelViewSet):
    serializer_class = GameSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'average_rating', 'active', 'discount']
    ordering = ['-average_rating']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        elif self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAuthenticated()]

    @swagger_auto_schema(
        operation_summary="List all games",
        operation_description="Retrieve a list of all games with optional search and ordering. Publicly accessible.",
        responses={200: GameSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific game by ID",
        operation_description="Get detailed information about a specific game.",
        responses={200: GameSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new game",
        operation_description="Create a new game. Requires admin authentication.",
        request_body=GameSerializer,
        responses={201: GameSerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a game (full update)",
        operation_description="Update all fields of an existing game. Requires admin authentication.",
        request_body=GameSerializer,
        responses={200: GameSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update a game",
        operation_description="Update one or more fields of a game. Requires admin authentication.",
        request_body=GameSerializer,
        responses={200: GameSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a game",
        operation_description="Delete a game by ID. Requires admin authentication.",
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Game.objects.none()
        category_pk = self.kwargs.get('category_pk')
        qs = Game.objects.select_related('category').annotate(
            average_rating=Avg('reviews__rating')
        )
        if category_pk:
            qs = qs.filter(category_id=category_pk, active=True)
        return qs.order_by('-average_rating', 'id')

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['rating', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        
        queryset = Review.objects.all().order_by('-created_at')
        game_pk = self.kwargs.get('game_pk')
        
        if game_pk:
            queryset = queryset.filter(game_id=game_pk)
            
        return queryset

    def perform_create(self, serializer):
        game_pk = self.kwargs.get('game_pk')
        if game_pk:
            serializer.save(user=self.request.user, game_id=game_pk)
        else:
            serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="List reviews",
        operation_description="Retrieve a list of reviews. If accessed via a specific game URL, it filters reviews for that game. Publicly accessible.",
        responses={200: ReviewSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific review",
        operation_description="Get detailed information about a specific review by its ID.",
        responses={200: ReviewSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a review",
        operation_description="Submit a new review. If accessed via a specific game URL, the review links to that game automatically. Requires authentication.",
        request_body=ReviewSerializer,
        responses={201: ReviewSerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a review",
        operation_description="Fully update a review. Only the owner or an admin can perform this action.",
        request_body=ReviewSerializer,
        responses={200: ReviewSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update a review",
        operation_description="Partially update a review. Only the owner or an admin can perform this action.",
        request_body=ReviewSerializer,
        responses={200: ReviewSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a review",
        operation_description="Delete a review. Only the owner or an admin can perform this action.",
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)