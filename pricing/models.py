"""pricing/models.py"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class PriceHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='price_history'
    )
    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'price_history'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['product', '-recorded_at']),
        ]

    def __str__(self):
        return f'{self.product.name} → {self.price} @ {self.recorded_at:%Y-%m-%d %H:%M}'


class PriceAlert(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('triggered', 'Triggered'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='price_alerts',
        limit_choices_to={'role': 'buyer'}
    )
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='price_alerts'
    )
    target_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'price_alerts'
        unique_together = ('buyer', 'product')
        indexes = [
            models.Index(fields=['buyer', 'status']),
        ]

    def __str__(self):
        return f'Alert: {self.buyer.email} → {self.product.name} @ {self.target_price}'
