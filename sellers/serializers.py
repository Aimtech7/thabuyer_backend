"""sellers/serializers.py"""
from rest_framework import serializers
from .models import SellerProfile
from users.serializers import UserSerializer


class SellerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    total_products = serializers.SerializerMethodField()

    class Meta:
        model = SellerProfile
        fields = (
            'id', 'user', 'business_name', 'business_description',
            'rating_avg', 'rating_count', 'verified', 'commission_rate',
            'contact_email', 'contact_phone', 'address',
            'total_products', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'rating_avg', 'rating_count', 'verified', 'commission_rate', 'created_at', 'updated_at')

    def get_total_products(self, obj):
        return obj.user.products.count()


class SellerProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = ('business_name', 'business_description', 'contact_email', 'contact_phone', 'address')

    def create(self, validated_data):
        user = self.context['request'].user
        if SellerProfile.objects.filter(user=user).exists():
            raise serializers.ValidationError('Seller profile already exists.')
        return SellerProfile.objects.create(user=user, **validated_data)


class SellerDashboardSerializer(serializers.Serializer):
    profile = SellerProfileSerializer()
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_orders = serializers.IntegerField()
    recent_reviews = serializers.ListField()
