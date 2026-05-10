"""users/urls.py"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, LogoutView, ProfileView, GoogleLogin, Toggle2FAView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('google/', GoogleLogin.as_view(), name='google-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('toggle-2fa/', Toggle2FAView.as_view(), name='toggle-2fa'),
    
    # Email Verification
    path('registration/verify-email/', getattr(__import__('dj_rest_auth.registration.views', fromlist=['VerifyEmailView']), 'VerifyEmailView').as_view(), name='rest_verify_email'),
    path('registration/resend-email/', getattr(__import__('dj_rest_auth.registration.views', fromlist=['ResendEmailVerificationView']), 'ResendEmailVerificationView').as_view(), name='rest_resend_email'),
    
    # Password Reset
    path('password/reset/', getattr(__import__('dj_rest_auth.views', fromlist=['PasswordResetView']), 'PasswordResetView').as_view(), name='rest_password_reset'),
    path('password/reset/confirm/', getattr(__import__('dj_rest_auth.views', fromlist=['PasswordResetConfirmView']), 'PasswordResetConfirmView').as_view(), name='rest_password_reset_confirm'),
]
