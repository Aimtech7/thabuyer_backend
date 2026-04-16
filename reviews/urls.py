"""reviews/urls.py"""
from django.urls import path
from .views import (
    ProductReviewListView,
    ReviewCreateView,
    ReviewDetailView,
    DiscussionThreadListCreateView,
    DiscussionReplyCreateView,
)

urlpatterns = [
    # Reviews
    path('', ReviewCreateView.as_view(), name='review-create'),
    path('<uuid:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('products/<uuid:product_id>/', ProductReviewListView.as_view(), name='product-reviews'),

    # Discussions
    path('discussions/<uuid:product_id>/', DiscussionThreadListCreateView.as_view(), name='discussion-list'),
    path('discussions/thread/<uuid:thread_id>/reply/', DiscussionReplyCreateView.as_view(), name='discussion-reply'),
]
