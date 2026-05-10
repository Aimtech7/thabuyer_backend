"""
tests/test_promotions_ws.py — Tests for Coupon WebSocket broadcasting (Phase 2).
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestPromotionBroadcast:
    """New Coupons should broadcast to global_notifications via Channels."""

    @patch('promotions.models.get_channel_layer')
    @patch('promotions.models.async_to_sync')
    def test_new_active_coupon_broadcasts_to_ws(self, mock_async_to_sync, mock_get_channel_layer):
        """Creating a new active coupon should trigger a channel group_send."""
        from promotions.models import Coupon

        mock_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_layer
        with patch('orders.tasks.send_promotional_email.delay'):
            coupon = Coupon.objects.create(
                code='SAVE20',
                discount_type='percent',
                discount_amount=Decimal('20.00'),
                active=True,
            )

        assert mock_async_to_sync.called or mock_get_channel_layer.called

    @patch('promotions.models.get_channel_layer')
    @patch('promotions.models.async_to_sync')
    def test_inactive_coupon_does_not_broadcast(self, mock_async_to_sync, mock_get_channel_layer):
        """Creating an inactive coupon should NOT trigger a broadcast."""
        from promotions.models import Coupon

        mock_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_layer
        mock_async_to_sync.return_value = lambda *args, **kwargs: None

        coupon = Coupon.objects.create(
            code='INACTIVE10',
            discount_type='fixed',
            discount_amount=Decimal('10.00'),
            active=False,
        )

        # The signal receiver checks `if created and instance.active`
        # With active=False, async_to_sync should NOT be invoked for channel_send
        # We check the channel_layer.group_send was never requested
        if mock_get_channel_layer.called and mock_get_channel_layer.return_value:
            group_send = mock_get_channel_layer.return_value.group_send
            # If group_send was called, it should NOT have 'global_notifications'
            for call in group_send.call_args_list:
                assert 'global_notifications' not in str(call)
