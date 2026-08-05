from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Prefetch
from drf_yasg.utils import swagger_auto_schema
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer
from api.permissions import IsCartOwnerOrAdmin, IsOwnerOrAdmin, is_user_admin, CacheUserAdminMixin

class CartViewSet(viewsets.ModelViewSet):
    """
    Cart ViewSet:
    - Admins can manage all carts.
    - Regular users can only ever have ONE cart.
      -> If they already have one, return it.
      -> If they don’t, create it automatically.
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    @swagger_auto_schema(
        operation_summary="List carts",
        operation_description="Admins see all carts. Regular users always see exactly one cart (auto-created if missing).",
        responses={200: CartSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        if is_user_admin(request):
            return super().list(request, *args, **kwargs)

        # For normal users: ensure they always have one cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response([serializer.data], status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Retrieve a cart",
        operation_description="Admins can retrieve any cart by ID. Regular users can only access their own cart.",
        responses={200: CartSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a cart",
        operation_description="Create a new cart. Non-admin users will receive their existing cart if they already have one.",
        request_body=CartSerializer,
        responses={
            200: CartSerializer(),
            201: CartSerializer(),
            400: 'Cart already exists for this user (Admin only).'
        }
    )
    def create(self, request, *args, **kwargs):
        if is_user_admin(request):
            target_user_id = request.data.get('user', request.user.id)
            
            if Cart.objects.filter(user_id=target_user_id).exists():
                return Response(
                    {"detail": "A cart already exists for this user."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            return super().create(request, *args, **kwargs)

        user = request.user
        cart, created = Cart.objects.get_or_create(user=user)
        serializer = self.get_serializer(cart)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    @swagger_auto_schema(
        operation_summary="Update a cart",
        operation_description="Update an existing cart.",
        request_body=CartSerializer,
        responses={200: CartSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update a cart",
        operation_description="Partially update fields of a cart.",
        request_body=CartSerializer,
        responses={200: CartSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a cart",
        operation_description="Delete a cart by ID.",
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Cart.objects.none()

        qs = Cart.objects.all()
        if not is_user_admin(self.request):
            qs = qs.filter(user=self.request.user)

        return qs.select_related('user').prefetch_related(
            'user__groups',
            Prefetch('items', queryset=CartItem.objects.select_related('game').order_by('id'))
        ).order_by('id')

class CartItemViewSet(CacheUserAdminMixin, viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsCartOwnerOrAdmin]

    @swagger_auto_schema(
        operation_summary="List cart items",
        operation_description="Retrieve all items of a specific cart.",
        responses={200: CartItemSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a cart item",
        operation_description="Get details of a cart item by ID.",
        responses={200: CartItemSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a cart item",
        operation_description="Add a new item to a specific cart.",
        request_body=CartItemSerializer,
        responses={
            201: CartItemSerializer(),
            403: 'Forbidden if user does not own the cart.',
            404: 'Cart not found.'
        }
    )
    def create(self, request, *args, **kwargs):
        cart_pk = self.kwargs.get('cart_pk')
        try:
            cart = Cart.objects.get(pk=cart_pk)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        if not is_user_admin(request) and cart.user != request.user:
            return Response({"detail": "Not allowed to modify this cart."}, status=status.HTTP_403_FORBIDDEN)

        game_id = request.data.get('game')
        quantity = int(request.data.get('quantity', 1))

        if not game_id:
            return Response({"game": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(cart=cart, game_id=game_id, defaults={'quantity': quantity})
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Update a cart item",
        operation_description="Update an existing cart item.",
        request_body=CartItemSerializer,
        responses={200: CartItemSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update a cart item",
        operation_description="Partially update fields of a cart item.",
        request_body=CartItemSerializer,
        responses={200: CartItemSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a cart item",
        operation_description="Delete a cart item by ID.",
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
        cart_pk = self.kwargs.get('cart_pk')
        queryset = CartItem.objects.filter(cart_id=cart_pk).select_related('cart', 'game')
        if not is_user_admin(self.request):
            queryset = queryset.filter(cart__user=self.request.user)
        return queryset.order_by('id')


class OrderViewSet(CacheUserAdminMixin, viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List orders",
        operation_description="Retrieve orders. Admins see all; clients see only their orders.",
        responses={200: OrderSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve an order",
        operation_description="Get details of an order by ID.",
        responses={200: OrderSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create an order",
        operation_description="Create a new order.",
        request_body=OrderSerializer,
        responses={201: OrderSerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update an order",
        operation_description="Update an existing order. Clients cannot update order status.",
        request_body=OrderSerializer,
        responses={200: OrderSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update an order",
        operation_description="Partially update fields of an order.",
        request_body=OrderSerializer,
        responses={200: OrderSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete an order",
        operation_description="Delete an order by ID.",
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        request = self.request
        if is_user_admin(request):
            return Order.objects.all().select_related('user').prefetch_related(
                'user__groups',
                Prefetch('items', queryset=OrderItem.objects.select_related('game').order_by('id'))
            ).order_by('id')
        return Order.objects.filter(user=request.user).select_related('user').prefetch_related(
            'user__groups',
            Prefetch('items', queryset=OrderItem.objects.select_related('game').order_by('id'))
        ).order_by('id')

    def perform_update(self, serializer):
        if is_user_admin(self.request):
            serializer.save()
        else:
            validated_data = dict(serializer.validated_data)
            validated_data.pop('status', None)
            serializer.save(**validated_data)


class OrderItemViewSet(CacheUserAdminMixin, viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    @swagger_auto_schema(
        operation_summary="List order items",
        operation_description="Retrieve all items belonging to a specific order.",
        responses={200: OrderItemSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve an order item",
        operation_description="Get details of an order item by ID.",
        responses={200: OrderItemSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create an order item",
        operation_description="Add a new item to a specific order.",
        request_body=OrderItemSerializer,
        responses={
            201: OrderItemSerializer(),
            403: 'Forbidden if user does not own the order.',
            404: 'Order not found.'
        }
    )
    def create(self, request, *args, **kwargs):
        order_pk = self.kwargs.get('order_pk')
        try:
            order = Order.objects.get(pk=order_pk)
        except Order.DoesNotExist:
            raise PermissionDenied("Order not found.")

        if order.user != request.user and not is_user_admin(request):
            raise PermissionDenied("You cannot add items to this order.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(order=order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Update an order item",
        operation_description="Update an existing order item.",
        request_body=OrderItemSerializer,
        responses={200: OrderItemSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update an order item",
        operation_description="Partially update fields of an order item.",
        request_body=OrderItemSerializer,
        responses={200: OrderItemSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete an order item",
        operation_description="Delete an order item by ID.",
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return OrderItem.objects.none()
        order_pk = self.kwargs.get('order_pk')
        queryset = OrderItem.objects.filter(order_id=order_pk).select_related('order', 'game', 'order__user')
        if not is_user_admin(self.request):
            queryset = queryset.filter(order__user=self.request.user)
        return queryset.order_by('id')