"""orders/models.py"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from promotions.models import Coupon

class OrderSequence(models.Model):
    """Atomic per-year counter for human-readable order numbers."""
    year = models.PositiveIntegerField(unique=True)
    counter = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'order_sequences'

    def __str__(self):
        return f'OrderSequence({self.year}: {self.counter})'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, blank=True, db_index=True)
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders',
        limit_choices_to={'role': 'buyer'}
    )
    total_amount = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(0)]
    )
    coupon_applied = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    payment_ref = models.CharField(max_length=255, blank=True, db_index=True)
    shipping_address = models.TextField(blank=True) # Fallback to text for easy migrations or manual addresses
    tracking_number = models.CharField(max_length=255, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    shipping_rate_id = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        num = self.order_number or str(self.id)[:8]
        return f'Order #{num} — {self.buyer.email} [{self.status}]'

    def save(self, *args, **kwargs):
        if not self.order_number:
            from orders.utils import generate_order_number
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product', on_delete=models.SET_NULL, null=True, related_name='order_items'
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    commission_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    seller_earnings = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f'{self.quantity}x {self.product.name if self.product else "deleted"}'

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        if self.product and self.product.seller:
            self.commission_rate = self.product.seller.seller_profile.commission_rate
            self.commission_amount = self.subtotal * (self.commission_rate / 100)
            self.seller_earnings = self.subtotal - self.commission_amount
        super().save(*args, **kwargs)
