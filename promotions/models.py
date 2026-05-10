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

from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Coupon)
def broadcast_new_coupon(sender, instance, created, **kwargs):
    if created and instance.active:
        # 1. Real-time broadcast
        channel_layer = get_channel_layer()
        if channel_layer:
            message = f"New Promotion! Use code {instance.code} for {instance.discount_amount} "
            message += f"{'%' if instance.discount_type == 'percent' else 'off'}!"
            async_to_sync(channel_layer.group_send)(
                'global_notifications',
                {
                    'type': 'promotion_alert',
                    'code': instance.code,
                    'message': message,
                    'discount': str(instance.discount_amount),
                    'expiration': str(instance.valid_until) if instance.valid_until else 'Never',
                    'seller': instance.seller_restricted.business_name if instance.seller_restricted else 'Sitewide'
                }
            )
        
        # 2. Email Campaign
        from orders.tasks import send_promotional_email
        headline = "New Promotion Just For You! 🎁"
        body = f"Use code {instance.code} to get a special discount on your next order."
        terms = "Valid for a limited time only. Cannot be combined with other offers."
        send_promotional_email.delay(
            coupon_id=str(instance.id),
            headline=headline,
            body=body,
            terms=terms
        )

