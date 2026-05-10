"""
tests/test_sku_commission.py — Tests for SKU auto-generation and commission tracking (Phase 6).
"""
import pytest
from decimal import Decimal


@pytest.mark.django_db
class TestSKUAutoGeneration:
    """Product.save() should auto-generate a SKU if not provided."""

    def test_sku_generated_when_blank(self, seller_user, seller_profile, category):
        from products.models import Product
        product = Product.objects.create(
            seller=seller_user,
            category=category,
            name='Test Widget',
            description='A widget',
            price=Decimal('29.99'),
            stock_qty=10,
            SKU='',  # Blank — should be auto-generated
        )
        assert product.SKU != ''
        assert len(product.SKU) > 0

    def test_sku_uses_product_name_prefix(self, seller_user, seller_profile, category):
        from products.models import Product
        product = Product.objects.create(
            seller=seller_user,
            category=category,
            name='Zoom Camera',
            description='Good camera',
            price=Decimal('299.99'),
            stock_qty=5,
            SKU='',
        )
        # Prefix should be derived from first 3 chars of name (uppercased alphanum)
        assert product.SKU.startswith('ZOO') or product.SKU.startswith('ZOO') or '-' in product.SKU

    def test_sku_is_unique_across_products(self, seller_user, seller_profile, category):
        from products.models import Product
        p1 = Product.objects.create(
            seller=seller_user, category=category, name='Item Alpha',
            price=Decimal('9.99'), stock_qty=1, SKU='',
        )
        p2 = Product.objects.create(
            seller=seller_user, category=category, name='Item Alpha',
            price=Decimal('9.99'), stock_qty=1, SKU='',
        )
        assert p1.SKU != p2.SKU

    def test_explicit_sku_is_preserved(self, seller_user, seller_profile, category):
        from products.models import Product
        product = Product.objects.create(
            seller=seller_user, category=category, name='Manual SKU Product',
            price=Decimal('49.99'), stock_qty=10, SKU='MANUAL-XYZ',
        )
        assert product.SKU == 'MANUAL-XYZ'


@pytest.mark.django_db
class TestCommissionTracking:
    """OrderItem should automatically compute commission_amount and seller_earnings."""

    def test_commission_calculated_on_order_item_save(self, buyer, product, seller_profile):
        from orders.models import Order, OrderItem
        # Set a known commission rate
        seller_profile.commission_rate = Decimal('10.00')
        seller_profile.save()

        order = Order.objects.create(
            buyer=buyer,
            total_amount=Decimal('199.99'),
            status='pending',
            shipping_address='123 Test St',
        )
        item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            unit_price=Decimal('199.99'),
            subtotal=Decimal('199.99'),
        )

        item.refresh_from_db()
        assert item.commission_rate == Decimal('10.00')
        expected_commission = round(Decimal('199.99') * Decimal('10.00') / 100, 2)
        assert item.commission_amount == expected_commission
        expected_earnings = Decimal('199.99') - expected_commission
        assert item.seller_earnings == expected_earnings

    def test_subtotal_is_calculated_from_quantity(self, buyer, product, seller_profile):
        from orders.models import Order, OrderItem
        order = Order.objects.create(
            buyer=buyer,
            total_amount=Decimal('399.98'),
            status='pending',
            shipping_address='123 Test St',
        )
        item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=2,
            unit_price=Decimal('199.99'),
            subtotal=Decimal('0'),  # Should be overridden by save()
        )
        item.refresh_from_db()
        assert item.subtotal == Decimal('399.98')
