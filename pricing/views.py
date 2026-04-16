"""pricing/views.py"""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from core.permissions import IsBuyer, IsBuyerOrAdmin
from .models import PriceHistory, PriceAlert
from .serializers import PriceHistorySerializer, PriceAlertSerializer


class ProductPriceHistoryView(generics.ListAPIView):
    """Public price history for a product."""
    serializer_class = PriceHistorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return PriceHistory.objects.filter(product_id=product_id).order_by('-recorded_at')


class PriceAlertListCreateView(generics.ListCreateAPIView):
    """List buyer's price alerts or create new one."""
    serializer_class = PriceAlertSerializer
    permission_classes = [IsBuyer]

    def get_queryset(self):
        return PriceAlert.objects.filter(
            buyer=self.request.user
        ).select_related('product').order_by('-created_at')


class PriceAlertDeleteView(generics.DestroyAPIView):
    """Cancel a price alert."""
    permission_classes = [IsBuyer]

    def get_queryset(self):
        return PriceAlert.objects.filter(buyer=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = 'cancelled'
        instance.save(update_fields=['status'])
        return Response({'status': 'success', 'message': 'Alert cancelled.'})
