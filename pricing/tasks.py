"""pricing/tasks.py — Celery tasks for price alert checking."""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='pricing.tasks.check_price_alerts')
def check_price_alerts():
    """
    Scan all active price alerts. If a product's current price
    has dropped to or below the target price, trigger the alert.
    """
    from .models import PriceAlert

    active_alerts = PriceAlert.objects.filter(
        status='active'
    ).select_related('buyer', 'product')

    triggered_count = 0
    for alert in active_alerts:
        try:
            if alert.product.price <= alert.target_price:
                alert.status = 'triggered'
                alert.triggered_at = timezone.now()
                alert.save(update_fields=['status', 'triggered_at'])

                # Send branded notification email (async, non-blocking)
                from orders.tasks import send_price_alert_email
                send_price_alert_email.delay(str(alert.id))
                
                # Push WebSocket notification
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'user_{alert.buyer.id}',
                        {
                            'type': 'price_alert_triggered',
                            'message': f'Price Alert: {alert.product.name} has dropped to ${alert.product.price}',
                            'product_id': str(alert.product.id),
                            'current_price': str(alert.product.price)
                        }
                    )
                    
                triggered_count += 1
        except Exception as e:
            logger.exception('Error processing alert %s: %s', alert.id, e)

    logger.info('Price alert check complete. Triggered: %d', triggered_count)
    return {'triggered': triggered_count}
