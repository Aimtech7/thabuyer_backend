"""products/urls.py"""
from django.urls import path
from .views import (
    CategoryListView,
    CategoryCreateView,
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductSearchView,
    ProductCompareView,
    ProductBulkUploadView,
    AIDescribeView,
)

from pricing.views import ProductPriceHistoryView

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<uuid:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('<uuid:pk>/compare/', ProductCompareView.as_view(), name='product-compare'),
    path('<uuid:product_id>/price-history/', ProductPriceHistoryView.as_view(), name='product-price-history'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('bulk-upload/', ProductBulkUploadView.as_view(), name='product-bulk-upload'),
    path('ai-describe/', AIDescribeView.as_view(), name='ai-describe'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category-create'),
]
