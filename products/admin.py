"""products/admin.py"""
from django.contrib import admin
from .models import Product, ProductImage, Category


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ('uploaded_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'SKU', 'seller', 'category', 'price', 'stock_qty', 'is_active', 'created_at'
    )
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'SKU', 'seller__email', 'seller__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [ProductImageInline]

    fieldsets = (
        ('Product Info', {'fields': ('id', 'name', 'description', 'SKU', 'category')}),
        ('Pricing & Stock', {'fields': ('price', 'stock_qty', 'is_active')}),
        ('Ownership', {'fields': ('seller',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    actions = ['deactivate_products', 'activate_products']

    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} product(s) deactivated.')
    deactivate_products.short_description = 'Deactivate selected products'

    def activate_products(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} product(s) activated.')
    activate_products.short_description = 'Activate selected products'
