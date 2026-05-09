"""ai_engine/urls.py"""
from django.urls import path
from .views import AIRecommendView, ImageEnhanceView

urlpatterns = [
    path('recommend/<uuid:product_id>/', AIRecommendView.as_view(), name='ai-recommend'),
    path('enhance-image/', ImageEnhanceView.as_view(), name='ai-enhance-image'),
]
