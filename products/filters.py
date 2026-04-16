"""products/filters.py"""
import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
    seller = django_filters.UUIDFilter(field_name='seller__id')

    class Meta:
        model = Product
        fields = ['category', 'seller', 'min_price', 'max_price', 'in_stock']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_qty__gt=0)
        return queryset.filter(stock_qty=0)
