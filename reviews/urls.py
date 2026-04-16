"""reviews/urls.py"""
from django.urls import path
from .views import (
    ProductReviewListView,
    ReviewCreateView,
    ReviewDetailView,
    DiscussionThreadListCreateView,
    DiscussionReplyCreateView,
    DiscussionThreadDeleteView,
    SellerReplyCreateView,
    ContentReportCreateView,
    ReportedContentListView,
)

urlpatterns = [
    # Reviews
    path('', ReviewCreateView.as_view(), name='review-create'),
    path('<uuid:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('products/<uuid:product_id>/', ProductReviewListView.as_view(), name='product-reviews'),

    # Seller replies on reviews
    path('<uuid:review_id>/reply/', SellerReplyCreateView.as_view(), name='seller-review-reply'),

    # Discussions
    path('discussions/<uuid:product_id>/', DiscussionThreadListCreateView.as_view(), name='discussion-list'),
    path('discussions/thread/<uuid:thread_id>/reply/', DiscussionReplyCreateView.as_view(), name='discussion-reply'),
    path('discussions/thread/<uuid:pk>/delete/', DiscussionThreadDeleteView.as_view(), name='discussion-thread-delete'),

    # Content reports / moderation
    path('report/', ContentReportCreateView.as_view(), name='content-report'),
    path('reported/', ReportedContentListView.as_view(), name='reported-content'),
]
