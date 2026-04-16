"""pricing/admin.py"""
from django.contrib import admin
from .models import PriceHistory, PriceAlert


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'price', 'recorded_at')
    list_filter = ('recorded_at',)
    search_fields = ('product__name', 'product__SKU')
    readonly_fields = ('id', 'recorded_at')
    ordering = ('-recorded_at',)


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'product', 'target_price', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('buyer__email', 'product__name')
    readonly_fields = ('id', 'created_at', 'triggered_at')
