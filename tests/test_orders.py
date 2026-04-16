"""tests/test_orders.py — Order model & checkout endpoint tests."""
import pytest
from decimal import Decimal
from django.urls import reverse
from unittest.mock import patch

from orders.models import Order, OrderItem


# ─── Model Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestOrderModel:
    def test_order_str(self, completed_order):
        s = str(completed_order)
        assert 'buyer@test.com' in s
        assert 'delivered' in s

    def test_order_item_subtotal_auto_calculated(self, completed_order):
        item = completed_order.items.first()
        assert item.subtotal == item.unit_price * item.quantity

    def test_status_choices_are_valid(self):
        statuses = [s[0] for s in Order.STATUS_CHOICES]
        assert 'pending' in statuses
        assert 'delivered' in statuses
        assert 'cancelled' in statuses


# ─── Checkout API Tests ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCheckoutAPI:
    def test_checkout_requires_auth(self, api_client):
        resp = api_client.post(reverse('order-checkout'), {})
        assert resp.status_code == 401

    def test_seller_cannot_checkout(self, seller_client):
        resp = seller_client.post(reverse('order-checkout'), {})
        assert resp.status_code == 403

    def test_checkout_empty_cart_fails(self, buyer_client):
        resp = buyer_client.post(
            reverse('order-checkout'),
            {'shipping_address': '123 Test St'},
            format='json',
        )
        assert resp.status_code == 400

    @patch('orders.views.stripe.PaymentIntent.create')
    def test_checkout_creates_order(self, mock_stripe, buyer_client, cart_with_item, product, buyer):
        class MockIntent:
            id = 'PAY-001'
            client_secret = 'secret_123'
        
        mock_stripe.return_value = MockIntent()

        initial_stock = product.stock_qty  # 50
        resp = buyer_client.post(
            reverse('order-checkout'),
            {'shipping_address': '99 Market Lane', 'payment_ref': 'PAY-001'},
            format='json',
        )
        assert resp.status_code == 201
        assert resp.data['status'] == 'success'

        order = Order.objects.get(buyer=buyer)
        assert order.status == 'pending'
        assert order.items.count() == 1

        # Stock decremented
        product.refresh_from_db()
        assert product.stock_qty == initial_stock - 2  # quantity was 2

        # Cart is cleared
        from cart.models import CartItem
        assert CartItem.objects.filter(cart__buyer=buyer).count() == 0

    def test_checkout_insufficient_stock_fails(self, buyer_client, buyer_cart, product):
        from cart.models import CartItem
        CartItem.objects.create(
            cart=buyer_cart,
            product=product,
            quantity=product.stock_qty + 100,  # exceeds stock
            price_at_add=product.price,
        )
        resp = buyer_client.post(
            reverse('order-checkout'),
            {'shipping_address': '123 Test St'},
            format='json',
        )
        assert resp.status_code == 400
        assert 'stock' in resp.data['message'].lower()


# ─── Order List / Detail Tests ────────────────────────────────────────────────

@pytest.mark.django_db
class TestOrderListAPI:
    def test_buyer_sees_own_orders(self, buyer_client, completed_order):
        resp = buyer_client.get(reverse('order-list'))
        assert resp.status_code == 200
        ids = [r['id'] for r in resp.data['results']]
        assert str(completed_order.id) in ids

    def test_buyer_cannot_see_others_orders(self, buyer_client, admin_user):
        from orders.models import Order
        other_order = Order.objects.create(
            buyer=admin_user,
            total_amount=Decimal('50.00'),
            status='pending',
            shipping_address='Other address',
        )
        resp = buyer_client.get(reverse('order-list'))
        ids = [r['id'] for r in resp.data['results']]
        assert str(other_order.id) not in ids


# ─── Status Transition Tests ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestOrderStatusTransition:
    def test_invalid_transition_rejected(self, admin_client, completed_order):
        # delivered → processing is invalid
        url = reverse('order-status-update', kwargs={'pk': completed_order.id})
        resp = admin_client.patch(url, {'status': 'processing'}, format='json')
        assert resp.status_code == 400

    def test_valid_transition_accepted(self, admin_client, buyer, product):
        order = Order.objects.create(
            buyer=buyer,
            total_amount=Decimal('100'),
            status='pending',
            shipping_address='Addr',
        )
        url = reverse('order-status-update', kwargs={'pk': order.id})
        resp = admin_client.patch(url, {'status': 'processing'}, format='json')
        assert resp.status_code == 200
        order.refresh_from_db()
        assert order.status == 'processing'
