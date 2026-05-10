from django.urls import path
from .views import WishlistView, WishlistItemCreateView, WishlistItemDeleteView

urlpatterns = [
    path('', WishlistView.as_view(), name='wishlist-detail'),
    path('add/', WishlistItemCreateView.as_view(), name='wishlist-add'),
    path('remove/<uuid:product_id>/', WishlistItemDeleteView.as_view(), name='wishlist-remove-param'),
    path('remove/', WishlistItemDeleteView.as_view(), name='wishlist-remove-body'),
]
