"""core/celery.py — Celery application configuration."""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

app = Celery('ecommerce')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# ─── Periodic Tasks ───────────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Check price alerts every 30 minutes
    'check-price-alerts': {
        'task': 'pricing.tasks.check_price_alerts',
        'schedule': crontab(minute='*/30'),
    },
    # Generate daily platform report at midnight
    'daily-platform-report': {
        'task': 'admin_panel.tasks.generate_daily_report',
        'schedule': crontab(hour=0, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
