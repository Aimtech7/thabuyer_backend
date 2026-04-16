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

                # Send notification email (async, non-blocking)
                send_price_alert_email.delay(
                    buyer_email=alert.buyer.email,
                    buyer_name=alert.buyer.name,
                    product_name=alert.product.name,
                    target_price=str(alert.target_price),
                    current_price=str(alert.product.price),
                )
                triggered_count += 1
        except Exception as e:
            logger.exception('Error processing alert %s: %s', alert.id, e)

    logger.info('Price alert check complete. Triggered: %d', triggered_count)
    return {'triggered': triggered_count}


@shared_task(name='pricing.tasks.send_price_alert_email')
def send_price_alert_email(buyer_email, buyer_name, product_name, target_price, current_price):
    """Send email notification when a price alert is triggered."""
    from django.core.mail import send_mail
    from django.conf import settings

    subject = f'🔔 Price Alert: {product_name} is now ${current_price}!'
    message = (
        f'Hi {buyer_name},\n\n'
        f'Great news! The price of "{product_name}" has dropped to ${current_price},\n'
        f'which meets your target price of ${target_price}.\n\n'
        f'Visit the platform to purchase before it goes back up!\n\n'
        f'— The E-Commerce Team'
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[buyer_email],
            fail_silently=False,
        )
        logger.info('Price alert email sent to %s', buyer_email)
    except Exception as e:
        logger.exception('Failed to send price alert email to %s: %s', buyer_email, e)
