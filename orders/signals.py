"""
orders/signals.py

Django signal receivers for automated email notifications.
- order_status_change → shipped email
- Uses Celery tasks for async execution
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender='orders.Order')
def capture_previous_status(sender, instance, **kwargs):
    """Capture the previous status before saving for transition detection."""
    if instance.pk:
        try:
            instance._prev_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            instance._prev_status = None
    else:
        instance._prev_status = None


@receiver(post_save, sender='orders.Order')
def on_order_status_change(sender, instance, created, **kwargs):
    """
    Trigger shipped email when order transitions to 'shipped', 'ready', or 'fulfilled'.
    """
    if created:
        return  # Confirmation email is triggered from webhook

    prev = getattr(instance, '_prev_status', None)
    current = instance.status

    SHIP_TRIGGERS = {'shipped', 'ready', 'fulfilled'}

    if current in SHIP_TRIGGERS and prev not in SHIP_TRIGGERS:
        logger.info(
            'order_status_trigger_ship_email',
            extra={'order_id': str(instance.id), 'prev': prev, 'current': current}
        )
        from orders.tasks import send_order_shipped_email
        send_order_shipped_email.delay(str(instance.id))
