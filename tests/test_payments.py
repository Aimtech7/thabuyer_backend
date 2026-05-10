"""
tests/test_payments.py — Tests for Paystack Webhook verification (Phase 3).
"""
import json
import hmac
import hashlib
import pytest
from django.conf import settings


def _sign_payload(payload: dict, secret: str) -> str:
    raw = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    return hmac.new(secret.encode('utf-8'), raw, hashlib.sha512).hexdigest()


WEBHOOK_URL = '/api/v1/payments/webhook/'


@pytest.mark.django_db
class TestPaystackWebhook:
    """Paystack webhook with HMAC signature verification."""

    def _post_webhook(self, api_client, payload, secret=None):
        if secret is None:
            secret = getattr(settings, 'PAYSTACK_SECRET_KEY', 'sk_test_fake')
        raw = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        sig = hmac.new(secret.encode('utf-8'), raw, hashlib.sha512).hexdigest()
        return api_client.post(
            WEBHOOK_URL,
            data=raw,
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=sig,
        )

    def test_valid_signature_returns_200(self, api_client):
        payload = {'event': 'ping', 'data': {}}
        res = self._post_webhook(api_client, payload)
        assert res.status_code == 200

    def test_missing_signature_returns_400(self, api_client):
        payload = {'event': 'ping', 'data': {}}
        res = api_client.post(
            WEBHOOK_URL,
            data=json.dumps(payload),
            content_type='application/json',
        )
        assert res.status_code == 400

    def test_invalid_signature_returns_400(self, api_client):
        payload = {'event': 'ping', 'data': {}}
        raw = json.dumps(payload).encode('utf-8')
        res = api_client.post(
            WEBHOOK_URL,
            data=raw,
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='invalid_sig_abcdef',
        )
        assert res.status_code == 400

    def test_charge_success_updates_order(self, api_client, completed_order):
        """charge.success event should update order status to 'processing'."""
        completed_order.status = 'pending'
        completed_order.save()

        payload = {
            'event': 'charge.success',
            'data': {
                'reference': str(completed_order.id),
                'status': 'success',
                'amount': 39998,
            }
        }
        from unittest.mock import patch
        with patch('orders.tasks.send_order_confirmation_email.delay'), \
             patch('orders.tasks.send_seller_order_email.delay'):
            res = self._post_webhook(api_client, payload)
        assert res.status_code == 200

        from orders.models import Order
        updated = Order.objects.get(id=completed_order.id)
        assert updated.status == 'processing'
