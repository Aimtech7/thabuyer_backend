"""cart/models.py"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='cart',
        limit_choices_to={'role': 'buyer'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    def __str__(self):
        return f'Cart of {self.buyer.email}'

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        return self.items.count()


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price_at_add = models.DecimalField(max_digits=12, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ('cart', 'product')

    def __str__(self):
        return f'{self.quantity}x {self.product.name}'

    @property
    def subtotal(self):
        return self.price_at_add * self.quantity
