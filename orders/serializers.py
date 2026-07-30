from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem

class CartItemSerializer(serializers.ModelSerializer):
    game_title = serializers.ReadOnlyField(source='game.title')
    game_price = serializers.ReadOnlyField(source='game.price')
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'game', 'game_title', 'game_price', 'quantity', 'subtotal']

    def get_subtotal(self, obj):
        return obj.quantity * getattr(obj.game, 'price', 0)

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total', 'created_at', 'updated_at']
        read_only_fields = ['user']

    def get_total(self, obj):
        return sum(item.quantity * getattr(item.game, 'price', 0) for item in obj.items.all())

class OrderItemSerializer(serializers.ModelSerializer):
    game_title = serializers.ReadOnlyField(source='game.title')

    class Meta:
        model = OrderItem
        fields = ['id', 'game', 'game_title', 'quantity', 'price_at_purchase']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_amount', 'status', 'items', 'created_at', 'updated_at']
        read_only_fields = ['user', 'total_amount', 'status', 'created_at']