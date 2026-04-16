"""orders/views.py"""
import logging
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from core.permissions import IsBuyer, IsSellerOrAdmin, IsAdmin
from .models import Order, OrderItem
from .serializers import OrderSerializer, CheckoutSerializer, OrderStatusUpdateSerializer

logger = logging.getLogger(__name__)


class CheckoutView(APIView):
    """
    Convert cart → Order atomically.
    Decrements stock, creates OrderItems, clears cart.
    """
    permission_classes = [IsBuyer]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        cart = serializer.validated_data['cart']
        cart_items = cart.items.select_related('product').select_for_update()

        # Validate stock for all items before committing
        stock_errors = []
        for item in cart_items:
            if item.quantity > item.product.stock_qty:
                stock_errors.append(
                    f'"{item.product.name}": only {item.product.stock_qty} in stock.'
                )
        if stock_errors:
            return Response(
                {'status': 'error', 'message': 'Stock insufficient.', 'errors': stock_errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total = sum(item.price_at_add * item.quantity for item in cart_items)

        order = Order.objects.create(
            buyer=request.user,
            total_amount=total,
            status='pending',
            shipping_address=serializer.validated_data['shipping_address'],
            notes=serializer.validated_data.get('notes', ''),
            payment_ref=serializer.validated_data.get('payment_ref', ''),
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.price_at_add,
            )
            # Decrement stock
            item.product.stock_qty -= item.quantity
            item.product.save(update_fields=['stock_qty'])

        # Clear cart
        cart.items.all().delete()

        logger.info('Order %s created for buyer %s — total: %s', order.id, request.user.email, total)

        return Response(
            {
                'status': 'success',
                'message': 'Order placed successfully.',
                'data': OrderSerializer(order).data,
            },
            status=status.HTTP_201_CREATED,
        )


class OrderListView(generics.ListAPIView):
    """List all orders for the authenticated buyer."""
    serializer_class = OrderSerializer
    permission_classes = [IsBuyer]

    def get_queryset(self):
        return (
            Order.objects.filter(buyer=self.request.user)
            .prefetch_related('items__product')
            .order_by('-created_at')
        )


class OrderDetailView(generics.RetrieveAPIView):
    """Get a specific order (buyer sees own, admin sees all)."""
    serializer_class = OrderSerializer

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.prefetch_related('items__product').all()
        return Order.objects.filter(buyer=user).prefetch_related('items__product')


class OrderStatusUpdateView(generics.UpdateAPIView):
    """Allow admins/sellers to advance order status."""
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsSellerOrAdmin]
    http_method_names = ['patch']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        # Sellers can only update orders involving their products
        return Order.objects.filter(items__product__seller=user).distinct()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'status': 'success',
            'message': f'Order status updated to "{instance.status}".',
            'data': OrderSerializer(instance).data,
        })
