from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from django.contrib.auth import get_user_model
from api.permissions import is_user_admin
from django.db.models import Prefetch

User = get_user_model()


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'game', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if is_user_admin(request):
                self.fields['cart'].queryset = Cart.objects.all()
            else:
                self.fields['cart'].queryset = Cart.objects.filter(user=request.user)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_amount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and not is_user_admin(request):
            self.fields['user'].queryset = User.objects.filter(id=request.user.id)

    def get_total_amount(self, obj):
        items = getattr(obj, 'items', None)
        if items is None:
            return 0
        if hasattr(items, 'all'):
            items = items.all()
        
        # Calculate total based on game price. 
        # Note: If you want discounts to apply in the cart, subtract item.game.discount here.
        return round(sum(item.game.price * item.quantity for item in items), 2)


class OrderItemSerializer(serializers.ModelSerializer):
    game_title = serializers.CharField(source="game.title", read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'game', 'game_title', 'price_at_purchase', 'quantity']
        read_only_fields = ['price_at_purchase']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    status = serializers.CharField(read_only=False, required=False)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'total_amount', 'status', 'created_at', 'updated_at']
        read_only_fields = ['total_amount', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if not is_user_admin(request):
                self.fields['user'].read_only = True
                self.fields['status'].read_only = True
            else:
                self.fields['user'].queryset = User.objects.all()
                self.fields['user'].read_only = False
                self.fields['status'].read_only = False

    def create(self, validated_data):
        request = self.context['request']
        request_user = request.user

        if is_user_admin(request):
            order_user = validated_data.get('user')
            if not order_user:
                raise serializers.ValidationError({"user": "User is required for admin orders."})
        else:
            order_user = request_user

        try:
            cart = Cart.objects.prefetch_related(
                Prefetch('items', queryset=CartItem.objects.select_related('game'))
            ).get(user=order_user)
        except Cart.DoesNotExist:
            raise serializers.ValidationError({"cart": "No cart found for this user."})

        cart_items = cart.items.all()
        if not cart_items.exists():
            raise serializers.ValidationError({"cart": "No items in cart to place an order."})

        # Create the Order placeholder
        order = Order.objects.create(user=order_user, total_amount=0)
        
        total_amount = 0
        for item in cart_items:
            # Calculate final price. If your discount is a flat amount, you can do: 
            # final_price = item.game.price - (item.game.discount or 0)
            # We default to game.price here to ensure type safety.
            final_price = item.game.price 
            
            OrderItem.objects.create(
                order=order,
                game=item.game,
                quantity=item.quantity,
                price_at_purchase=final_price
            )
            total_amount += final_price * item.quantity

        order.total_amount = total_amount
        order.save()

        # Clear the cart after successful order creation
        cart.delete()
        return order

    def update(self, instance, validated_data):
        request = self.context['request']
        if not is_user_admin(request):
            # Non-admins cannot update the status
            validated_data.pop('status', None)
        return super().update(instance, validated_data)