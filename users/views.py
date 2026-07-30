from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .models import Profile
from .serializers import CustomUserSerializer, ProfileSerializer

User = get_user_model()

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    # This viewset is strictly for listing users outside of Djoser's auth flow
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAdminUser]

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Profile.objects.all()
        return Profile.objects.filter(user=self.request.user)

    def get_object(self):
        # Checks if the URL is missing a primary key or explicitly requests 'me'
        if not self.kwargs.get('pk') or self.kwargs.get('pk') == 'me':
            profile, created = Profile.objects.get_or_create(user=self.request.user)
            return profile
        return super().get_object()