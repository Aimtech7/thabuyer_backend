"""tests/test_admin_panel.py — Admin panel API tests."""
import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAdminUserManagement:
    def test_admin_can_list_users(self, admin_client, buyer, seller_user):
        resp = admin_client.get(reverse('admin-user-list'))
        assert resp.status_code == 200
        emails = [u['email'] for u in resp.data['results']]
        assert 'buyer@test.com' in emails

    def test_buyer_cannot_access_admin_users(self, buyer_client):
        resp = buyer_client.get(reverse('admin-user-list'))
        assert resp.status_code == 403

    def test_seller_cannot_access_admin_users(self, seller_client):
        resp = seller_client.get(reverse('admin-user-list'))
        assert resp.status_code == 403

    def test_admin_can_suspend_buyer(self, admin_client, buyer):
        url = reverse('admin-suspend-user', kwargs={'pk': buyer.id})
        resp = admin_client.post(url)
        assert resp.status_code == 200
        buyer.refresh_from_db()
        assert buyer.is_active is False

    def test_admin_cannot_suspend_admin(self, admin_client, admin_user):
        url = reverse('admin-suspend-user', kwargs={'pk': admin_user.id})
        resp = admin_client.post(url)
        assert resp.status_code == 403

    def test_admin_can_activate_suspended_user(self, admin_client, buyer):
        buyer.is_active = False
        buyer.save()
        url = reverse('admin-activate-user', kwargs={'pk': buyer.id})
        resp = admin_client.post(url)
        assert resp.status_code == 200
        buyer.refresh_from_db()
        assert buyer.is_active is True

    def test_suspend_nonexistent_user_returns_404(self, admin_client):
        import uuid
        url = reverse('admin-suspend-user', kwargs={'pk': uuid.uuid4()})
        resp = admin_client.post(url)
        assert resp.status_code == 404

    def test_admin_stats_endpoint(self, admin_client, buyer, product):
        resp = admin_client.get(reverse('admin-stats'))
        assert resp.status_code == 200
        data = resp.data['data']
        assert 'users' in data
        assert 'products' in data
        assert 'orders' in data
        assert data['users']['total'] >= 1
        assert data['products']['total'] >= 1

    def test_admin_can_verify_seller(self, admin_client, seller_profile):
        seller_profile.verified = False
        seller_profile.save()
        url = reverse('admin-verify-seller', kwargs={'pk': seller_profile.id})
        resp = admin_client.post(url)
        assert resp.status_code == 200
        seller_profile.refresh_from_db()
        assert seller_profile.verified is True

    def test_unauthenticated_cannot_access_admin(self, api_client):
        resp = api_client.get(reverse('admin-user-list'))
        assert resp.status_code == 401
