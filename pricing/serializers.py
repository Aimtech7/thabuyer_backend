"""pricing/serializers.py"""
from rest_framework import serializers
from .models import PriceHistory, PriceAlert


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ('id', 'product', 'price', 'recorded_at')
        read_only_fields = ('id', 'recorded_at')


class PriceAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    current_price = serializers.DecimalField(
        source='product.price', max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = PriceAlert
        fields = (
            'id', 'product', 'product_name', 'current_price',
            'target_price', 'status', 'triggered_at', 'created_at',
        )
        read_only_fields = ('id', 'status', 'triggered_at', 'created_at')

    def validate(self, attrs):
        buyer = self.context['request'].user
        product = attrs['product']
        if PriceAlert.objects.filter(buyer=buyer, product=product, status='active').exists():
            raise serializers.ValidationError('An active alert for this product already exists.')
        if attrs['target_price'] >= product.price:
            raise serializers.ValidationError(
                'Target price must be lower than the current price.'
            )
        return attrs

    def create(self, validated_data):
        validated_data['buyer'] = self.context['request'].user
        return super().create(validated_data)
