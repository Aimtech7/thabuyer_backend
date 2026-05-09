"""users/views.py"""
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
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

    @extend_schema(
        request=RegisterSerializer,
        responses={201: OpenApiResponse(description='User registered successfully')},
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

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
    callback_url = "http://localhost:3000/auth/google/callback" # Update for frontend URL
    client_class = OAuth2Client
