"""users/tasks.py — Celery tasks for user-related actions."""
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from core.email_service import render_email, send_email

User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60, # retry after 1 minute
)
def send_password_reset_email_task(self, user_id, context):
    """
    Asynchronously send a branded password reset email.
    """
    try:
        user = User.objects.get(id=user_id)
        subject = "Reset Your THA BUYER Password"
        to = [user.email]
        
        # Merge basic user info into context if not present
        if 'user_name' not in context:
            context['user_name'] = user.name or user.email.split('@')[0]
            
        success = send_email(
            subject=subject,
            to=to,
            template_name='password_reset.html',
            context=context
        )
        
        if not success:
            raise Exception("Email sending returned False")
            
        return f"Password reset email sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for password reset email.")
        return False
    except Exception as exc:
        logger.error(f"Error sending password reset email: {exc}")
        raise self.retry(exc=exc)
