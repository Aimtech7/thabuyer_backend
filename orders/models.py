"""orders/models.py"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders',
        limit_choices_to={'role': 'buyer'}
    )
    total_amount = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(0)]
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    payment_ref = models.CharField(max_length=255, blank=True, db_index=True)
    shipping_address = models.TextField(blank=True)
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
        return f'Order #{str(self.id)[:8]} — {self.buyer.email} [{self.status}]'


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product', on_delete=models.SET_NULL, null=True, related_name='order_items'
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f'{self.quantity}x {self.product.name if self.product else "deleted"}'

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)
