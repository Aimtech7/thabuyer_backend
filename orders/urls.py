"""orders/urls.py"""
from django.urls import path
from .views import CheckoutView, OrderListView, OrderDetailView, OrderStatusUpdateView, StripeWebhookView, OrderFulfillmentView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='order-checkout'),
    path('', OrderListView.as_view(), name='order-list'),
    path('<uuid:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<uuid:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('<uuid:pk>/fulfill/', OrderFulfillmentView.as_view(), name='order-fulfill'),
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
