from django.conf import settings

def frontend_url(request):
    """Injects FRONTEND_URL from settings into template context."""
    return {
        'FRONTEND_URL': getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    }
