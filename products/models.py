"""products/models.py"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children'
    )
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='products',
        limit_choices_to={'role': 'seller'}
    )
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='products'
    )
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stock_qty = models.PositiveIntegerField(default=0)
    delivery_days = models.PositiveIntegerField(default=3, help_text="Estimated shipping days")
    SKU = models.CharField(max_length=100, unique=True, db_index=True, blank=True)
    clicks_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f'{self.name} — {self.SKU}'

    @property
    def in_stock(self):
        return self.stock_qty > 0

    def save(self, *args, **kwargs):
        if not self.SKU:
            import random
            import string
            # Generate a random 8-character string for the SKU
            prefix = ''.join(e for e in self.name[:3] if e.isalnum()).upper() if self.name else "PRD"
            if len(prefix) < 3:
                prefix = prefix.ljust(3, 'X')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            self.SKU = f"{prefix}-{random_str}"
            # Ensure unique
            while Product.objects.filter(SKU=self.SKU).exists():
                random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                self.SKU = f"{prefix}-{random_str}"

        is_new = self._state.adding
        old_price = None
        if not is_new:
            try:
                old_price = Product.objects.get(pk=self.pk).price
            except Product.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Record price change in history
        if is_new or (old_price is not None and old_price != self.price):
            from pricing.models import PriceHistory
            PriceHistory.objects.create(product=self, price=self.price)

            # Broadcast price drop event if price decreased
            if old_price is not None and self.price < old_price:
                try:
                    from asgiref.sync import async_to_sync
                    from channels.layers import get_channel_layer
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'global_notifications',
                        {
                            'type': 'price_drop',
                            'product_id': str(self.id),
                            'product_name': self.name,
                            'old_price': str(old_price),
                            'new_price': str(self.price),
                        }
                    )
                except Exception:
                    pass  # Graceful fallback


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_images'

    def __str__(self):
        return f'Image for {self.product.name}'
