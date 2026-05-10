"""
orders/utils.py

Human-readable order number generator.
Format: TB-YYYY-NNNN (e.g. TB-2026-0042)
Uses database-level atomic counter via F() to prevent race conditions.
"""
import logging
from datetime import date

logger = logging.getLogger(__name__)


def generate_order_number() -> str:
    """
    Generate a unique, human-readable order number in format TB-YYYY-NNNN.
    Uses atomic DB increment to prevent collisions under concurrent load.
    """
    from orders.models import OrderSequence

    year = date.today().year

    # Atomic get-or-create + increment
    seq, _ = OrderSequence.objects.get_or_create(year=year, defaults={'counter': 0})

    # Use F() expression + refresh to avoid race conditions
    from django.db.models import F
    OrderSequence.objects.filter(year=year).update(counter=F('counter') + 1)
    seq.refresh_from_db()

    order_number = f'TB-{year}-{seq.counter:04d}'
    logger.info('order_number_generated', extra={'order_number': order_number})
    return order_number
