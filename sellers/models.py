"""sellers/models.py"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


class SellerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='seller_profile'
    )
    business_name = models.CharField(max_length=200)
    business_description = models.TextField(blank=True)
    rating_avg = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    rating_count = models.PositiveIntegerField(default=0)
    verified = models.BooleanField(default=False)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    commission_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'seller_profiles'
        verbose_name = 'Seller Profile'
        verbose_name_plural = 'Seller Profiles'

    def __str__(self):
        return f'{self.business_name} ({"✓" if self.verified else "pending"})'

    def update_rating(self, new_stars: float):
        """Recalculate running average rating."""
        total = self.rating_avg * self.rating_count + new_stars
        self.rating_count += 1
        self.rating_avg = round(total / self.rating_count, 2)
        self.save(update_fields=['rating_avg', 'rating_count'])
