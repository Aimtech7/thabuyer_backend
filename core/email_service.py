"""
core/email_service.py

Centralized email service for THA BUYER.
Handles template rendering, plain-text fallback generation, and queuing.
All public methods accept plain data dicts and return immediately (fire & forget).
"""
import logging
from datetime import date
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'https://thabuyer.com')
FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'THA BUYER <noreply@thabuyer.com>')
CURRENT_YEAR = date.today().year


def _base_context() -> dict:
    """Return context common to all email templates."""
    return {
        'frontend_url': FRONTEND_URL,
        'current_year': CURRENT_YEAR,
    }


def render_email(template_name: str, context: dict) -> tuple[str, str]:
    """
    Render an HTML email and generate a plain-text fallback.
    Returns (html_body, text_body)
    """
    ctx = {**_base_context(), **context}
    html_body = render_to_string(f'emails/{template_name}', ctx)
    text_body = strip_tags(html_body).strip()
    return html_body, text_body


def send_email(
    subject: str,
    to: list[str],
    template_name: str,
    context: dict,
    *,
    from_email: str = None,
    reply_to: list[str] = None,
) -> bool:
    """
    Render and send a branded HTML email with plain-text fallback.
    Returns True on success, False on failure.
    """
    try:
        html_body, text_body = render_email(template_name, context)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email or FROM_EMAIL,
            to=to,
            reply_to=reply_to,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
        logger.info('email_sent', extra={'subject': subject, 'to': to, 'template': template_name})
        return True
    except Exception as exc:
        logger.error(
            'email_send_failed',
            extra={'subject': subject, 'to': to, 'template': template_name, 'error': str(exc)},
            exc_info=True,
        )
        return False


# ─── Convenience senders ─────────────────────────────────────────────────────

def send_order_confirmation(order, buyer) -> bool:
    """Send the buyer their order confirmation email."""
    items = [
        {
            'product_name': item.product.name if item.product else 'Deleted Product',
            'seller_name': item.product.seller.name if item.product and item.product.seller else '—',
            'quantity': item.quantity,
            'subtotal': f'{item.subtotal:.2f}',
        }
        for item in order.items.select_related('product__seller').all()
    ]
    context = {
        'buyer_name': buyer.name or buyer.email,
        'order_number': getattr(order, 'order_number', f'TB-{str(order.id)[:8].upper()}'),
        'order_date': order.created_at.strftime('%B %d, %Y'),
        'items': items,
        'subtotal': f'{(order.total_amount + order.discount_amount):.2f}',
        'discount_amount': f'{order.discount_amount:.2f}',
        'shipping_display': 'Calculated at checkout',
        'total_amount': f'{order.total_amount:.2f}',
        'shipping_address': order.shipping_address,
        'estimated_delivery': '5–7 business days',
        'track_order_url': f'{FRONTEND_URL}/orders/{order.id}',
        'payment_ref': order.payment_ref,
    }
    return send_email(
        subject=f'Your THA BUYER order {context["order_number"]} has been placed ✓',
        to=[buyer.email],
        template_name='order_confirmation.html',
        context=context,
    )


def send_seller_order_notification(order, seller, seller_items) -> bool:
    """Send the seller a new order alert for their items only."""
    formatted_items = [
        {
            'product_name': item.product.name if item.product else '—',
            'sku': item.product.SKU if item.product else '—',
            'quantity': item.quantity,
            'subtotal': f'{item.subtotal:.2f}',
            'seller_earnings': f'{item.seller_earnings:.2f}',
        }
        for item in seller_items
    ]
    seller_total = sum(item.subtotal for item in seller_items)
    commission_amount = sum(item.commission_amount for item in seller_items)
    seller_payout = sum(item.seller_earnings for item in seller_items)
    commission_rate = seller_items[0].commission_rate if seller_items else 5

    context = {
        'seller_name': seller.name or seller.email,
        'order_number': getattr(order, 'order_number', f'TB-{str(order.id)[:8].upper()}'),
        'order_date': order.created_at.strftime('%B %d, %Y'),
        'buyer_name': order.buyer.name or order.buyer.email,
        'shipping_address': order.shipping_address,
        'seller_items': formatted_items,
        'seller_total': f'{seller_total:.2f}',
        'commission_rate': f'{commission_rate:.0f}',
        'commission_amount': f'{commission_amount:.2f}',
        'seller_payout': f'{seller_payout:.2f}',
        'seller_dashboard_url': f'{FRONTEND_URL}/seller/dashboard',
    }
    return send_email(
        subject=f'New Order Received — Order {context["order_number"]}',
        to=[seller.email],
        template_name='seller_new_order.html',
        context=context,
    )


