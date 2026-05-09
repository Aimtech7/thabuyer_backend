import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order
orders = Order.objects.all()
print(f"Total Orders: {orders.count()}")
for o in orders:
    print(f"Order {o.id}: Status={o.status}, Amount={o.total_amount}")
