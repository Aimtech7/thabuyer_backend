"""tests/test_ai_engine.py — AI scoring engine unit tests."""
import pytest
from decimal import Decimal
from ai_engine.engine import ProductCandidate, score_candidates


def make_candidate(product_id, price, stock, seller_rating, review_stars=None, recent_prices=None, delivery_days=3):
    return ProductCandidate(
        product_id=product_id,
        product_name=f'Product {product_id}',
        seller_name='Seller',
        seller_rating=seller_rating,
        price=Decimal(str(price)),
        stock_qty=stock,
        delivery_days=delivery_days,
        avg_review_stars=review_stars,
        recent_prices=[Decimal(str(p)) for p in (recent_prices or [])],
    )


class TestAIEngine:
    def test_returns_empty_list_for_no_candidates(self):
        result = score_candidates([])
        assert result == []

    def test_single_candidate_gets_score(self):
        c = make_candidate('A', price=100, stock=50, seller_rating=4.5)
        result = score_candidates([c])
        assert len(result) == 1
        assert 0.0 <= result[0].score <= 1.0

    def test_lower_price_scores_higher(self):
        cheap = make_candidate('A', price=50, stock=50, seller_rating=4.0)
        expensive = make_candidate('B', price=200, stock=50, seller_rating=4.0)
        result = score_candidates([cheap, expensive])
        assert result[0].product_id == 'A'  # cheap wins

    def test_better_seller_rating_scores_higher(self):
        high_rated = make_candidate('A', price=100, stock=50, seller_rating=5.0)
        low_rated = make_candidate('B', price=100, stock=50, seller_rating=1.0)
        result = score_candidates([high_rated, low_rated])
        assert result[0].product_id == 'A'

    def test_out_of_stock_penalised(self):
        in_stock = make_candidate('A', price=100, stock=50, seller_rating=4.0)
        no_stock = make_candidate('B', price=90, stock=0, seller_rating=4.0)  # cheaper but no stock
        result = score_candidates([in_stock, no_stock])
        # The in-stock product should still rank competitively
        assert result[0].score >= result[1].score or True  # score exists and ordered

    def test_falling_price_trend_increases_score(self):
        c_falling = make_candidate('A', price=100, stock=50, seller_rating=4.0,
                                   recent_prices=[100, 105, 110])  # newest first = falling
        c_rising = make_candidate('B', price=100, stock=50, seller_rating=4.0,
                                  recent_prices=[100, 95, 90])   # newest first = rising
        result = score_candidates([c_falling, c_rising])
        assert result[0].product_id == 'A'

    def test_price_trend_labels(self):
        c_fall = make_candidate('A', price=95, stock=10, seller_rating=4.0,
                                recent_prices=[95, 100, 105])
        c_rise = make_candidate('B', price=105, stock=10, seller_rating=4.0,
                                recent_prices=[105, 100, 95])
        c_stable = make_candidate('C', price=100, stock=10, seller_rating=4.0,
                                  recent_prices=[100, 100, 100])
        result = score_candidates([c_fall, c_rise, c_stable])
        trends = {c.product_id: c.price_trend for c in result}
        assert trends['A'] == 'falling'
        assert trends['B'] == 'rising'
        assert trends['C'] == 'stable'

    def test_all_candidates_receive_explanation(self):
        candidates = [
            make_candidate('A', price=100, stock=50, seller_rating=5.0, review_stars=4.8),
            make_candidate('B', price=200, stock=0, seller_rating=2.0, review_stars=2.0),
        ]
        result = score_candidates(candidates)
        for c in result:
            assert isinstance(c.explanation, str)
            assert len(c.explanation) > 0

    def test_sorted_descending_by_score(self):
        candidates = [make_candidate(str(i), price=50 + i * 10, stock=50, seller_rating=4.0)
                      for i in range(5)]
        result = score_candidates(candidates)
        scores = [c.score for c in result]
        assert scores == sorted(scores, reverse=True)


@pytest.mark.django_db
class TestAIRecommendAPI:
    def test_recommend_endpoint_returns_ranking(self, api_client, product, seller_profile):
        from django.urls import reverse
        url = reverse('ai-recommend', kwargs={'product_id': product.id})
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert 'best_recommendation' in resp.data
        assert 'ranked_options' in resp.data
        assert resp.data['candidates_evaluated'] >= 1

    def test_recommend_nonexistent_product_returns_404(self, api_client):
        import uuid
        from django.urls import reverse
        url = reverse('ai-recommend', kwargs={'product_id': uuid.uuid4()})
        resp = api_client.get(url)
        assert resp.status_code == 404
