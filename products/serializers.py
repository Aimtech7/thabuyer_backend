"""products/serializers.py"""
import uuid
from rest_framework import serializers
from .models import Product, ProductImage, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'parent')
        read_only_fields = ('id', 'slug')

    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            from django.utils.text import slugify
            validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    seller_business = serializers.SerializerMethodField()
    in_stock = serializers.BooleanField(read_only=True)
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'seller', 'seller_name', 'seller_business',
            'category', 'category_name',
            'name', 'description', 'price', 'stock_qty', 'delivery_days', 'SKU',
            'is_active', 'in_stock', 'images', 'avg_rating',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'seller', 'created_at', 'updated_at')

    def get_seller_business(self, obj):
        try:
            return obj.seller.seller_profile.business_name
        except Exception:
            return None

    def get_avg_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews.exists():
            return None
        return round(sum(r.stars for r in reviews) / reviews.count(), 2)


class ProductCreateSerializer(serializers.ModelSerializer):
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Product
        fields = (
            'name', 'description', 'price', 'stock_qty', 'delivery_days',
            'SKU', 'category', 'is_active', 'uploaded_images',
        )

    def validate_SKU(self, value):
        request = self.context.get('request')
        qs = Product.objects.filter(SKU=value)
        # On update, exclude current instance
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A product with this SKU already exists.')
        return value

    def create(self, validated_data):
        images = validated_data.pop('uploaded_images', [])
        seller = self.context['request'].user
        product = Product.objects.create(seller=seller, **validated_data)
        for i, img in enumerate(images):
            ProductImage.objects.create(
                product=product, image=img, is_primary=(i == 0)
            )
        return product

    def update(self, instance, validated_data):
        images = validated_data.pop('uploaded_images', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        for i, img in enumerate(images):
            ProductImage.objects.create(product=instance, image=img)
        return instance


class ProductBulkRowSerializer(serializers.Serializer):
    """Validates a single row from bulk upload Excel."""
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, default='')
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    stock_qty = serializers.IntegerField(min_value=0)
    SKU = serializers.CharField(max_length=100)
    category = serializers.CharField(max_length=100, allow_blank=True, default='')


class ProductCompareSerializer(serializers.Serializer):
    """Comparison table entry."""
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    seller_name = serializers.CharField()
    seller_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock_qty = serializers.IntegerField()
    delivery_days = serializers.IntegerField()
    is_lowest_price = serializers.BooleanField()
    price_difference = serializers.DecimalField(max_digits=12, decimal_places=2)
