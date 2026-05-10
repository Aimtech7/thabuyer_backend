"""users/views.py"""
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    """Register a new user (Buyer or Seller)."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_attempt'

    @extend_schema(
        request=RegisterSerializer,
        responses={201: OpenApiResponse(description='User registered successfully')},
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        from allauth.account.models import EmailAddress
        from allauth.account.utils import send_email_confirmation
        from django.conf import settings
        
        EmailAddress.objects.get_or_create(user=user, email=user.email, primary=True, verified=False)
        send_email_confirmation(request, user, signup=True)

        if getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'none') == 'mandatory':
            return Response(
                {
                    'status': 'success',
                    'message': 'Registration successful. Please check your email to verify your account.',
                    'data': {'user': UserSerializer(user).data},
                },
                status=status.HTTP_201_CREATED,
            )

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                'status': 'success',
                'message': 'Registration successful.',
                'data': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data,
                },
            },
            status=status.HTTP_201_CREATED,
        )
        from dj_rest_auth.jwt_auth import set_jwt_cookies
        set_jwt_cookies(response, refresh.access_token, refresh)
        return response


class LoginView(APIView):
    """Authenticate and receive JWT tokens."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_attempt'

    @extend_schema(
        request=LoginSerializer,
        responses={200: OpenApiResponse(description='Login successful')},
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                'status': 'success',
                'message': 'Login successful.',
                'data': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data,
                },
            },
            status=status.HTTP_200_OK,
        )
        from dj_rest_auth.jwt_auth import set_jwt_cookies
        set_jwt_cookies(response, refresh.access_token, refresh)
        return response


class LogoutView(APIView):
    """Blacklist the refresh token on logout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.conf import settings
        from dj_rest_auth.jwt_auth import unset_jwt_cookies
        try:
            refresh_cookie_name = settings.REST_AUTH.get('JWT_AUTH_REFRESH_COOKIE', 'my-refresh-token')
            refresh_token = request.data.get('refresh') or request.COOKIES.get(refresh_cookie_name)
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            response = Response({'status': 'success', 'message': 'Logged out.'})
            unset_jwt_cookies(response)
            return response
        except Exception:
            response = Response({'status': 'error', 'message': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
            unset_jwt_cookies(response)
            return response


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update authenticated user's profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class Toggle2FAView(APIView):
    """Toggle TOTP Two-Factor Authentication."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        enabled = request.data.get('enabled', False)
        user = request.user
        
        import pyotp
        if enabled and not user.otp_secret:
            user.otp_secret = pyotp.random_base32()
        
        user.is_2fa_enabled = enabled
        user.save()
        
        return Response({
            'status': 'success',
            'is_2fa_enabled': user.is_2fa_enabled,
            'otp_secret': user.otp_secret if enabled else None
        })


class GoogleLogin(SocialLoginView):
    """
    Callback/Endpoint for Google OAuth frontend exchange.
    Requires an access_token or code passed from the frontend.
    """
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

    @property
    def callback_url(self):
        from django.conf import settings
        return getattr(settings, 'FRONTEND_URL', 'http://localhost:5173') + '/auth/google/callback'



class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        from django.conf import settings
        refresh_cookie_name = settings.REST_AUTH.get('JWT_AUTH_REFRESH_COOKIE', 'my-refresh-token')
        refresh_token = request.data.get('refresh') or request.COOKIES.get(refresh_cookie_name)
        if refresh_token:
            request.data._mutable = True
            request.data['refresh'] = refresh_token
            request.data._mutable = False
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            from dj_rest_auth.jwt_auth import set_jwt_cookies
            from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
            access_token = response.data.get('access')
            new_refresh_token = response.data.get('refresh')
            if access_token and new_refresh_token:
                set_jwt_cookies(response, AccessToken(access_token), RefreshToken(new_refresh_token))
        return response


class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset view that ensures enumeration protection
    and returns a clean, branded response.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'password_reset'
    @extend_schema(tags=['Authentication'])
    def post(self, request, *args, **kwargs):
        # Default dj_rest_auth behavior is mostly fine, 
        # but we ensure success even if email doesn't exist (enumeration protection)
        super().post(request, *args, **kwargs)
        return Response(
            {"detail": "Password reset e-mail has been sent."},
            status=status.HTTP_200_OK
        )


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom password reset confirm view to handle the new password.
    """
    @extend_schema(tags=['Authentication'])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password has been reset with the new password."},
            status=status.HTTP_200_OK
        )
