"""pricing/urls.py"""
from django.urls import path
from .views import ProductPriceHistoryView, PriceAlertListCreateView, PriceAlertDeleteView

urlpatterns = [
    path('history/<uuid:product_id>/', ProductPriceHistoryView.as_view(), name='price-history'),
    path('alerts/', PriceAlertListCreateView.as_view(), name='price-alerts'),
    path('alerts/<uuid:pk>/cancel/', PriceAlertDeleteView.as_view(), name='price-alert-cancel'),
]
