from django.contrib import admin
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_amount', 'discount_type', 'active', 'times_used', 'valid_until')
    list_filter = ('active', 'discount_type', 'valid_from', 'valid_until')
    search_fields = ('code',)
