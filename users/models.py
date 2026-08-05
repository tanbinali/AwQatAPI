from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from cloudinary.models import CloudinaryField


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    is_customer = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email or self.username


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True)
    avatar = CloudinaryField('image', blank=True, null=True, resource_type='image', folder='users/avatars/')
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"