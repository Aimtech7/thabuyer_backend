"""orders/views.py"""
import logging
import stripe
from django.db import transaction
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core.permissions import IsBuyer, IsSellerOrAdmin, IsAdmin
from .models import Order, OrderItem
from .serializers import OrderSerializer, CheckoutSerializer, OrderStatusUpdateSerializer
from . import shipping

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


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

        total_without_discount = sum(item.price_at_add * item.quantity for item in cart_items)
        discount_amount = 0

        coupon = serializer.validated_data.get('coupon')
        if coupon:
            if coupon.seller_restricted:
                # Only apply to items from this seller
                eligible_total = sum(
                    item.price_at_add * item.quantity 
                    for item in cart_items 
                    if item.product.seller == coupon.seller_restricted
                )
                if coupon.discount_type == 'fixed':
                    discount_amount = min(coupon.discount_amount, eligible_total)
                else:
                    discount_amount = eligible_total * (coupon.discount_amount / 100)
            else:
                # Apply to whole cart
                if coupon.discount_type == 'fixed':
                    discount_amount = min(coupon.discount_amount, total_without_discount)
                else:
                    discount_amount = total_without_discount * (coupon.discount_amount / 100)

            coupon.times_used += 1
            coupon.save(update_fields=['times_used'])

        final_total = total_without_discount - discount_amount

        # Create Stripe PaymentIntent
        if final_total > 0:
            intent = stripe.PaymentIntent.create(
                amount=int(final_total * 100),
                currency='usd',
                metadata={'buyer_id': str(request.user.id)}
            )
            payment_ref = intent.id
            client_secret = intent.client_secret
        else:
            payment_ref = 'free_order'
            client_secret = None

        order = Order.objects.create(
            buyer=request.user,
            total_amount=final_total,
            coupon_applied=coupon,
            discount_amount=discount_amount,
            status='pending',
            shipping_address=serializer.validated_data['shipping_address'],
            notes=serializer.validated_data.get('notes', ''),
            payment_ref=payment_ref,
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

        logger.info('Order %s created for buyer %s — total: %s', order.id, request.user.email, final_total)

        response_data = {
            'status': 'success',
            'message': 'Order placed successfully.',
            'client_secret': client_secret,
            'data': OrderSerializer(order).data,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        end_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, end_secret
            )
        except ValueError as e:
            return Response(status=400)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=400)

        # Handle the event
        if event.type == 'payment_intent.succeeded':
            payment_intent = event.data.object
            payment_ref = payment_intent.id
            
            Order.objects.filter(payment_ref=payment_ref).update(status='processing')
            logger.info("Order with payment_ref %s marked as paid (processing).", payment_ref)

        return Response(status=200)


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

class OrderFulfillmentView(APIView):
    """Sellers can hit this endpoint to generate a shipping label via EasyPost and mark as shipped."""
    permission_classes = [IsSellerOrAdmin]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        user = request.user
        if not user.is_admin_user:
            # Verify the seller owns at least one item in this order
            if not order.items.filter(product__seller=user).exists():
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        # In a real scenario, addresses would be parsed or fetched from models
        # This is a stub showing the integration flow:
        mock_from_address = {'street1': '417 Montgomery Street', 'city': 'San Francisco', 'state': 'CA', 'zip_code': '94104'}
        mock_to_address = {'street1': '100 Main St', 'city': 'New York', 'state': 'NY', 'zip_code': '10001'}
        
        shipment = shipping.create_shipment(mock_from_address, mock_to_address, {'weight': 20})
        
        if shipment and hasattr(shipment, 'rates') and shipment.rates:
            # Buy lowest rate
            lowest_rate = shipment.rates[0]
            label_data = shipping.buy_shipment(shipment.id, lowest_rate.id)
            if label_data:
                order.tracking_number = label_data['tracking_code']
                order.carrier = label_data['carrier']
                order.status = 'shipped'
                order.save(update_fields=['tracking_number', 'carrier', 'status'])
                
                return Response({
                    'status': 'success',
                    'message': 'Label purchased and order shipped.',
                    'tracking': label_data
                })
        
        # Fallback if EasyPost isn't configured with real keys
        order.status = 'shipped'
        order.tracking_number = 'EZP_MOCK_123456789'
        order.carrier = 'MockPost'
        order.save(update_fields=['tracking_number', 'carrier', 'status'])
        
        return Response({
            'status': 'success',
            'message': 'Order marked as shipped (mocked shipping).',
            'tracking': {
                'tracking_code': order.tracking_number,
                'carrier': order.carrier
            }
        })
