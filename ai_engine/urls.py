"""ai_engine/urls.py"""
from django.urls import path
from .views import AIRecommendView

urlpatterns = [
    path('recommend/<uuid:product_id>/', AIRecommendView.as_view(), name='ai-recommend'),
]
