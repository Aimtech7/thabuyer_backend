"""ai_engine/views.py"""
from decimal import Decimal
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from products.models import Product
from pricing.models import PriceHistory
from .engine import ProductCandidate, score_candidates


class AIRecommendView(APIView):
    """
    AI Buying Tool Endpoint.

    Given a product_id, finds all comparable products (by name),
    scores them using a multi-factor algorithm, and returns:
      - Ranked list with scores & explanations
      - The single best recommendation with a full rationale
    """
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        # Resolve the base product
        try:
            base = Product.objects.select_related(
                'seller', 'seller__seller_profile'
            ).get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Find comparable products (same keyword in name)
        keyword = base.name.split()[0]
        comparables = Product.objects.filter(
            name__icontains=keyword,
            is_active=True,
        ).select_related('seller', 'seller__seller_profile').prefetch_related(
            'reviews', 'price_history'
        )

        if not comparables.exists():
            comparables = Product.objects.filter(pk=product_id).select_related(
                'seller', 'seller__seller_profile'
            ).prefetch_related('reviews', 'price_history')

        # Build candidate list
        candidates = []
        for product in comparables:
            try:
                seller_rating = float(product.seller.seller_profile.rating_avg)
            except Exception:
                seller_rating = 0.0

            reviews = product.reviews.all()
            avg_stars = (
                sum(r.stars for r in reviews) / reviews.count()
                if reviews.exists() else None
            )

            recent_prices = list(
                PriceHistory.objects.filter(product=product)
                .order_by('-recorded_at')
                .values_list('price', flat=True)[:10]
            )

            candidates.append(ProductCandidate(
                product_id=str(product.id),
                product_name=product.name,
                seller_name=product.seller.name,
                seller_rating=seller_rating,
                price=product.price,
                stock_qty=product.stock_qty,
                delivery_days=product.delivery_days,
                avg_review_stars=avg_stars,
                recent_prices=recent_prices,
            ))

        # Score and rank
        ranked = score_candidates(candidates)

        best = ranked[0] if ranked else None

        ranked_output = [
            {
                'rank': i + 1,
                'product_id': c.product_id,
                'product_name': c.product_name,
                'seller_name': c.seller_name,
                'seller_rating': c.seller_rating,
                'price': str(c.price),
                'stock_qty': c.stock_qty,
                'avg_review_stars': c.avg_review_stars,
                'price_trend': c.price_trend,
                'ai_score': c.score,
                'explanation': c.explanation,
            }
            for i, c in enumerate(ranked)
        ]

        return Response({
            'status': 'success',
            'query_product_id': str(product_id),
            'candidates_evaluated': len(ranked),
            'best_recommendation': {
                'product_id': best.product_id if best else None,
                'product_name': best.product_name if best else None,
                'price': str(best.price) if best else None,
                'ai_score': best.score if best else None,
                'explanation': best.explanation if best else 'No comparable products found.',
            },
            'ranked_options': ranked_output,
        })