def send_order_shipped_notification(order, buyer) -> bool:
    """Send the buyer a shipment confirmation email."""
    items = [
        {
            'product_name': item.product.name if item.product else '—',
            'quantity': item.quantity,
            'subtotal': f'{item.subtotal:.2f}',
        }
        for item in order.items.select_related('product').all()
    ]
    context = {
        'buyer_name': buyer.name or buyer.email,
        'order_number': getattr(order, 'order_number', f'TB-{str(order.id)[:8].upper()}'),
        'shipped_date': order.updated_at.strftime('%B %d, %Y'),
        'tracking_number': order.tracking_number or 'Pending',
        'carrier': order.carrier or 'Our Logistics Partner',
        'estimated_delivery': '3–5 business days',
        'shipping_address': order.shipping_address,
        'items': items,
        'tracking_url': f'https://track.aftership.com/{order.tracking_number}' if order.tracking_number else FRONTEND_URL + '/orders/' + str(order.id),
        'order_detail_url': f'{FRONTEND_URL}/orders/{order.id}',
    }
    return send_email(
        subject=f'Your order {context["order_number"]} is on the way 🚚',
        to=[buyer.email],
        template_name='order_shipped.html',
        context=context,
    )


def send_price_alert_notification(alert, product) -> bool:
    """Send a price drop alert to a buyer."""
    buyer = alert.buyer
    old_price = float(alert.target_price) * 1.15  # approximate previous higher price
    savings = old_price - float(product.price)
    savings_pct = round((savings / old_price) * 100, 1) if old_price > 0 else 0

    context = {
        'buyer_name': buyer.name or buyer.email,
        'product_name': product.name,
        'seller_name': product.seller.name if product.seller else '—',
        'old_price': f'{old_price:.2f}',
        'current_price': f'{product.price:.2f}',
        'target_price': f'{alert.target_price:.2f}',
        'savings_amount': f'{savings:.2f}',
        'savings_percent': savings_pct,
        'product_url': f'{FRONTEND_URL}/products/{product.id}',
        'unsubscribe_url': f'{FRONTEND_URL}/settings/notifications',
    }
    return send_email(
        subject=f'Price Drop: {product.name} is now ${product.price:.2f}',
        to=[buyer.email],
        template_name='price_alert.html',
        context=context,
    )


def send_promotional_notification(recipients: list[str], coupon=None, headline: str = '', body: str = '', terms: str = '') -> bool:
    """Send a promotional/coupon email to a list of recipients."""
    context = {
        'promo_subject': headline,
        'promo_headline': headline,
        'promo_body': body,
        'coupon_code': coupon.code if coupon else None,
        'discount_type': coupon.discount_type if coupon else None,
        'discount_amount': f'{coupon.discount_amount:.0f}' if coupon else None,
        'valid_until': coupon.valid_until.strftime('%B %d, %Y') if coupon and getattr(coupon, 'valid_until', None) else None,
        'shop_url': FRONTEND_URL,
        'unsubscribe_url': f'{FRONTEND_URL}/settings/notifications',
        'terms': terms,
    }
    return send_email(
        subject=headline,
        to=recipients,
        template_name='promotional.html',
        context=context,
    )
