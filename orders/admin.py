"""orders/admin.py"""
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('id', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'buyer', 'total_amount', 'status', 'payment_ref', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('buyer__email', 'buyer__name', 'payment_ref')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Info', {'fields': ('id', 'buyer', 'status')}),
        ('Financials', {'fields': ('total_amount', 'payment_ref')}),
        ('Shipping', {'fields': ('shipping_address', 'notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def short_id(self, obj):
        return str(obj.id)[:8].upper()
    short_id.short_description = 'Order ID'
