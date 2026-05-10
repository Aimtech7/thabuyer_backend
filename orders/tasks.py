"""
orders/tasks.py

Celery tasks for the THA BUYER email notification system.
All tasks are async, retryable, and logged.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


# ─── ORDER CONFIRMATION ───────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60, name='orders.send_order_confirmation_email')
def send_order_confirmation_email(self, order_id: str) -> dict:
    """
    Send the buyer a branded order confirmation email.
    Triggered on Paystack charge.success webhook.
    """
    try:
        from orders.models import Order
        from core.email_service import send_order_confirmation

        order = Order.objects.select_related('buyer').prefetch_related('items__product__seller').get(id=order_id)
        success = send_order_confirmation(order, order.buyer)
        result = {'status': 'sent' if success else 'failed', 'order_id': order_id}
        logger.info('task_order_confirmation', extra=result)
        return result
    except Exception as exc:
        logger.error('task_order_confirmation_error', extra={'order_id': order_id, 'error': str(exc)}, exc_info=True)
        raise self.retry(exc=exc)


# ─── SELLER NOTIFICATION ──────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60, name='orders.send_seller_order_email')
def send_seller_order_email(self, order_id: str, seller_id: str) -> dict:
    """
    Notify a specific seller about their items in a new order.
    One task per seller — called for each unique seller in an order.
    """
    try:
        from orders.models import Order, OrderItem
        from users.models import User
        from core.email_service import send_seller_order_notification

        order = Order.objects.select_related('buyer').get(id=order_id)
        seller = User.objects.get(id=seller_id)
        seller_items = list(
            OrderItem.objects
            .filter(order=order, product__seller=seller)
            .select_related('product__seller')
        )
        if not seller_items:
            return {'status': 'skipped', 'reason': 'no_items', 'seller_id': seller_id}

        success = send_seller_order_notification(order, seller, seller_items)
        result = {'status': 'sent' if success else 'failed', 'order_id': order_id, 'seller_id': seller_id}
        logger.info('task_seller_order_email', extra=result)
        return result
    except Exception as exc:
        logger.error('task_seller_order_email_error', extra={'order_id': order_id, 'seller_id': seller_id, 'error': str(exc)}, exc_info=True)
        raise self.retry(exc=exc)


# ─── SHIPPED NOTIFICATION ─────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60, name='orders.send_order_shipped_email')
def send_order_shipped_email(self, order_id: str) -> dict:
    """
    Notify the buyer that their order has shipped.
    Triggered when order status transitions to 'shipped'.
    """
    try:
        from orders.models import Order
        from core.email_service import send_order_shipped_notification

        order = Order.objects.select_related('buyer').prefetch_related('items__product').get(id=order_id)
        success = send_order_shipped_notification(order, order.buyer)
        result = {'status': 'sent' if success else 'failed', 'order_id': order_id}
        logger.info('task_order_shipped_email', extra=result)
        return result
    except Exception as exc:
        logger.error('task_order_shipped_email_error', extra={'order_id': order_id, 'error': str(exc)}, exc_info=True)
        raise self.retry(exc=exc)


# ─── PRICE ALERT ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=120, name='orders.send_price_alert_email')
def send_price_alert_email(self, alert_id: str) -> dict:
    """
    Send a branded price drop alert to the buyer.
    Triggered from pricing.tasks.check_price_alerts.
    """
    try:
        from pricing.models import PriceAlert
        from core.email_service import send_price_alert_notification

        alert = PriceAlert.objects.select_related('buyer', 'product__seller').get(id=alert_id)
        success = send_price_alert_notification(alert, alert.product)
        result = {'status': 'sent' if success else 'failed', 'alert_id': alert_id}
        logger.info('task_price_alert_email', extra=result)
        return result
    except Exception as exc:
        logger.error('task_price_alert_email_error', extra={'alert_id': alert_id, 'error': str(exc)}, exc_info=True)
        raise self.retry(exc=exc)


# ─── PROMOTIONAL EMAIL ────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=300, name='orders.send_promotional_email')
def send_promotional_email(self, coupon_id: str = None, headline: str = '', body: str = '', terms: str = '') -> dict:
    """
    Send a promotional/coupon email to all active buyers.
    Called from promotions signal on active coupon creation.
    """
    try:
        from users.models import User
        from core.email_service import send_promotional_notification

        coupon = None
        if coupon_id:
            from promotions.models import Coupon
            coupon = Coupon.objects.filter(id=coupon_id).first()

        recipients = list(
            User.objects.filter(role='buyer', is_active=True)
            .values_list('email', flat=True)[:500]  # Safety cap
        )

        if not recipients:
            return {'status': 'skipped', 'reason': 'no_recipients'}

        success = send_promotional_notification(recipients, coupon=coupon, headline=headline, body=body, terms=terms)
        result = {'status': 'sent' if success else 'failed', 'recipient_count': len(recipients)}
        logger.info('task_promotional_email', extra=result)
        return result
    except Exception as exc:
        logger.error('task_promotional_email_error', extra={'error': str(exc)}, exc_info=True)
        raise self.retry(exc=exc)


# ─── LEGACY ALIAS ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60, name='orders.send_order_receipt')
def send_order_receipt(self, order_id: str) -> dict:
    """Legacy task — delegates to send_order_confirmation_email."""
    return send_order_confirmation_email.apply(args=[order_id]).get()
