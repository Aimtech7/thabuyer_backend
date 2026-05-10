from django.core.management.base import BaseCommand
from orders.models import Order
from orders.utils import generate_order_number

class Command(BaseCommand):
    help = 'Generate order numbers for existing orders that do not have one.'

    def handle(self, *args, **options):
        orders = Order.objects.filter(order_number='')
        count = orders.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No orders without order numbers found.'))
            return

        self.stdout.write(f'Found {count} orders without order numbers. Generating...')
        
        for order in orders:
            order.order_number = generate_order_number()
            order.save(update_fields=['order_number'])
            self.stdout.write(f'Generated {order.order_number} for Order {order.id}')
            
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} orders.'))
