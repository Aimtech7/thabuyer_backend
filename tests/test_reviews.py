"""tests/test_reviews.py — Review model & endpoint tests."""
import pytest
from decimal import Decimal
from django.urls import reverse
from reviews.models import Review


# ─── Model Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReviewModel:
    def test_review_creation(self, buyer, product, completed_order):
        review = Review.objects.create(
            product=product, buyer=buyer, stars=5, comment='Excellent!'
        )
        assert review.stars == 5
        assert review.comment == 'Excellent!'

    def test_one_review_per_buyer_per_product(self, buyer, product, completed_order):
        Review.objects.create(product=product, buyer=buyer, stars=4, comment='Good')
        with pytest.raises(Exception):
            Review.objects.create(product=product, buyer=buyer, stars=3, comment='Dup')

    def test_str_representation(self, buyer, product, completed_order):
        r = Review.objects.create(product=product, buyer=buyer, stars=4, comment='Nice')
        assert '4' in str(r)
        assert buyer.email in str(r)


# ─── API Tests ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReviewAPI:
    def test_product_reviews_public(self, api_client, buyer, product, completed_order):
        Review.objects.create(product=product, buyer=buyer, stars=5, comment='Great')
        url = reverse('product-reviews', kwargs={'product_id': product.id})
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data['count'] == 1
        assert resp.data['average_rating'] == 5.0

    def test_buyer_can_create_review(self, buyer_client, buyer, product, completed_order):
        url = reverse('review-create')
        data = {'product': str(product.id), 'stars': 4, 'comment': 'Very good!'}
        resp = buyer_client.post(url, data, format='json')
        assert resp.status_code == 201

    def test_buyer_cannot_review_unordered_product(self, buyer_client, product):
        url = reverse('review-create')
        data = {'product': str(product.id), 'stars': 3, 'comment': 'Meh'}
        resp = buyer_client.post(url, data, format='json')
        assert resp.status_code == 400

    def test_unauthenticated_cannot_review(self, api_client, product):
        url = reverse('review-create')
        data = {'product': str(product.id), 'stars': 5, 'comment': ''}
        resp = api_client.post(url, data, format='json')
        assert resp.status_code == 401

    def test_seller_cannot_create_review(self, seller_client, product, completed_order):
        url = reverse('review-create')
        data = {'product': str(product.id), 'stars': 5, 'comment': 'Self-review attempt'}
        resp = seller_client.post(url, data, format='json')
        assert resp.status_code == 403
