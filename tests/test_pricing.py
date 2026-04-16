"""tests/test_pricing.py — PriceHistory & PriceAlert model/API tests."""
import pytest
from decimal import Decimal
from django.urls import reverse
from pricing.models import PriceHistory, PriceAlert


# ─── Model Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPriceHistoryModel:
    def test_price_history_auto_created_on_product_save(self, product):
        """Products auto-create a PriceHistory entry when first saved."""
        records = PriceHistory.objects.filter(product=product)
        assert records.exists()
        assert records.first().price == product.price

    def test_price_history_entry_on_price_change(self, product):
        initial_count = PriceHistory.objects.filter(product=product).count()
        product.price = Decimal('179.99')
        product.save()
        assert PriceHistory.objects.filter(product=product).count() == initial_count + 1

    def test_no_duplicate_on_non_price_save(self, product):
        """Saving without changing price must NOT create a new history record."""
        initial_count = PriceHistory.objects.filter(product=product).count()
        product.description = 'Updated description only'
        product.save()
        assert PriceHistory.objects.filter(product=product).count() == initial_count

    def test_price_history_ordering(self, product):
        product.price = Decimal('180.00')
        product.save()
        product.price = Decimal('160.00')
        product.save()
        records = PriceHistory.objects.filter(product=product).order_by('-recorded_at')
        assert records[0].price == Decimal('160.00')

    def test_str_representation(self, product):
        record = PriceHistory.objects.filter(product=product).first()
        assert product.name in str(record)


@pytest.mark.django_db
class TestPriceAlertModel:
    def test_price_alert_creation(self, buyer, product):
        alert = PriceAlert.objects.create(
            buyer=buyer,
            product=product,
            target_price=Decimal('150.00'),
        )
        assert alert.status == 'active'
        assert alert.triggered_at is None

    def test_one_active_alert_per_buyer_product(self, buyer, product):
        PriceAlert.objects.create(buyer=buyer, product=product, target_price=Decimal('150.00'))
        with pytest.raises(Exception):
            PriceAlert.objects.create(buyer=buyer, product=product, target_price=Decimal('140.00'))

    def test_str_representation(self, buyer, product):
        alert = PriceAlert.objects.create(
            buyer=buyer, product=product, target_price=Decimal('150.00')
        )
        assert buyer.email in str(alert)
        assert product.name in str(alert)


# ─── API Tests ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPriceHistoryAPI:
    def test_price_history_is_public(self, api_client, product):
        url = reverse('price-history', kwargs={'product_id': product.id})
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data['count'] >= 1

    def test_price_history_items_have_price_and_date(self, api_client, product):
        url = reverse('price-history', kwargs={'product_id': product.id})
        resp = api_client.get(url)
        record = resp.data['results'][0]
        assert 'price' in record
        assert 'recorded_at' in record


@pytest.mark.django_db
class TestPriceAlertAPI:
    def test_buyer_can_create_alert(self, buyer_client, product):
        url = reverse('price-alerts')
        data = {'product': str(product.id), 'target_price': '150.00'}
        resp = buyer_client.post(url, data, format='json')
        assert resp.status_code == 201

    def test_target_price_must_be_below_current_price(self, buyer_client, product):
        url = reverse('price-alerts')
        data = {'product': str(product.id), 'target_price': '999.99'}
        resp = buyer_client.post(url, data, format='json')
        assert resp.status_code == 400

    def test_seller_cannot_create_alert(self, seller_client, product):
        url = reverse('price-alerts')
        data = {'product': str(product.id), 'target_price': '100.00'}
        resp = seller_client.post(url, data, format='json')
        assert resp.status_code == 403

    def test_buyer_can_list_own_alerts(self, buyer_client, buyer, product):
        PriceAlert.objects.create(
            buyer=buyer, product=product, target_price=Decimal('150.00')
        )
        resp = buyer_client.get(reverse('price-alerts'))
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_buyer_can_cancel_alert(self, buyer_client, buyer, product):
        alert = PriceAlert.objects.create(
            buyer=buyer, product=product, target_price=Decimal('150.00')
        )
        url = reverse('price-alert-cancel', kwargs={'pk': alert.id})
        resp = buyer_client.delete(url)
        assert resp.status_code == 200
        alert.refresh_from_db()
        assert alert.status == 'cancelled'

    def test_duplicate_alert_rejected(self, buyer_client, buyer, product):
        PriceAlert.objects.create(
            buyer=buyer, product=product, target_price=Decimal('150.00')
        )
        url = reverse('price-alerts')
        data = {'product': str(product.id), 'target_price': '140.00'}
        resp = buyer_client.post(url, data, format='json')
        assert resp.status_code == 400
