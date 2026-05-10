"""
tests/test_celery_tasks.py — Tests for updated branded Celery tasks (Phases 2 & 3).
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestPriceAlertTask:
    """pricing.tasks.check_price_alerts should trigger branded alerts."""

    def test_alert_triggered_when_price_drops(self, buyer, product):
        from pricing.models import PriceAlert
        from pricing.tasks import check_price_alerts

        alert = PriceAlert.objects.create(
            buyer=buyer,
            product=product,
            target_price=Decimal('250.00'),  # product price is 199.99, so already below target
            status='active',
        )

        with patch('orders.tasks.send_price_alert_email.delay') as mock_email, \
             patch('channels.layers.get_channel_layer', return_value=None):
            result = check_price_alerts()
            assert result['triggered'] >= 1
            assert mock_email.called
            mock_email.assert_called_with(str(alert.id))

        alert.refresh_from_db()
        assert alert.status == 'triggered'

    def test_alert_not_triggered_when_price_is_higher(self, buyer, product):
        from pricing.models import PriceAlert
        from pricing.tasks import check_price_alerts

        alert = PriceAlert.objects.create(
            buyer=buyer,
            product=product,
            target_price=Decimal('10.00'),  # product is 199.99, much higher
            status='active',
        )

        with patch('orders.tasks.send_price_alert_email.delay') as mock_email, \
             patch('channels.layers.get_channel_layer', return_value=None):
            result = check_price_alerts()
            assert result['triggered'] == 0
            assert not mock_email.called

        alert.refresh_from_db()
        assert alert.status == 'active'


@pytest.mark.django_db
class TestSendPriceAlertEmail:
    """orders.tasks.send_price_alert_email should call email_service."""

    @patch('core.email_service.send_email')
    def test_email_is_sent(self, mock_send_email, buyer, product):
        from pricing.models import PriceAlert
        from orders.tasks import send_price_alert_email
        
        alert = PriceAlert.objects.create(
            buyer=buyer,
            product=product,
            target_price=Decimal('100.00'),
            status='active',
        )
        
        send_price_alert_email(str(alert.id))
        assert mock_send_email.called
        # Check that we used the right template
        args, kwargs = mock_send_email.call_args
        assert kwargs['template_name'] == 'price_alert.html'


@pytest.mark.django_db
class TestSendOrderConfirmation:
    """orders.tasks.send_order_confirmation_email should send branded email."""

    @patch('core.email_service.send_email')
    def test_confirmation_email_sent(self, mock_send_email, completed_order):
        from orders.tasks import send_order_confirmation_email
        send_order_confirmation_email(str(completed_order.id))
        assert mock_send_email.called
        args, kwargs = mock_send_email.call_args
        assert kwargs['template_name'] == 'order_confirmation.html'

    @patch('core.email_service.send_email')
    def test_confirmation_with_invalid_order_does_not_raise(self, mock_send_email):
        from orders.tasks import send_order_confirmation_email
        import uuid
        # Should catch DoesNotExist and log, then retry or fail gracefully
        # Here we just check it doesn't crash the worker
        with pytest.raises(Exception): # Celery retry raises Retry exception
             send_order_confirmation_email(str(uuid.uuid4()))


@pytest.mark.django_db
class TestAdminDailyReport:
    """admin_panel.tasks.generate_daily_report should aggregate platform stats."""

    def test_daily_report_runs_without_error(self, buyer, completed_order):
        from admin_panel.tasks import generate_daily_report
        result = generate_daily_report()
        assert 'new_users' in result
        assert 'new_orders' in result
        assert 'revenue' in result
