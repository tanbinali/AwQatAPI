from rest_framework import viewsets, filters, permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Avg
from drf_yasg.utils import swagger_auto_schema
from .models import Category, Game, Review
from .serializers import CategorySerializer, GameSerializer, ReviewSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [permissions.AllowAny()]

class GameViewSet(viewsets.ModelViewSet):
    serializer_class = GameSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'average_rating', 'active', 'created_at']
    ordering = ['-average_rating', 'id']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        elif self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAuthenticated()]

    @swagger_auto_schema(
        operation_summary="List all games",
        operation_description="Retrieve a list of all games with optional search and ordering.",
        responses={200: GameSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific game",
        operation_description="Get detailed information about a specific game by ID.",
        responses={200: GameSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new game",
        operation_description="Create a new game. Requires admin access.",
        request_body=GameSerializer,
        responses={201: GameSerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Game.objects.none()
        
        category_pk = self.kwargs.get('category_pk')
        qs = Game.objects.select_related('category').prefetch_related('images').annotate(
            average_rating=Avg('reviews__rating')
        )
        
        if category_pk:
            qs = qs.filter(category_id=category_pk, active=True)
            
        return qs.order_by('-average_rating', 'id')

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
            
        game_pk = self.kwargs.get('game_pk')
        if game_pk:
            return Review.objects.filter(game_id=game_pk)
        return Review.objects.all()

    def perform_create(self, serializer):
        game_id = self.kwargs.get('game_pk')
        if game_id:
            serializer.save(user=self.request.user, game_id=game_id)
        else:
            serializer.save(user=self.request.user)