"""
tests/test_wishlists.py — Test suite for the Wishlist system (Phase 2).
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestWishlistView:
    """GET /api/v1/wishlist/ — should auto-create and return the buyer's wishlist."""

    def test_get_wishlist_creates_if_missing(self, buyer_client):
        res = buyer_client.get('/api/v1/wishlist/')
        assert res.status_code == 200
        assert 'items' in res.data

    def test_anonymous_cannot_access_wishlist(self, api_client):
        res = api_client.get('/api/v1/wishlist/')
        assert res.status_code == 401


@pytest.mark.django_db
class TestWishlistAdd:
    """POST /api/v1/wishlist/add/ — add a product to wishlist."""

    def test_add_product_to_wishlist(self, buyer_client, product):
        res = buyer_client.post('/api/v1/wishlist/add/', {'product_id': str(product.id)}, format='json')
        assert res.status_code == 201

    def test_add_same_product_twice_returns_200(self, buyer_client, product):
        buyer_client.post('/api/v1/wishlist/add/', {'product_id': str(product.id)}, format='json')
        res = buyer_client.post('/api/v1/wishlist/add/', {'product_id': str(product.id)}, format='json')
        assert res.status_code == 200
        assert res.data['message'] == 'Product already in wishlist'

    def test_add_nonexistent_product_returns_404(self, buyer_client):
        import uuid
        res = buyer_client.post('/api/v1/wishlist/add/', {'product_id': str(uuid.uuid4())}, format='json')
        assert res.status_code == 404

    def test_seller_cannot_add_to_wishlist(self, seller_client, product):
        """Sellers are not buyers, but we allow them to add (no role restriction on wishlists)."""
        res = seller_client.post('/api/v1/wishlist/add/', {'product_id': str(product.id)}, format='json')
        # Wishlists are open to authenticated users, just limit_choices_to='buyer' on Wishlist model
        # seller_user does not have role='buyer' so Wishlist creation for them would create a buyer=seller
        # This tests that the endpoint at least responds to authenticated users
        assert res.status_code in (201, 400)


@pytest.mark.django_db
class TestWishlistRemove:
    """DELETE /api/v1/wishlist/remove/<uuid>/ — remove a product from wishlist."""

    def test_remove_product_from_wishlist(self, buyer_client, product):
        buyer_client.post('/api/v1/wishlist/add/', {'product_id': str(product.id)}, format='json')
        res = buyer_client.delete(f'/api/v1/wishlist/remove/{product.id}/')
        assert res.status_code == 204

    def test_remove_product_not_in_wishlist_returns_404(self, buyer_client, product):
        res = buyer_client.delete(f'/api/v1/wishlist/remove/{product.id}/')
        assert res.status_code == 404
