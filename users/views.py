"""users/views.py"""
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
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
        return Response(
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
        return Response(
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


class LogoutView(APIView):
    """Blacklist the refresh token on logout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'status': 'success', 'message': 'Logged out.'})
        except Exception:
            return Response(
                {'status': 'error', 'message': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update authenticated user's profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
