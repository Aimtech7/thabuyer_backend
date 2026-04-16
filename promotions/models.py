from django.db import models
from django.core.validators import MinValueValidator
from sellers.models import SellerProfile

class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('fixed', 'Fixed Amount'),
        ('percent', 'Percentage'),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='fixed')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    active = models.BooleanField(default=True)
    seller_restricted = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='coupons', help_text="If set, this coupon only applies to products from this seller.")
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'coupons'
        ordering = ['-valid_from']

    def __str__(self):
        return f"{self.code} ({self.discount_amount} {self.discount_type})"

    def is_valid(self):
        from django.utils import timezone
        if not self.active:
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True
