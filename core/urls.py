"""core/urls.py"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django Admin
    path('django-admin/', admin.site.urls),

    # API Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1 Routes
    path('api/v1/', include('api.urls')),

    # Required by dj_rest_auth password reset — redirects to frontend
    path(
        'api/v1/auth/password/reset/confirm/<uidb64>/<token>/',
        RedirectView.as_view(url=settings.FRONTEND_URL + '/auth/reset-password?uid=%(uidb64)s&token=%(token)s'),
        name='password_reset_confirm',
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
