from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import User, Profile
from api.permissions import is_user_admin

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    avatar = serializers.ImageField(required=False)
    order_history = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'email',
            'full_name', 'phone_number', 'address',
            'avatar', 'bio', 'date_of_birth',
            'order_history'
        ]
        read_only_fields = ['id', 'username', 'email', 'order_history']

    def get_order_history(self, obj):
        orders = getattr(obj.user, 'order_set', None) or getattr(obj.user, 'orders', None)
        if orders is None:
            return []

        history = []
        for order in orders.all():
            games_list = []
            items = getattr(order, 'items', None) or getattr(order, 'order_items', None)
            
            if items is not None:
                for item in items.all():
                    games_list.append({
                        "game_id": item.game.id,
                        "title": item.game.title,
                        "price_at_purchase": getattr(item, 'price_at_purchase', 0),
                        "quantity": item.quantity,
                    })
            
            history.append({
                "order_id": order.id,
                "order_status": order.status,
                "total_price": order.total_amount,
                "ordered_at": order.created_at,
                "games": games_list,
            })
        return history


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model including nested profile information 
    and admin-restricted group modification.

    Fields:
        - id (int): User ID (read-only)
        - email (str): User's email
        - username (str): Username
        - profile (ProfileSerializer): Nested read-only profile information
        - groups (list[str]): List of group names. Editable only by admin users.

    Permissions:
        - Only admin users (is_staff=True) can modify the 'groups' field.
        - Other fields can be updated by authorized users as usual.
    """
    profile = ProfileSerializer(read_only=True)
    
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'username','is_active','profile', 'groups']

    def update(self, instance, validated_data):
        """
        Update a user instance.

        Admin-only group update logic:
            - If 'groups' is in the request, check if the request user is admin.
            - If not admin, raise a ValidationError.
            - If admin, update the user's groups.

        Other fields are updated normally.
        """
        request = self.context.get('request')
        groups = validated_data.pop('groups', None)
        
        is_staff_or_admin = request.user.is_staff or is_user_admin(request)

        if groups is not None:
            if not is_staff_or_admin:
                raise serializers.ValidationError({
                    "groups": "You do not have permission to change user groups."
                })
            instance.groups.set(groups)

        if 'is_active' in validated_data:
            if not is_staff_or_admin:
                validated_data.pop('is_active')

        return super().update(instance, validated_data)


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new User.

    Fields:
        - id (int): Unique identifier (read-only).
        - email (str): Email address.
        - username (str): Username.
        - password (str): Write-only password field.

    Behavior:
        - Uses `create_user` to hash passwords before saving.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
        )
        user.is_active = False
        user.save()
        return user