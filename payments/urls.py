from django.urls import path
from .views import CreateCheckoutSessionView, PaystackWebhookView

urlpatterns = [
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),
]
