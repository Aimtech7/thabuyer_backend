"""tests/test_cart.py — Cart model & endpoint tests."""
import pytest
from decimal import Decimal
from django.urls import reverse
from cart.models import Cart, CartItem


# ─── Model Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCartModel:
    def test_cart_created_with_buyer(self, buyer_cart, buyer):
        assert buyer_cart.buyer == buyer

    def test_cart_total_is_correct(self, cart_with_item):
        # 2 × 199.99 = 399.98
        assert cart_with_item.total == Decimal('399.98')

    def test_cart_item_count(self, cart_with_item):
        assert cart_with_item.item_count == 1

    def test_cart_item_subtotal(self, cart_with_item):
        item = cart_with_item.items.first()
        assert item.subtotal == Decimal('399.98')

    def test_empty_cart_total_is_zero(self, buyer_cart):
        assert buyer_cart.total == 0

    def test_str_representation(self, buyer_cart, buyer):
        assert buyer.email in str(buyer_cart)


# ─── API Tests ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCartAPI:
    def test_get_cart_requires_auth(self, api_client):
        resp = api_client.get(reverse('cart-detail'))
        assert resp.status_code == 401

    def test_seller_cannot_access_cart(self, seller_client):
        resp = seller_client.get(reverse('cart-detail'))
        assert resp.status_code == 403

    def test_buyer_gets_empty_cart(self, buyer_client):
        resp = buyer_client.get(reverse('cart-detail'))
        assert resp.status_code == 200
        assert resp.data['data']['item_count'] == 0

    def test_add_item_to_cart(self, buyer_client, product):
        url = reverse('cart-add')
        resp = buyer_client.post(url, {'product_id': str(product.id), 'quantity': 1}, format='json')
        assert resp.status_code == 200
        assert resp.data['data']['item_count'] == 1

    def test_add_item_increments_existing(self, buyer_client, product, buyer_cart):
        # Add once
        buyer_client.post(reverse('cart-add'), {'product_id': str(product.id), 'quantity': 2}, format='json')
        # Add again
        buyer_client.post(reverse('cart-add'), {'product_id': str(product.id), 'quantity': 3}, format='json')
        item = CartItem.objects.get(cart=buyer_cart, product=product)
        assert item.quantity == 5

    def test_add_exceeds_stock_returns_400(self, buyer_client, product):
        url = reverse('cart-add')
        resp = buyer_client.post(url, {'product_id': str(product.id), 'quantity': 9999}, format='json')
        assert resp.status_code == 400

    def test_add_inactive_product_returns_400(self, buyer_client, product):
        product.is_active = False
        product.save()
        url = reverse('cart-add')
        resp = buyer_client.post(url, {'product_id': str(product.id), 'quantity': 1}, format='json')
        assert resp.status_code == 400

    def test_remove_item_from_cart(self, buyer_client, cart_with_item, product):
        url = reverse('cart-remove')
        resp = buyer_client.delete(url, {'product_id': str(product.id)}, format='json')
        assert resp.status_code == 200
        assert CartItem.objects.filter(product=product).count() == 0

    def test_remove_nonexistent_item_returns_404(self, buyer_client, product):
        url = reverse('cart-remove')
        resp = buyer_client.delete(url, {'product_id': str(product.id)}, format='json')
        assert resp.status_code == 404

    def test_clear_cart(self, buyer_client, cart_with_item):
        resp = buyer_client.delete(reverse('cart-clear'))
        assert resp.status_code == 200
        assert CartItem.objects.filter(cart=cart_with_item).count() == 0
