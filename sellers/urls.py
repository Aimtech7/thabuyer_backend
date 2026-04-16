"""sellers/urls.py"""
from django.urls import path
from .views import SellerProfileView, SellerProfileCreateView, SellerDashboardView, SellerProductsView

urlpatterns = [
    path('profile/', SellerProfileView.as_view(), name='seller-profile'),
    path('profile/create/', SellerProfileCreateView.as_view(), name='seller-profile-create'),
    path('dashboard/', SellerDashboardView.as_view(), name='seller-dashboard'),
    path('products/', SellerProductsView.as_view(), name='seller-products'),
]
