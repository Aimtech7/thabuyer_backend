import os
import sys
import django
import requests
from decimal import Decimal
from django.utils.text import slugify
from django.core.files.base import ContentFile

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from users.models import User
from sellers.models import SellerProfile
from products.models import Category, Product, ProductImage

def download_image_to_model(url, product, is_primary=True):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            file_name = f"{product.SKU}_{'primary' if is_primary else 'extra'}.jpg"
            img_record = ProductImage(
                product=product,
                alt_text=product.name,
                is_primary=is_primary
            )
            img_record.image.save(file_name, ContentFile(response.content), save=True)
            return True
    except Exception as e:
        print(f"   ! Error downloading image for {product.name}: {e}")
    return False

def run():
    print("--- STARTING PRODUCTION-GRADE DATA SEEDING ---")
    
    cat_images = {
        'Electronics': 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&q=80',
        'Clothing': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=800&q=80',
        'Foodstuff': 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=800&q=80',
        'Audio': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
        'Home & Garden': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80',
        'Beauty': 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=800&q=80',
    }
    
    print("Clearing old Products and Categories...")
    try:
        Product.objects.all().delete()
        Category.objects.all().delete()
    except Exception as e:
        print(f" ! Skipping deletion (tables might not exist): {e}")

    cat_map = {}
    for name, img_url in cat_images.items():
        cat, created = Category.objects.get_or_create(name=name, defaults={'slug': slugify(name)})
        cat_map[name] = cat
        if created:
            try:
                resp = requests.get(img_url, timeout=10)
                if resp.status_code == 200:
                    cat.image.save(f"cat_{slugify(name)}.jpg", ContentFile(resp.content), save=True)
                    print(f" -> Category image saved: {name}")
            except Exception as e:
                print(f" ! Error saving category image {name}: {e}")
    
    seller_emails = [
        'cherrylbahati@gmail.com', 
        'tech_store@thabuyer.com',
        'fashion_boutique@thabuyer.com',
        'grocery_market@thabuyer.com'
    ]
    
    sellers = []
    for email in seller_emails:
        user, created = User.objects.get_or_create(
            email=email, 
            defaults={'name': email.split('@')[0].replace('_', ' ').title()}
        )
        user.set_password('password123')
        user.role = 'seller'
        user.is_staff = False
        user.save()
        
        profile, p_created = SellerProfile.objects.get_or_create(
            user=user,
            defaults={
                'business_name': f"{user.name.split()[0]}'s Official Store",
                'commission_accepted': True,
                'verified': True,
                'rating_avg': 4.8
            }
        )
        sellers.append(user)
        print(f" -> Prepared Seller: {user.email}")

    # Production Products List
    production_products = [
        # Electronics
        {
            'name': 'MacBook Pro M3 Max', 
            'desc': 'Unleash extreme performance for pro workflows with the M3 Max chip.', 
            'cat': 'Electronics', 'price': 3199.00, 'sku': 'MAC-M3X-001',
            'img': 'https://images.unsplash.com/photo-1517336714467-d13a23232eb2?w=800&q=80'
        },
        {
            'name': 'Samsung Galaxy S24 Ultra', 
            'desc': 'Latest flagship smartphone with AI features and 200MP camera.', 
            'cat': 'Electronics', 'price': 1149.00, 'sku': 'SAM-S24U-001',
            'img': 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=800&q=80'
        },
        # Clothing
        {
            'name': 'Classic Denim Jacket', 
            'desc': 'Timeless denim jacket with a modern slim fit.', 
            'cat': 'Clothing', 'price': 85.00, 'sku': 'CLO-DEN-001',
            'img': 'https://images.unsplash.com/photo-1576905355162-7270bcdea8b0?w=800&q=80'
        },
        {
            'name': 'Organic Cotton T-Shirt', 
            'desc': 'Super soft t-shirt made from 100% certified organic cotton.', 
            'cat': 'Clothing', 'price': 25.00, 'sku': 'CLO-TEE-ORG',
            'img': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80'
        },
        # Foodstuff
        {
            'name': 'Premium Jasmine Rice (5kg)', 
            'desc': 'Fragrant and high-quality jasmine rice, perfect for all meals.', 
            'cat': 'Foodstuff', 'price': 12.50, 'sku': 'FOD-RIC-JAS',
            'img': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&q=80'
        },
        {
            'name': 'Extra Virgin Olive Oil', 
            'desc': 'Cold-pressed extra virgin olive oil from Mediterranean olives.', 
            'cat': 'Foodstuff', 'price': 18.00, 'sku': 'FOD-OIL-EVO',
            'img': 'https://images.unsplash.com/photo-1474979266404-7eaacabc88c5?w=800&q=80'
        },
        # Audio
        {
            'name': 'Sony WH-1000XM5', 
            'desc': 'Industry-leading noise cancelling headphones with exceptional sound.', 
            'cat': 'Audio', 'price': 348.00, 'sku': 'SNY-WH5-001',
            'img': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80'
        },
    ]

    print(f"\nCreating {len(production_products)} Products...")
    
    for i, p_data in enumerate(production_products):
        assigned_seller = sellers[i % len(sellers)]
        
        prod, created = Product.objects.get_or_create(
            SKU=p_data['sku'],
            defaults={
                'seller': assigned_seller,
                'category': cat_map[p_data['cat']],
                'name': p_data['name'],
                'description': p_data['desc'],
                'price': Decimal(str(p_data['price'])),
                'stock_qty': 50,
                'delivery_days': 2,
            }
        )
        
        print(f" -> Product: {prod.name} | Seller: {assigned_seller.email}")
        if created:
            download_image_to_model(p_data['img'], prod)

    print("\n--- SEEDING COMPLETE ---")

if __name__ == '__main__':
    run()
