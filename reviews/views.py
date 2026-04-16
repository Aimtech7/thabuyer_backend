"""reviews/views.py"""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.permissions import IsBuyer, IsOwnerOrAdmin, IsSellerOrAdmin
from .models import Review, DiscussionThread, DiscussionReply, SellerReply, ContentReport
from .serializers import (
    ReviewSerializer,
    DiscussionThreadSerializer,
    DiscussionReplySerializer,
    SellerReplySerializer,
    ContentReportSerializer,
)


class ProductReviewListView(generics.ListAPIView):
    """List all reviews for a product (public)."""
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return (
            Review.objects.filter(product_id=product_id)
            .select_related('buyer', 'product')
            .order_by('-created_at')
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.exists():
            avg = sum(r.stars for r in queryset) / queryset.count()
        else:
            avg = None
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'average_rating': round(avg, 2) if avg else None,
            'results': serializer.data,
        })


class ReviewCreateView(generics.CreateAPIView):
    """Create a review (buyers only, must have ordered the product)."""
    serializer_class = ReviewSerializer
    permission_classes = [IsBuyer]


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a review (owner or admin)."""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return Review.objects.select_related('buyer', 'product').all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'status': 'success', 'message': 'Review deleted.'})


class DiscussionThreadListCreateView(generics.ListCreateAPIView):
    """List or create discussion threads for a product."""
    serializer_class = DiscussionThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        qs = DiscussionThread.objects.select_related(
            'user', 'product'
        ).prefetch_related('replies__user')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs.order_by('-created_at')


class DiscussionReplyCreateView(generics.CreateAPIView):
    """Reply to a discussion thread."""
    serializer_class = DiscussionReplySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        thread_id = self.kwargs['thread_id']
        thread = DiscussionThread.objects.get(pk=thread_id)
        serializer.save(user=self.request.user, thread=thread)


class DiscussionThreadDeleteView(generics.DestroyAPIView):
    """Admins can delete a discussion thread and all its replies."""
    permission_classes = [IsSellerOrAdmin]

    def get_queryset(self):
        return DiscussionThread.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'status': 'success', 'message': 'Thread deleted.'})


class SellerReplyCreateView(generics.CreateAPIView):
    """Sellers/admins can post a one-time reply on a buyer review."""
    serializer_class = SellerReplySerializer
    permission_classes = [IsSellerOrAdmin]

    def perform_create(self, serializer):
        review_id = self.kwargs['review_id']
        review = Review.objects.get(pk=review_id)
        # Prevent duplicate seller replies (enforced at DB via OneToOneField)
        serializer.save(author=self.request.user, review=review)


class ContentReportCreateView(generics.CreateAPIView):
    """Any authenticated user can flag a review or thread."""
    serializer_class = ContentReportSerializer
    permission_classes = [IsAuthenticated]


class ReportedContentListView(generics.ListAPIView):
    """Admins list all unresolved content reports."""
    serializer_class = ContentReportSerializer
    permission_classes = [IsSellerOrAdmin]

    def get_queryset(self):
        return ContentReport.objects.filter(resolved=False).select_related(
            'reporter', 'review', 'thread'
        ).order_by('-created_at')
