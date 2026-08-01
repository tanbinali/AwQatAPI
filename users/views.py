from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Prefetch
from drf_yasg.utils import swagger_auto_schema

from .models import User, Profile
from orders.models import Order, OrderItem
from .serializers import UserSerializer, ProfileSerializer, UserCreateSerializer
from api.permissions import IsAdminUser, IsOwnerOrAdmin


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('profile').prefetch_related('groups').order_by('id')
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_permissions(self):
        if getattr(self, 'swagger_fake_view', False):
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'profile':
            return ProfileSerializer
        return UserSerializer

    @swagger_auto_schema(
        operation_summary="List all users",
        operation_description="Retrieve a paginated list of all users in the system. Only accessible by admin users.",
        responses={200: UserSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a user by ID",
        operation_description="Fetch detailed information about a user specified by their ID. Includes related profile and group information.",
        responses={200: UserSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new user",
        operation_description="Create a new user account. Required fields: username, email, password.",
        request_body=UserCreateSerializer,
        responses={201: UserSerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a user (full update)",
        operation_description="Update all fields of an existing user. Only admins can modify groups.",
        request_body=UserSerializer,
        responses={200: UserSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a user",
        operation_description="Update one or more fields of an existing user. Only admins can modify groups.",
        request_body=UserSerializer,
        responses={200: UserSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a user",
        operation_description="Delete a user by ID. Admins can delete without password verification.",
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if request.user.is_staff:
            self.perform_destroy(user)
            return Response({"detail": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        current_password = request.data.get("current_password")
        if not current_password or not request.user.check_password(current_password):
            return Response(
                {"current_password": ["This field is required or incorrect."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(user)
        return Response({"detail": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method='get',
        operation_summary="Retrieve a user's profile",
        operation_description="Get the profile associated with a specific user. Accessible by the user or admins.",
        responses={200: ProfileSerializer()}
    )
    @swagger_auto_schema(
        method='put',
        operation_summary="Update a user's profile (full update)",
        operation_description="Fully update a user's profile.",
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer()}
    )
    @swagger_auto_schema(
        method='patch',
        operation_summary="Partially update a user's profile",
        operation_description="Partially update fields of a user's profile.",
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer()}
    )
    @swagger_auto_schema(
        method='delete',
        operation_summary="Delete a user's profile",
        operation_description="Delete the specified profile.",
        responses={204: 'No Content'}
    )
    @action(
        detail=True,
        methods=['get', 'put', 'patch', 'delete'],
        permission_classes=[IsAuthenticated, IsOwnerOrAdmin],
        serializer_class=ProfileSerializer
    )
    def profile(self, request, pk=None):
        user = self.get_object()
        profile = getattr(user, 'profile', None)
        if not profile:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(profile, data=request.data, partial=(request.method == 'PATCH'))
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        elif request.method == 'DELETE':
            profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all().select_related("user")
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_summary="List all profiles",
        operation_description="Retrieve all user profiles. Restricted to admins.",
        responses={200: ProfileSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a profile by ID",
        operation_description="Get profile details by ID. Restricted to admins.",
        responses={200: ProfileSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new profile",
        operation_description="Create a user profile.",
        request_body=ProfileSerializer,
        responses={201: ProfileSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a profile by ID",
        operation_description="Update all profile fields.",
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a profile",
        operation_description="Delete a profile by ID.",
        responses={
            204: 'No Content',
            404: 'Not Found',
            403: 'Forbidden',
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a profile by ID",
        operation_description="Partially update fields of a profile.",
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer()},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        method='get',
        operation_summary="Retrieve your own profile",
        operation_description="Clients can retrieve their profile and order history.",
        responses={200: ProfileSerializer()},
    )
    @swagger_auto_schema(
        method='put',
        operation_summary="Update your own profile",
        operation_description="Fully update your profile.",
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer()},
    )
    @swagger_auto_schema(
        method='patch',
        operation_summary="Partially update your own profile",
        operation_description="Partially update your profile.",
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer()},
    )
    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me', permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        profile_qs = (
            Profile.objects
            .select_related('user')
            .prefetch_related(
                Prefetch(
                    'user__orders',
                    queryset=Order.objects.prefetch_related(
                        Prefetch(
                            'items',
                            queryset=OrderItem.objects.select_related('game')
                        )
                    ).order_by('-created_at')
                )
            )
        )

        try:
            profile = profile_qs.get(user=request.user)
        except Profile.DoesNotExist:
            return Response({'detail': 'Profile not found.'}, status=404)

        if request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(profile, data=request.data, partial=(request.method == 'PATCH'))
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = self.get_serializer(profile)
        return Response(serializer.data)