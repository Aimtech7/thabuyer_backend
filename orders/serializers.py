"""orders/serializers.py"""
from rest_framework import serializers
from .models import Order, OrderItem
from promotions.models import Coupon


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.SKU', read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'product_sku', 'quantity', 'unit_price', 'subtotal')
        read_only_fields = ('id', 'subtotal')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_email = serializers.EmailField(source='buyer.email', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'buyer', 'buyer_email', 'items',
            'total_amount', 'status', 'payment_ref',
            'shipping_address', 'tracking_number', 'carrier', 'shipping_rate_id',
            'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'buyer', 'total_amount', 'status', 'tracking_number', 'carrier', 'created_at', 'updated_at')


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    payment_ref = serializers.CharField(required=False, allow_blank=True, default='')
    coupon_code = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        user = self.context['request'].user
        try:
            cart = user.cart
        except Exception:
            raise serializers.ValidationError('No cart found.')
        if not cart.items.exists():
            raise serializers.ValidationError('Cart is empty.')
        attrs['cart'] = cart

        coupon_code = attrs.get('coupon_code')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if not coupon.is_valid():
                    raise serializers.ValidationError({'coupon_code': 'Coupon is invalid or expired.'})
                attrs['coupon'] = coupon
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({'coupon_code': 'Invalid coupon code.'})

        return attrs


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('status',)

    def validate_status(self, value):
        current = self.instance.status
        valid_transitions = {
            'pending': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': ['refunded'],
            'cancelled': [],
            'refunded': [],
        }
        if value not in valid_transitions.get(current, []):
            raise serializers.ValidationError(
                f'Cannot transition from "{current}" to "{value}".'
            )
        return value
