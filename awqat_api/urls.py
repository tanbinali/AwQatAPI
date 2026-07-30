from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework_nested import routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from debug_toolbar.toolbar import debug_toolbar_urls

# Import views from your apps
from games.views import CategoryViewSet, GameViewSet, ReviewViewSet

# Schema view configuration for Swagger and Redoc API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="AwQat Gamestore API",
        default_version='v1',
        description="API documentation for the AwQat Gamestore application.",
        contact=openapi.Contact(email="admin@awqat.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Main router for registering top-level viewsets
router = routers.DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'games', GameViewSet, basename='games')
router.register(r'reviews', ReviewViewSet, basename='reviews')

# Nested routes for games under categories
category_router = routers.NestedDefaultRouter(router, r'categories', lookup='category')
category_router.register(r'games', GameViewSet, basename='category-games')

# Nested routes for reviews under games
game_router = routers.NestedDefaultRouter(router, r'games', lookup='game')
game_router.register(r'reviews', ReviewViewSet, basename='game-reviews')

urlpatterns = [
    # Admin site URL
    path('admin/', admin.site.urls),

    # Swagger/OpenAPI schema and UI endpoints
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Authentication endpoints using Djoser (including JWT)
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    
    # API endpoints from the main and nested routers
    path('api/', include(router.urls)),
    path('api/', include(category_router.urls)),
    path('api/', include(game_router.urls)),

] + debug_toolbar_urls()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)