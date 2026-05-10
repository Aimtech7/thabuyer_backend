from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from datetime import date

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        # Point directly to the React frontend
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        return f"{frontend_url}/auth/verify-email?key={emailconfirmation.key}"

    def get_common_context(self):
        """Standard branding context for all emails."""
        return {
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'https://thabuyer.com'),
            'current_year': date.today().year,
        }

    def render_mail(self, template_prefix, email, context, headers=None):
        """Override to inject branding context and ensure consistent variables."""
        context.update(self.get_common_context())
        
        # Normalize variables for our branded templates
        if 'user' in context:
            context['user_name'] = getattr(context['user'], 'name', '') or context['user'].email.split('@')[0]
        
        # Verification URL normalization
        if 'activate_url' not in context and 'confirmation' in context:
            context['activate_url'] = self.get_email_confirmation_url(None, context['confirmation'])
            
        # Password Reset URL normalization
        if 'password_reset_url' not in context and 'key' in context:
            # Assuming standard password reset link structure on frontend
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://thabuyer.com')
            context['password_reset_url'] = f"{frontend_url}/auth/reset-password?key={context['key']}"

        if 'expiration_days' not in context:
            context['expiration_days'] = getattr(settings, 'ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS', 3)

        return super().render_mail(template_prefix, email, context, headers)
