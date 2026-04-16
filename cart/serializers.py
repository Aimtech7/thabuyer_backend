"""cart/serializers.py"""
from rest_framework import serializers
from products.serializers import ProductSerializer
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = (
            'id', 'product', 'product_detail',
            'quantity', 'price_at_add', 'subtotal', 'added_at',
        )
        read_only_fields = ('id', 'price_at_add', 'added_at')


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'buyer', 'items', 'total', 'item_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'buyer', 'created_at', 'updated_at')


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        from products.models import Product
        try:
            product = Product.objects.get(pk=attrs['product_id'], is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({'product_id': 'Product not found or inactive.'})

        if attrs['quantity'] > product.stock_qty:
            raise serializers.ValidationError(
                {'quantity': f'Only {product.stock_qty} units available.'}
            )
        attrs['product'] = product
        return attrs


class RemoveFromCartSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
