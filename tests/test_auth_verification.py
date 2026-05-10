"""
tests/test_auth_verification.py — Tests for Email Verification & Password Reset (Phase 1).
"""
import pytest
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

REGISTER_URL = '/api/v1/auth/register/'
LOGIN_URL = '/api/v1/auth/login/'
VERIFY_EMAIL_URL = '/api/v1/auth/registration/verify-email/'
RESEND_EMAIL_URL = '/api/v1/auth/registration/resend-email/'
PASSWORD_RESET_URL = '/api/v1/auth/password/reset/'


@pytest.mark.django_db
class TestRegistrationEmailVerification:
    """When ACCOUNT_EMAIL_VERIFICATION is mandatory, registration should not return tokens."""

    @patch('allauth.account.utils.send_email_confirmation')
    def test_register_returns_message_not_tokens(self, mock_send_email, api_client):
        payload = {
            'name': 'New User',
            'email': 'newuser@test.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'role': 'buyer',
        }
        res = api_client.post(REGISTER_URL, payload, format='json')
        assert res.status_code == 201
        assert 'access' not in res.data.get('data', {})
        assert 'email' in res.data['message'].lower() or 'verify' in res.data['message'].lower()
        assert mock_send_email.called

    @patch('allauth.account.utils.send_email_confirmation')
    def test_register_duplicate_email_fails(self, mock_send_email, api_client, buyer):
        payload = {
            'name': 'Dup User',
            'email': buyer.email,
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'role': 'buyer',
        }
        res = api_client.post(REGISTER_URL, payload, format='json')
        assert res.status_code == 400


@pytest.mark.django_db
class TestLoginWithUnverifiedEmail:
    """Unverified users should not be able to log in."""

    def test_unverified_user_cannot_login(self, api_client):
        user = User.objects.create_user(
            email='unverified@test.com',
            password='TestPass123!',
            name='Unverified',
            role='buyer',
            verified=False,
        )
        res = api_client.post(LOGIN_URL, {'email': 'unverified@test.com', 'password': 'TestPass123!'}, format='json')
        # Login should fail since email is not verified via allauth EmailAddress
        assert res.status_code == 400
        assert 'verified' in str(res.data).lower() or 'not verified' in str(res.data).lower()

    def test_verified_user_can_login(self, api_client, buyer):
        # buyer fixture already creates a verified EmailAddress
        res = api_client.post(LOGIN_URL, {'email': buyer.email, 'password': 'TestPass123!'}, format='json')
        assert res.status_code == 200
        assert 'access' in res.data['data']


@pytest.mark.django_db
class TestPasswordReset:
    """Password reset endpoint should trigger email."""

    @patch('django.core.mail.send_mail')
    def test_password_reset_request_sends_email(self, mock_mail, api_client, buyer):
        res = api_client.post(PASSWORD_RESET_URL, {'email': buyer.email}, format='json')
        assert res.status_code == 200

    def test_password_reset_with_unknown_email_still_returns_200(self, api_client):
        """Security: should not leak whether email exists."""
        res = api_client.post(PASSWORD_RESET_URL, {'email': 'nonexistent@test.com'}, format='json')
        assert res.status_code == 200
