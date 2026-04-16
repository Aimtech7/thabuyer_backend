"""tests/test_products.py — Product model & endpoint tests."""
import pytest
from decimal import Decimal
from django.urls import reverse
from products.models import Product, Category


# ─── Model Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductModel:
    def test_product_creation(self, product):
        assert product.name == 'Wireless Headphones'
        assert product.price == Decimal('199.99')
        assert product.in_stock is True
        assert product.is_active is True

    def test_out_of_stock_property(self, product_out_of_stock):
        assert product_out_of_stock.in_stock is False

    def test_str_representation(self, product):
        assert 'WH-001' in str(product)

    def test_price_history_created_on_save(self, product):
        from pricing.models import PriceHistory
        assert PriceHistory.objects.filter(product=product).exists()

    def test_price_history_updated_on_price_change(self, product):
        from pricing.models import PriceHistory
        initial_count = PriceHistory.objects.filter(product=product).count()
        product.price = Decimal('179.99')
        product.save()
        assert PriceHistory.objects.filter(product=product).count() == initial_count + 1

    def test_sku_uniqueness(self, product, seller_user, seller_profile, category):
        with pytest.raises(Exception):
            Product.objects.create(
                seller=seller_user, category=category,
                name='Another Product', price=Decimal('50'),
                stock_qty=10, SKU='WH-001',
            )


# ─── API Tests ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductListAPI:
    def test_list_is_public(self, api_client, product):
        url = reverse('product-list')
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data['count'] >= 1

    def test_inactive_products_excluded(self, api_client, product):
        product.is_active = False
        product.save()
        url = reverse('product-list')
        resp = api_client.get(url)
        ids = [r['id'] for r in resp.data['results']]
        assert str(product.id) not in ids

    def test_search_by_name(self, api_client, product):
        url = reverse('product-search') + '?q=Wireless'
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert any('Wireless' in r['name'] for r in resp.data['results'])

    def test_search_empty_query_returns_empty(self, api_client):
        url = reverse('product-search') + '?q='
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data['count'] == 0


@pytest.mark.django_db
class TestProductCreateAPI:
    def test_seller_can_create_product(self, seller_client, seller_profile, category):
        url = reverse('product-create')
        data = {
            'name': 'Bluetooth Speaker',
            'description': 'Great sound quality.',
            'price': '89.99',
            'stock_qty': 100,
            'SKU': 'BS-001',
            'category': str(category.id),
        }
        resp = seller_client.post(url, data, format='json')
        assert resp.status_code == 201

    def test_buyer_cannot_create_product(self, buyer_client, category, seller_profile):
        url = reverse('product-create')
        data = {
            'name': 'Test Product',
            'price': '50.00',
            'stock_qty': 10,
            'SKU': 'TP-001',
        }
        resp = buyer_client.post(url, data, format='json')
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create(self, api_client):
        url = reverse('product-create')
        resp = api_client.post(url, {}, format='json')
        assert resp.status_code == 401


@pytest.mark.django_db
class TestProductCompareAPI:
    def test_compare_returns_comparison_table(self, api_client, product):
        url = reverse('product-compare', kwargs={'pk': product.id})
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert 'comparison' in resp.data
        assert 'lowest_price' in resp.data

    def test_compare_nonexistent_product_404(self, api_client):
        import uuid
        url = reverse('product-compare', kwargs={'pk': uuid.uuid4()})
        resp = api_client.get(url)
        assert resp.status_code == 404
