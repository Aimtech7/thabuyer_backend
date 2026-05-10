from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings

class Command(BaseCommand):
    help = 'Syncs the default Site object domain and name with FRONTEND_URL'

    def handle(self, *args, **options):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
        # Strip protocol
        domain = frontend_url.replace('https://', '').replace('http://', '').split('/')[0]
        
        site, created = Site.objects.get_or_create(id=1)
        site.domain = domain
        site.name = 'Tha Buyer'
        site.save()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully synced Site ID 1 to domain: {domain}'))
