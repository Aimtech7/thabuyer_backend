from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from datetime import date

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        # Point directly to the React frontend
        return f"{settings.FRONTEND_URL}/auth/verify-email?key={emailconfirmation.key}"

    def get_common_context(self):
        """Standard branding context for all emails."""
        return {
            'frontend_url': settings.FRONTEND_URL,
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
            context['password_reset_url'] = f"{settings.FRONTEND_URL}/auth/reset-password?key={context['key']}"

        if 'expiration_days' not in context:
            context['expiration_days'] = getattr(settings, 'ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS', 3)

        return super().render_mail(template_prefix, email, context, headers)

    def send_mail(self, template_prefix, email, context):
        """
        Detect password reset and verification emails to send via Celery.
        """
        if template_prefix == 'account/email/password_reset_key':
            from .tasks import send_password_reset_email_task
            user = context.get('user')
            if user:
                # Prepare context for Celery (ensure render_mail was called first or manually add vars)
                # render_mail is called inside send_mail by super().send_mail, 
                # but we want to intercept BEFORE it sends synchronously.
                
                # Re-run normalization logic if needed or just use what's in context
                # Actually, allauth calls render_mail BEFORE send_mail? No, send_mail calls render_mail.
                
                # To be safe, let's ensure normalization happens
                if 'password_reset_url' not in context and 'key' in context:
                    context['password_reset_url'] = f"{settings.FRONTEND_URL}/auth/reset-password?key={context['key']}"
                if 'user_name' not in context and 'user' in context:
                    context['user_name'] = getattr(context['user'], 'name', '') or context['user'].email.split('@')[0]

                task_context = {
                    'password_reset_url': context.get('password_reset_url'),
                    'user_name': context.get('user_name'),
                    'expiration_days': context.get('expiration_days', 3),
                }
                send_password_reset_email_task.delay(user.id, task_context)
                return

        return super().send_mail(template_prefix, email, context)
