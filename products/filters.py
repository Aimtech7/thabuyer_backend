"""products/filters.py"""
import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
    seller = django_filters.UUIDFilter(field_name='seller__id')
    rating = django_filters.NumberFilter(method='filter_rating')

    class Meta:
        model = Product
        fields = ['category', 'seller', 'min_price', 'max_price', 'in_stock', 'rating']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_qty__gt=0)
        return queryset.filter(stock_qty=0)

    def filter_rating(self, queryset, name, value):
        from django.db.models import Avg
        return queryset.annotate(
            avg_rating=Avg('reviews__stars')
        ).filter(avg_rating__gte=value)
