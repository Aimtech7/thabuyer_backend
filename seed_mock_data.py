import os
import sys
import django
import requests
from decimal import Decimal
from django.utils.text import slugify
from django.core.files.base import ContentFile

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from sellers.models import SellerProfile
from products.models import Category, Product, ProductImage

def download_image_to_model(url, product, is_primary=True):
    """Helper to download an image from a URL and save it to the ProductImage model."""
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
    print("--- STARTING IMPROVED STORE SEEDING ---")
    
    # 1. Define Categories with images
    cat_images = {
        'Electronics': 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=300&q=80',
        'Audio': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&q=80',
        'Fashion': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=300&q=80',
        'Home & Garden': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=300&q=80',
        'Beauty': 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=300&q=80',
        'Sports': 'https://images.unsplash.com/photo-1461896836934-bd45ba5b17c3?w=300&q=80',
        'Toys & Games': 'https://images.unsplash.com/photo-1558060370-d644479cb6f7?w=300&q=80',
        'Watches': 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=300&q=80'
    }
    
    print("Clearing old Products and Categories...")
    Product.objects.all().delete()
    Category.objects.all().delete()

    cat_map = {}
    for name, img_url in cat_images.items():
        cat = Category.objects.create(name=name, slug=slugify(name))
        cat_map[name] = cat
        # Download category image
        try:
            resp = requests.get(img_url, timeout=10)
            if resp.status_code == 200:
                cat.image.save(f"cat_{slugify(name)}.jpg", ContentFile(resp.content), save=True)
                print(f" -> Category image saved: {name}")
        except Exception as e:
            print(f" ! Error saving category image {name}: {e}")
    
    # 2. Get or Create Sellers
    seller_emails = [
        'cherrylbahati@gmail.com', 
        'seller_tech@example.com',
        'fashion_hub@example.com',
        'home_essentials@example.com'
    ]
    
    sellers = []
    for email in seller_emails:
        user, created = User.objects.get_or_create(
            email=email, 
            defaults={'name': email.split('@')[0].replace('_', ' ').title()}
        )
        user.set_password('password123')
        user.role = 'seller' if email != 'cherrylbahati@gmail.com' else 'admin'
        user.is_staff = (user.role == 'admin')
        user.is_2fa_enabled = False
        user.save()
        
        profile, p_created = SellerProfile.objects.get_or_create(
            user=user,
            defaults={
                'business_name': f"{user.name}'s Official Store",
                'commission_accepted': True
            }
        )
        if not p_created:
            profile.commission_accepted = True
            profile.save()
            
        sellers.append(user)
        print(f" -> Prepared Seller: {user.email}")

    # 3. Define Diverse Products
    mock_products = [
        {
            'name': 'Samsung Galaxy S24 Ultra', 
            'desc': 'Latest flagship smartphone with AI features and 200MP camera.', 
            'cat': 'Electronics', 'price': 1149.00, 'sku': 'SAM-S24U-001',
            'img': 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&q=80&w=800'
        },
        {
            'name': 'Sony WH-1000XM5', 
            'desc': 'Industry-leading noise cancelling headphones with exceptional sound.', 
            'cat': 'Audio', 'price': 348.00, 'sku': 'SNY-WH5-001',
            'img': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&q=80&w=800'
        },
        {
            'name': 'Leather Designer Handbag', 
            'desc': 'Premium Italian leather handbag for modern elegance.', 
            'cat': 'Fashion', 'price': 450.00, 'sku': 'FSH-HB-001',
            'img': 'https://images.unsplash.com/photo-1584917033904-491178331a1b?auto=format&fit=crop&q=80&w=800'
        },
        {
            'name': 'Mechanical Gaming Keyboard', 
            'desc': 'RGB backlit mechanical keyboard with blue switches.', 
            'cat': 'Electronics', 'price': 89.99, 'sku': 'TEC-KB-RGB',
            'img': 'https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&q=80&w=800'
        },
        {
            'name': 'Ergonomic Office Chair', 
            'desc': 'Premium mesh chair with lumbar support for long working hours.', 
            'cat': 'Home & Garden', 'price': 299.00, 'sku': 'HOM-CH-ERG',
            'img': 'https://images.unsplash.com/photo-1505797149-43b0069ec26b?auto=format&fit=crop&q=80&w=800'
        },
        {
            'name': 'Minimalist Smart Watch', 
            'desc': 'Track your health and stay connected with this sleek watch.', 
            'cat': 'Watches', 'price': 199.00, 'sku': 'WAT-SMRT-MIN',
            'img': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&q=80&w=800'
        },
        {
            'name': 'Nike Air Zoom Pegasus', 
            'desc': 'Iconic running shoes for performance and comfort.', 
            'cat': 'Sports', 'price': 130.00, 'sku': 'SPT-NKE-PG',
            'img': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&q=80&w=800'
        },
        {
            'name': 'Organic Skincare Set', 
            'desc': '4-piece set for a glowing, natural complexion.', 
            'cat': 'Beauty', 'price': 75.00, 'sku': 'BEA-SKN-ORG',
            'img': 'https://images.unsplash.com/photo-1556228578-0d85b1a4d571?auto=format&fit=crop&q=80&w=800'
        },
        {
            'name': 'Coffee Espresso Machine', 
            'desc': 'Professional-grade machine for your morning brew.', 
            'cat': 'Home & Garden', 'price': 599.00, 'sku': 'HOM-COF-ESP',
            'img': 'https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?auto=format&fit=crop&q=80&w=800'
        },
        {
            'name': 'Wireless Gaming Mouse', 
            'desc': 'High-precision sensor with zero-latency wireless tech.', 
            'cat': 'Electronics', 'price': 120.00, 'sku': 'TEC-MS-WIR',
            'img': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&q=80&w=800'
        }
    ]

    print(f"\nCreating {len(mock_products)} Products and distributing to {len(sellers)} Sellers...")
    
    for i, p_data in enumerate(mock_products):
        assigned_seller = sellers[i % len(sellers)]
        
        prod = Product.objects.create(
            seller=assigned_seller,
            category=cat_map[p_data['cat']],
            name=p_data['name'],
            description=p_data['desc'],
            price=Decimal(str(p_data['price'])),
            stock_qty=20,
            delivery_days=3,
            SKU=p_data['sku'],
            clicks_count=0,
            views_count=0
        )
        
        print(f" -> Product: {prod.name} | Seller: {assigned_seller.email}")
        download_image_to_model(p_data['img'], prod)

    print("\n--- SEEDING COMPLETE ---")

if __name__ == '__main__':
    run()
