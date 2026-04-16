"""tests/test_users.py — User model & auth endpoint tests."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# ─── Model Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserModel:
    def test_create_buyer(self):
        user = User.objects.create_user(
            email='u@test.com', password='Pass123!', name='Alice', role='buyer'
        )
        assert user.email == 'u@test.com'
        assert user.role == 'buyer'
        assert user.is_buyer is True
        assert user.is_seller is False
        assert user.is_admin_user is False
        assert user.check_password('Pass123!')

    def test_create_seller(self):
        user = User.objects.create_user(
            email='s@test.com', password='Pass123!', name='Bob', role='seller'
        )
        assert user.is_seller is True

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@test.com', password='Admin123!'
        )
        assert admin.role == 'admin'
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_email_is_unique(self, buyer):
        with pytest.raises(Exception):
            User.objects.create_user(
                email='buyer@test.com', password='Pass123!', name='Dup'
            )

    def test_str_representation(self, buyer):
        assert 'buyer@test.com' in str(buyer)
        assert 'buyer' in str(buyer)

    def test_password_is_hashed(self, buyer):
        assert not buyer.password.startswith('TestPass')


# ─── API Tests ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuthEndpoints:
    def test_register_buyer(self, api_client):
        url = reverse('auth-register')
        data = {
            'name': 'New User',
            'email': 'new@test.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'role': 'buyer',
        }
        resp = api_client.post(url, data, format='json')
        assert resp.status_code == 201
        assert resp.data['status'] == 'success'
        assert 'access' in resp.data['data']
        assert User.objects.filter(email='new@test.com').exists()

    def test_register_fails_password_mismatch(self, api_client):
        url = reverse('auth-register')
        data = {
            'name': 'User',
            'email': 'x@test.com',
            'password': 'Pass123!',
            'password_confirm': 'Wrong123!',
            'role': 'buyer',
        }
        resp = api_client.post(url, data, format='json')
        assert resp.status_code == 400

    def test_register_cannot_self_assign_admin(self, api_client):
        url = reverse('auth-register')
        data = {
            'name': 'Hacker',
            'email': 'hack@test.com',
            'password': 'Pass123!',
            'password_confirm': 'Pass123!',
            'role': 'admin',
        }
        resp = api_client.post(url, data, format='json')
        assert resp.status_code == 400

    def test_login_success(self, api_client, buyer):
        url = reverse('auth-login')
        resp = api_client.post(url, {'email': 'buyer@test.com', 'password': 'TestPass123!'}, format='json')
        assert resp.status_code == 200
        assert 'access' in resp.data['data']
        assert resp.data['data']['user']['email'] == 'buyer@test.com'

    def test_login_wrong_password(self, api_client, buyer):
        url = reverse('auth-login')
        resp = api_client.post(url, {'email': 'buyer@test.com', 'password': 'wrong'}, format='json')
        assert resp.status_code == 400

    def test_login_suspended_user(self, api_client, buyer):
        buyer.is_active = False
        buyer.save()
        url = reverse('auth-login')
        resp = api_client.post(url, {'email': 'buyer@test.com', 'password': 'TestPass123!'}, format='json')
        assert resp.status_code == 400

    def test_profile_requires_auth(self, api_client):
        url = reverse('user-profile')
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_profile_returns_own_data(self, buyer_client, buyer):
        url = reverse('user-profile')
        resp = buyer_client.get(url)
        assert resp.status_code == 200
        assert resp.data['email'] == buyer.email
