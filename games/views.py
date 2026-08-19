from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_yasg.utils import swagger_auto_schema
from .models import Category, Studio, Game, Review, GameImage
from .serializers import CategorySerializer, StudioSerializer, GameSerializer, ReviewSerializer, GameImageSerializer
from api.permissions import IsAdminUser, IsOwnerOrAdmin
from django.db.models import Avg, Prefetch, F, ExpressionWrapper, DecimalField

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('id').prefetch_related(
        Prefetch(
            'games',
            queryset=Game.objects.annotate(avg_rating=Avg('reviews__rating')).order_by('id'),
            to_attr='prefetched_games'
        )
    )
    serializer_class = CategorySerializer
    parser_classes = (MultiPartParser, FormParser)
    
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
        games = getattr(category, 'prefetched_games', [])
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)


class StudioViewSet(viewsets.ModelViewSet):
    queryset = Studio.objects.all().order_by('name')
    serializer_class = StudioSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_summary="List all studios",
        operation_description="Retrieve a list of all game studios. Publicly accessible.",
        responses={200: StudioSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific studio by ID",
        operation_description="Get detailed information about a specific studio.",
        responses={200: StudioSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new studio",
        operation_description="Create a new studio. Requires admin authentication.",
        request_body=StudioSerializer,
        responses={201: StudioSerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update an existing studio (full update)",
        operation_description="Update all fields of a studio. Requires admin authentication.",
        request_body=StudioSerializer,
        responses={200: StudioSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update of a studio",
        operation_description="Update one or more fields of a studio. Requires admin authentication.",
        request_body=StudioSerializer,
        responses={200: StudioSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a studio",
        operation_description="Delete a studio by ID. Requires admin authentication.",
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class GameViewSet(viewsets.ModelViewSet):
    serializer_class = GameSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    
    search_fields = ['title', 'description', 'developer']
    ordering_fields = ['price', 'final_price']
    ordering = ['-average_rating']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        elif self.action in ['list', 'retrieve', 'discounted', 'upcoming']:
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

    @swagger_auto_schema(
        operation_summary="List discounted games",
        operation_description="Retrieve a list of active games currently on sale (discount > 0).",
        responses={200: GameSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='discounted')
    def discounted(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(discount__gt=0, active=True)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="List upcoming games",
        operation_description="Retrieve a list of upcoming games (inactive games).",
        responses={200: GameSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(active=False)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Game.objects.none()
            
        category_pk = self.kwargs.get('category_pk')
        discount_calculation = F('price') - (F('price') * F('discount') / 100.0)
        
        qs = Game.objects.select_related('category', 'studio').annotate(
            average_rating=Avg('reviews__rating'),
            final_price=ExpressionWrapper(discount_calculation, output_field=DecimalField(max_digits=10, decimal_places=2))
        )
        
        if category_pk:
            qs = qs.filter(category_id=category_pk, active=True)
            
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        studio_id = self.request.query_params.get('studio')
        category_id = self.request.query_params.get('category')

        if min_price is not None and min_price != '':
            qs = qs.filter(final_price__gte=min_price)
            
        if max_price is not None and max_price != '':
            qs = qs.filter(final_price__lte=max_price)
            
        if studio_id and studio_id != 'All':
            qs = qs.filter(studio_id=studio_id)
            
        if category_id and category_id != 'All':
            qs = qs.filter(category_id=category_id)

        return qs.order_by('-average_rating', 'id')

class GameImageViewSet(viewsets.ModelViewSet):
    queryset = GameImage.objects.all().order_by('-id')
    serializer_class = GameImageSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [permissions.AllowAny()]

    @swagger_auto_schema(
        operation_summary="List all game images",
        operation_description="Retrieve a list of all game images. This endpoint is public.",
        responses={200: GameImageSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a game image",
        operation_description="Get the details of a specific game image by its ID. This endpoint is public.",
        responses={
            200: GameImageSerializer(),
            404: "Not Found. The image does not exist."
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Upload a new game image",
        operation_description="Upload a new image for a game. You must have admin privileges.",
        responses={
            201: GameImageSerializer(),
            400: "Bad Request. Invalid data provided.",
            401: "Unauthorized. Authentication required.",
            403: "Forbidden. Admin privileges required."
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a game image",
        operation_description="Replace an existing game image. You must have admin privileges.",
        responses={
            200: GameImageSerializer(),
            400: "Bad Request. Invalid data provided.",
            401: "Unauthorized. Authentication required.",
            403: "Forbidden. Admin privileges required.",
            404: "Not Found. The image does not exist."
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a game image",
        operation_description="Modify specific fields of an existing game image. You must have admin privileges.",
        responses={
            200: GameImageSerializer(),
            400: "Bad Request. Invalid data provided.",
            401: "Unauthorized. Authentication required.",
            403: "Forbidden. Admin privileges required.",
            404: "Not Found. The image does not exist."
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a game image",
        operation_description="Remove a game image from the database. You must have admin privileges.",
        responses={
            204: "No Content. Successfully deleted.",
            401: "Unauthorized. Authentication required.",
            403: "Forbidden. Admin privileges required.",
            404: "Not Found. The image does not exist."
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


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