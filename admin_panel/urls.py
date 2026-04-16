"""admin_panel/urls.py"""
from django.urls import path
from .views import (
    AdminUserListView,
    AdminUserDetailView,
    AdminSuspendUserView,
    AdminActivateUserView,
    AdminVerifySellerView,
    AdminPlatformStatsView,
    AdminOrderListView,
    AdminAnalyticsView,
    AdminReportedContentView,
)

urlpatterns = [
    path('users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('users/<uuid:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('users/<uuid:pk>/suspend/', AdminSuspendUserView.as_view(), name='admin-suspend-user'),
    path('users/<uuid:pk>/activate/', AdminActivateUserView.as_view(), name='admin-activate-user'),
    path('sellers/<uuid:pk>/verify/', AdminVerifySellerView.as_view(), name='admin-verify-seller'),
    path('stats/', AdminPlatformStatsView.as_view(), name='admin-stats'),
    path('orders/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),
    path('reported-content/', AdminReportedContentView.as_view(), name='admin-reported-content'),
]
