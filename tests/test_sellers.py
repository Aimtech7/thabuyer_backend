"""tests/test_sellers.py — Seller profile model & endpoint tests."""
import pytest
from decimal import Decimal
from django.urls import reverse
from sellers.models import SellerProfile


# ─── Model Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSellerProfileModel:
    def test_seller_profile_creation(self, seller_profile):
        assert seller_profile.business_name == 'Test Store'
        assert seller_profile.verified is True
        assert seller_profile.rating_avg == Decimal('0.00')
        assert seller_profile.rating_count == 0

    def test_str_representation(self, seller_profile):
        assert 'Test Store' in str(seller_profile)
        assert '✓' in str(seller_profile)

    def test_unverified_str_has_pending(self, seller_user):
        profile = SellerProfile.objects.create(
            user=seller_user,
            business_name='Pending Store',
            verified=False,
        )
        assert 'pending' in str(profile)

    def test_update_rating_running_average(self, seller_profile):
        seller_profile.update_rating(4.0)
        assert seller_profile.rating_count == 1
        assert seller_profile.rating_avg == Decimal('4.00')

        seller_profile.update_rating(2.0)
        assert seller_profile.rating_count == 2
        assert seller_profile.rating_avg == Decimal('3.00')

    def test_update_rating_multiple(self, seller_profile):
        for stars in [5, 4, 3, 2, 1]:
            seller_profile.update_rating(stars)
        # Average of 5+4+3+2+1 = 15/5 = 3.0
        assert seller_profile.rating_avg == Decimal('3.00')
        assert seller_profile.rating_count == 5

    def test_commission_rate_default(self, seller_profile):
        assert seller_profile.commission_rate == Decimal('5.00')


# ─── API Tests ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSellerDashboardAPI:
    def test_dashboard_requires_seller_role(self, buyer_client):
        resp = buyer_client.get(reverse('seller-dashboard'))
        assert resp.status_code == 403

    def test_seller_gets_dashboard(self, seller_client, seller_profile, product):
        resp = seller_client.get(reverse('seller-dashboard'))
        assert resp.status_code == 200
        data = resp.data['data']
        assert 'profile' in data
        assert 'total_products' in data
        assert 'total_revenue' in data
        assert data['total_products'] == 1

    def test_seller_products_list(self, seller_client, seller_profile, product):
        resp = seller_client.get(reverse('seller-products'))
        assert resp.status_code == 200
        assert len(resp.data['data']) == 1
        assert resp.data['data'][0]['SKU'] == 'WH-001'

    def test_buyer_cannot_access_seller_products(self, buyer_client):
        resp = buyer_client.get(reverse('seller-products'))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access_dashboard(self, api_client):
        resp = api_client.get(reverse('seller-dashboard'))
        assert resp.status_code == 401

    def test_seller_profile_view(self, seller_client, seller_profile):
        resp = seller_client.get(reverse('seller-profile'))
        assert resp.status_code == 200
        assert resp.data['business_name'] == 'Test Store'

    def test_seller_can_update_profile(self, seller_client, seller_profile):
        resp = seller_client.patch(
            reverse('seller-profile'),
            {'business_description': 'Updated description'},
            format='json',
        )
        assert resp.status_code == 200
        seller_profile.refresh_from_db()
        assert seller_profile.business_description == 'Updated description'

    def test_seller_cannot_modify_own_rating(self, seller_client, seller_profile):
        """Rating avg must only change via the update_rating() method, not API."""
        resp = seller_client.patch(
            reverse('seller-profile'),
            {'rating_avg': '5.00', 'commission_rate': '0.01'},
            format='json',
        )
        seller_profile.refresh_from_db()
        # These are read-only fields; they should not change
        assert seller_profile.rating_avg == Decimal('0.00')
        assert seller_profile.commission_rate == Decimal('5.00')
