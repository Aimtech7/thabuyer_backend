"""cart/admin.py"""
from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('price_at_add', 'added_at', 'subtotal')

    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = 'Subtotal'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'item_count', 'total', 'created_at', 'updated_at')
    search_fields = ('buyer__email', 'buyer__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [CartItemInline]

    def item_count(self, obj):
        return obj.item_count
    item_count.short_description = '# Items'

    def total(self, obj):
        return f'${obj.total:.2f}'
    total.short_description = 'Total'
