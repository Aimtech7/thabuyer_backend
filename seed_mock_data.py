import os
import sys
import django
from decimal import Decimal
from django.utils.text import slugify

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from sellers.models import SellerProfile
from products.models import Category, Product

def run():
    target_email = sys.argv[1] if len(sys.argv) > 1 else 'austinemakwaka254@gmail.com'
    print(f"Assigning mock data to user: {target_email}")
    
    # Get or create the user
    user, created = User.objects.get_or_create(email=target_email, defaults={'name': 'Mock Admin'})
    if created:
        user.set_password('password123')
        user.role = 'admin'
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print("Created new user.")
    
    # Ensure they have a SellerProfile so they can own products properly
    seller_profile, sp_created = SellerProfile.objects.get_or_create(
        user=user, 
        defaults={'business_name': 'Tha Buyer Official Store', 'business_description': 'The official store for mock products.'}
    )

    # Clear existing data just in case
    print("Clearing old mock data...")
    Product.objects.all().delete()
    Category.objects.all().delete()

    print("Creating Categories...")
    categories = ['Electronics', 'Audio', 'Fashion', 'Home & Garden', 'Beauty', 'Sports', 'Toys & Games', 'Watches', 'Books', 'Automotive', 'Pet Supplies']
    cat_map = {}
    for c in categories:
        cat_map[c] = Category.objects.create(name=c, slug=slugify(c))

    print("Creating Products...")
    mock_products = [
        {'name': 'Samsung Galaxy S24 Ultra', 'desc': 'Latest flagship smartphone with AI features', 'cat': 'Electronics', 'price': 1149.00, 'sku': 'SAM-S24U-001'},
        {'name': 'MacBook Pro 16" M3 Max', 'desc': 'Professional laptop with M3 Max chip', 'cat': 'Electronics', 'price': 3499.00, 'sku': 'APL-MBP16-001'},
        {'name': 'iPad Air M2', 'desc': 'Versatile tablet for work and play', 'cat': 'Electronics', 'price': 599.00, 'sku': 'APL-IPA-001'},
        {'name': 'Sony WH-1000XM5', 'desc': 'Premium noise-cancelling headphones', 'cat': 'Audio', 'price': 348.00, 'sku': 'SNY-WH5-001'},
        {'name': 'Nike Air Max 270', 'desc': 'Comfortable lifestyle sneakers', 'cat': 'Fashion', 'price': 150.00, 'sku': 'NKE-AM270-001'},
        {'name': 'Dyson V15 Detect', 'desc': 'Cordless vacuum with laser detection', 'cat': 'Home & Garden', 'price': 749.00, 'sku': 'DYS-V15-001'},
        {'name': 'La Mer Moisturizing Cream', 'desc': 'Luxury face moisturizer', 'cat': 'Beauty', 'price': 190.00, 'sku': 'LM-MC-001'},
        {'name': 'Garmin Forerunner 265', 'desc': 'Advanced GPS running smartwatch', 'cat': 'Sports', 'price': 399.00, 'sku': 'GAR-FR265-001'},
        {'name': 'Apple Watch Ultra 2', 'desc': 'Rugged titanium smartwatch with GPS', 'cat': 'Watches', 'price': 749.00, 'sku': 'APL-AWU2-001'},
    ]

    for p in mock_products:
        prod = Product.objects.create(
            seller=user,
            category=cat_map[p['cat']],
            name=p['name'],
            description=p['desc'],
            price=Decimal(str(p['price'])),
            stock_qty=25,
            delivery_days=3,
            SKU=p['sku']
        )
        print(f" -> Created {prod.name} (${prod.price})")

    print("\n✅ Successfully seeded mock data to your account!")
    print("Refresh your React frontend and they will magically appear.")

if __name__ == '__main__':
    run()
