"""orders/views.py"""
import logging
from django.db import transaction
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core.permissions import IsBuyer, IsSellerOrAdmin, IsAdmin
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer, 
    SellerOrderSerializer,
    CheckoutSerializer, 
    OrderStatusUpdateSerializer
)
from . import shipping

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

        if not cart_items.exists():
            return Response(
                {'status': 'error', 'message': 'Cart is empty. Cannot checkout.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        # We will create the order first to generate an ID, then pass the order ID to Paystack as the reference.
        # So we skip payment intent creation here.
        payment_ref = ''
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

        # Save user address if none exists
        address_details = serializer.validated_data.get('address_details')
        if address_details and not request.user.addresses.exists():
            from users.models import UserAddress
            UserAddress.objects.create(
                user=request.user,
                street1=address_details.get('street', address_details.get('street1', '')),
                city=address_details.get('city', ''),
                state=address_details.get('state', ''),
                zip_code=address_details.get('zipCode', address_details.get('zip_code', '')),
                country=address_details.get('country', 'US'),
                is_default=True
            )

        logger.info('Order %s created for buyer %s — total: %s', order.id, request.user.email, final_total)
        
        # Create Paystack Session if amount > 0
        checkout_url = None
        if final_total > 0:
            paystack_key = getattr(settings, "PAYSTACK_SECRET_KEY", None)
            if paystack_key and paystack_key != 'sk_test_fake':
                import requests
                headers = {
                    "Authorization": f"Bearer {paystack_key}",
                    "Content-Type": "application/json"
                }
                frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
                data = {
                    "email": request.user.email,
                    "amount": int(final_total * 100),
                    "reference": str(order.id),
                    "callback_url": f"{frontend_url}/cart?step=confirmation",
                    "metadata": {
                        "cancel_action": f"{frontend_url}/cart"
                    }
                }
                try:
                    res = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
                    if res.status_code == 200:
                        checkout_url = res.json().get('data', {}).get('authorization_url')
                except Exception as e:
                    logger.error("Failed to initialize Paystack: %s", e)
            else:
                # If no Paystack key, the order is created but no checkout URL is provided.
                # In production, this should not happen if Paystack is properly configured.
                logger.warning("Order %s created but Paystack key is missing.", order.id)
                checkout_url = None

        # Notify sellers of new order items
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            # Group items by seller to notify each unique seller once
            seller_ids = order.items.values_list('product__seller_id', flat=True).distinct()
            for s_id in seller_ids:
                async_to_sync(channel_layer.group_send)(
                    f"user_{s_id}",
                    {
                        'type': 'notification_message',
                        'message': f"New order received! Order #{str(order.id)[:8]}",
                    }
                )
        except Exception:
            pass

        response_data = {
            'status': 'success',
            'message': 'Order placed successfully.',
            'checkout_url': checkout_url,
            'data': OrderSerializer(order).data,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)




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

        # Broadcast real-time order update to the buyer via WebSocket
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{instance.buyer.id}",
                {
                    'type': 'order_update',
                    'order_id': str(instance.id),
                    'status': instance.status,
                }
            )
        except Exception:
            pass  # Graceful fallback if Redis/channels not available

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

        buyer_address = order.buyer.addresses.filter(is_default=True).first()
        if buyer_address:
            to_address = {
                'street1': buyer_address.street1,
                'city': buyer_address.city,
                'state': buyer_address.state,
                'zip_code': buyer_address.zip_code,
                'country': buyer_address.country,
            }
        else:
            to_address = {'street1': order.shipping_address or '100 Main St', 'city': 'New York', 'state': 'NY', 'zip_code': '10001'}

        seller_address = user.addresses.filter(is_default=True).first()
        if seller_address:
            from_address = {
                'street1': seller_address.street1,
                'city': seller_address.city,
                'state': seller_address.state,
                'zip_code': seller_address.zip_code,
                'country': seller_address.country,
            }
        else:
            # Fallback to seller_profile.address text or default
            addr_text = getattr(user.seller_profile, 'address', '')
            from_address = {'street1': addr_text if addr_text else '417 Montgomery Street', 'city': 'San Francisco', 'state': 'CA', 'zip_code': '94104'}
        
        shipment = shipping.create_shipment(from_address, to_address, {'weight': 20})
        
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
        # Do not use hardcoded mock tracking numbers in production
        order.tracking_number = f"TBD-{order.id.hex[:8].upper()}"
        order.carrier = 'Standard Shipping'
        order.save(update_fields=['tracking_number', 'carrier', 'status'])
        
        return Response({
            'status': 'success',
            'message': 'Order marked as shipped.',
            'tracking': {
                'tracking_code': order.tracking_number,
                'carrier': order.carrier
            }
        })


class SellerOrderListView(generics.ListAPIView):
    """List all orders involving this seller's products."""
    serializer_class = SellerOrderSerializer
    permission_classes = [IsSellerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.prefetch_related('items__product').all()
        # Filter orders that contain at least one product from this seller
        return Order.objects.filter(items__product__seller=user).distinct().prefetch_related('items__product')


class SellerAnalyticsView(APIView):
    """Return sales performance data for charts (last 30 days)."""
    permission_classes = [IsSellerOrAdmin]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Sum, F
        from django.db.models.functions import TruncDate

        user = request.user
        days_30_ago = timezone.now() - timedelta(days=30)

        # 1. Daily Sales Trend
        daily_sales = (
            OrderItem.objects.filter(
                product__seller=user,
                order__created_at__gte=days_30_ago,
                order__status__in=['processing', 'shipped', 'delivered']
            )
            .annotate(date=TruncDate('order__created_at'))
            .values('date')
            .annotate(revenue=Sum(F('unit_price') * F('quantity')))
            .order_by('date')
        )

        # 2. Category Distribution
        category_sales = (
            OrderItem.objects.filter(product__seller=user)
            .values('product__category__name')
            .annotate(value=Sum(F('unit_price') * F('quantity')))
            .order_by('-value')[:5]
        )

        return Response({
            'status': 'success',
            'daily_sales': daily_sales,
            'category_sales': [
                {'name': item['product__category__name'] or 'Uncategorized', 'value': float(item['value'])}
                for item in category_sales
            ],
            'summary': {
                'total_revenue': sum(item['revenue'] for item in daily_sales),
                'order_count': Order.objects.filter(items__product__seller=user).distinct().count()
            }
        })
