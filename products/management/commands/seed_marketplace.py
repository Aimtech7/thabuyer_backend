import os
import random
import uuid
import requests
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.db import transaction

from users.models import User, UserAddress
from sellers.models import SellerProfile
from products.models import Category, Product, ProductImage, ProductView
from orders.models import Order, OrderItem
from reviews.models import Review
from wishlists.models import Wishlist, WishlistItem
from cart.models import Cart, CartItem
from pricing.models import PriceHistory

class Command(BaseCommand):
    help = 'Seeds the marketplace with realistic production-ready data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- STARTING REALISTIC MARKETPLACE SEEDING ---'))
        
        try:
            with transaction.atomic():
                self.seed_categories()
                self.seed_sellers()
                self.seed_buyers()
                self.seed_products()
                self.seed_activity()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Seeding failed: {e}'))
            raise e

        self.stdout.write(self.style.SUCCESS('--- SEEDING COMPLETE: MARKETPLACE IS LIVE ---'))

    def download_image(self, url, filename):
        """Helper to download image for FileField/ImageField."""
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return ContentFile(resp.content, name=filename)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ! Image download failed ({url}): {e}'))
        return None

    def seed_categories(self):
        self.stdout.write('Seeding Categories...')
        categories = [
            {'name': 'Electronics', 'img': 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800'},
            {'name': 'Fashion', 'img': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=800'},
            {'name': 'Foodstuff', 'img': 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=800'},
        ]
        for cat_data in categories:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'slug': slugify(cat_data['name'])}
            )
            if created or not cat.image:
                img = self.download_image(cat_data['img'], f'cat_{cat.slug}.jpg')
                if img:
                    cat.image.save(f'cat_{cat.slug}.jpg', img, save=True)
            self.stdout.write(f'  - {cat.name}')

    def seed_sellers(self):
        self.stdout.write('Seeding Sellers...')
        sellers_data = [
            {
                'email': 'techzone@thabuyer.com',
                'name': 'TechZone Solutions',
                'business': 'TechZone Official Store',
                'desc': 'Premium electronics, computing gear, and gaming accessories. Authorized distributor for top global brands.',
                'city': 'Lagos', 'state': 'Lagos', 'country': 'Nigeria',
                'logo': 'https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=200',
                'banner': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200'
            },
            {
                'email': 'vogue@thabuyer.com',
                'name': 'Sarah Williams',
                'business': 'Vogue Hub Fashion',
                'desc': 'Curated contemporary fashion for men and women. High-quality fabrics and trendy designs for the modern lifestyle.',
                'city': 'Nairobi', 'state': 'Nairobi', 'country': 'Kenya',
                'logo': 'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=200',
                'banner': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200'
            },
            {
                'email': 'freshmart@thabuyer.com',
                'name': 'FreshMart Groceries',
                'business': 'FreshMart Superstore',
                'desc': 'Your one-stop shop for fresh produce, imported grains, and household essentials. Quality guaranteed.',
                'city': 'Accra', 'state': 'Greater Accra', 'country': 'Ghana',
                'logo': 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=200',
                'banner': 'https://images.unsplash.com/photo-1534723452862-4c874018d66d?w=1200'
            }
        ]
        for s in sellers_data:
            user, created = User.objects.get_or_create(
                email=s['email'],
                defaults={'name': s['name'], 'role': 'seller', 'verified': True}
            )
            if created:
                user.set_password('sellerpass2025')
                user.save()
            
            profile, _ = SellerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'business_name': s['business'],
                    'business_description': s['desc'],
                    'city': s['city'],
                    'state': s['state'],
                    'country': s['country'],
                    'verified': True,
                    'commission_accepted': True,
                    'rating_avg': Decimal('4.8'),
                    'rating_count': 120
                }
            )
            if not profile.logo:
                img = self.download_image(s['logo'], f'logo_{user.id}.jpg')
                if img: profile.logo.save(f'logo_{user.id}.jpg', img, save=True)
            if not profile.banner:
                img = self.download_image(s['banner'], f'banner_{user.id}.jpg')
                if img: profile.banner.save(f'banner_{user.id}.jpg', img, save=True)
            self.stdout.write(f'  - {profile.business_name}')

    def seed_buyers(self):
        self.stdout.write('Seeding Buyers...')
        buyers_data = [
            {
                'email': 'john.doe@example.com', 'name': 'John Doe',
                'phone': '+2348012345678', 'city': 'Ikeja', 'state': 'Lagos',
                'address': '123 Funsho Williams Ave, Surulere',
                'avatar': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200'
            },
            {
                'email': 'jane.smith@example.com', 'name': 'Jane Smith',
                'phone': '+254712345678', 'city': 'Westlands', 'state': 'Nairobi',
                'address': 'Apt 4B, Sapphire Heights, Rhapta Road',
                'avatar': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200'
            },
            {
                'email': 'mike.jones@example.com', 'name': 'Mike Jones',
                'phone': '+233241234567', 'city': 'East Legon', 'state': 'Accra',
                'address': 'Plot 45, Boundary Road',
                'avatar': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200'
            }
        ]
        for b in buyers_data:
            user, created = User.objects.get_or_create(
                email=b['email'],
                defaults={'name': b['name'], 'role': 'buyer', 'phone': b['phone'], 'verified': True}
            )
            if created:
                user.set_password('buyerpass2025')
                user.save()
            
            if not user.avatar:
                img = self.download_image(b['avatar'], f'avatar_{user.id}.jpg')
                if img: user.avatar.save(f'avatar_{user.id}.jpg', img, save=True)
            
            UserAddress.objects.get_or_create(
                user=user,
                street1=b['address'],
                city=b['city'],
                state=b['state'],
                country='Nigeria' if '+234' in b['phone'] else 'Kenya' if '+254' in b['phone'] else 'Ghana',
                is_default=True
            )
            
            Wishlist.objects.get_or_create(buyer=user)
            Cart.objects.get_or_create(buyer=user)
            self.stdout.write(f'  - {user.name}')

    def seed_products(self):
        self.stdout.write('Seeding Products (with Jumia-quality descriptions)...')
        
        tech_seller = User.objects.get(email='techzone@thabuyer.com')
        vogue_seller = User.objects.get(email='vogue@thabuyer.com')
        fresh_seller = User.objects.get(email='freshmart@thabuyer.com')
        
        elec_cat = Category.objects.get(name='Electronics')
        fash_cat = Category.objects.get(name='Fashion')
        food_cat = Category.objects.get(name='Foodstuff')

        # Sample Products data
        products_data = [
            # Tech
            {
                'seller': tech_seller, 'cat': elec_cat, 'name': 'MacBook Pro 14" M3 Chip',
                'price': 1999.00, 'stock': 15, 'sku': 'APPLE-MBP14-M3',
                'desc': 'Experience the power of the M3 chip. Stunning Liquid Retina XDR display, pro ports, and incredible battery life. Perfect for developers and creators.',
                'imgs': ['https://images.unsplash.com/photo-1517336712461-4811428a2b8e?w=800', 'https://images.unsplash.com/photo-1611186871348-b1ec696e5237?w=800']
            },
            {
                'seller': tech_seller, 'cat': elec_cat, 'name': 'Sony PlayStation 5 Slim',
                'price': 499.99, 'stock': 25, 'sku': 'SONY-PS5-SLIM',
                'desc': 'The best way to play. Experience lightning-fast loading with an ultra-high-speed SSD, deeper immersion with support for haptic feedback, adaptive triggers, and 3D Audio.',
                'imgs': ['https://images.unsplash.com/photo-1606813907291-d86ebb9954ad?w=800']
            },
            {
                'seller': tech_seller, 'cat': elec_cat, 'name': 'Logitech MX Master 3S',
                'price': 99.00, 'stock': 50, 'sku': 'LOGI-MXM3S',
                'desc': 'Master your flow. Quiet clicks, MagSpeed scrolling, and an ergonomic design for all-day productivity.',
                'imgs': ['https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800']
            },
            # Fashion
            {
                'seller': vogue_seller, 'cat': fash_cat, 'name': 'Classic Leather Chelsea Boots',
                'price': 120.00, 'stock': 30, 'sku': 'VOGUE-CHELSEA-01',
                'desc': 'Timeless design meeting modern comfort. Genuine top-grain leather with a durable elastic side panel for easy wear.',
                'imgs': ['https://images.unsplash.com/photo-1638247025967-b4e38f787b76?w=800']
            },
            {
                'seller': vogue_seller, 'cat': fash_cat, 'name': 'Slim Fit Linen Shirt',
                'price': 45.00, 'stock': 60, 'sku': 'VOGUE-LINEN-WHT',
                'desc': 'Breathable, lightweight linen perfect for warm climates. Features a clean slim fit and classic button-down collar.',
                'imgs': ['https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800']
            },
            # Food
            {
                'seller': fresh_seller, 'cat': food_cat, 'name': 'Premium Basmati Rice 5kg',
                'price': 18.50, 'stock': 200, 'sku': 'FRESH-BASMATI-5K',
                'desc': 'Long-grain aromatic basmati rice. Aged for 2 years to ensure perfect fluffiness and distinct aroma in every meal.',
                'imgs': ['https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800']
            },
            {
                'seller': fresh_seller, 'cat': food_cat, 'name': 'Extra Virgin Olive Oil 1L',
                'price': 12.00, 'stock': 100, 'sku': 'FRESH-EVOO-1L',
                'desc': 'Cold-pressed extra virgin olive oil. Rich in antioxidants and perfect for salads or light cooking.',
                'imgs': ['https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=800']
            }
        ]
        
        # Multiply products to reach requested counts (15-30 per seller)
        # We will iterate and create variants
        for p in products_data:
            # Create the actual product
            product, created = Product.objects.get_or_create(
                SKU=p['sku'],
                defaults={
                    'seller': p['seller'],
                    'category': p['cat'],
                    'name': p['name'],
                    'description': p['desc'],
                    'price': Decimal(str(p['price'])),
                    'stock_qty': p['stock'],
                    'delivery_days': 3,
                    'is_active': True
                }
            )
            
            if created or product.images.count() == 0:
                for idx, img_url in enumerate(p['imgs']):
                    # Use picsum.photos as a more reliable fallback if unsplash fails
                    img_data = self.download_image(img_url, f'{product.SKU}_{idx}.jpg')
                    if not img_data:
                        img_data = self.download_image(f"https://picsum.photos/seed/{product.SKU}_{idx}/800/600", f'{product.SKU}_{idx}.jpg')
                    
                    if img_data:
                        ProductImage.objects.create(
                            product=product,
                            image=img_data,
                            is_primary=(idx == 0)
                        )
            
            # Seed PriceHistory (Current and one past price)
            PriceHistory.objects.get_or_create(
                product=product,
                price=product.price,
                recorded_at=timezone.now()
            )
            PriceHistory.objects.get_or_create(
                product=product,
                price=product.price * Decimal('1.1'),
                recorded_at=timezone.now() - timedelta(days=30)
            )

            # Create variants to reach 15-30 products per seller
            for v in range(1, 10):
                variant_sku = f"{p['sku']}-V{v}"
                v_product, v_created = Product.objects.get_or_create(
                    SKU=variant_sku,
                    defaults={
                        'seller': p['seller'],
                        'category': p['cat'],
                        'name': f"{p['name']} (Edition {v})",
                        'description': f"Variant {v} of the popular {p['name']}. {p['desc']}",
                        'price': product.price * Decimal(str(1 + (v * 0.05))),
                        'stock_qty': random.randint(5, 100),
                        'delivery_days': random.randint(2, 5),
                        'is_active': True
                    }
                )
                if v_created:
                    # Link same images for speed
                    for orig_img in product.images.all():
                        ProductImage.objects.create(product=v_product, image=orig_img.image, is_primary=orig_img.is_primary)
                    PriceHistory.objects.create(product=v_product, price=v_product.price)

            self.stdout.write(f'  - Product & Variants: {product.name}')

    def seed_activity(self):
        self.stdout.write('Simulating Market Activity (Orders, Reviews, Wishlists)...')
        buyers = User.objects.filter(role='buyer')
        products = Product.objects.all()
        
        for buyer in buyers:
            # 1. Add some to wishlist
            wishlist = buyer.wishlist
            wish_items = random.sample(list(products), 3)
            for p in wish_items:
                WishlistItem.objects.get_or_create(wishlist=wishlist, product=p)
            
            # 2. Record some views
            view_items = random.sample(list(products), 5)
            for p in view_items:
                ProductView.objects.create(user=buyer, product=p)

            # 3. Create 3-5 orders
            for i in range(random.randint(3, 5)):
                order_products = random.sample(list(products), random.randint(1, 3))
                total = sum(p.price for p in order_products)
                
                order = Order.objects.create(
                    buyer=buyer,
                    total_amount=total,
                    status=random.choice(['delivered', 'shipped', 'delivered', 'processing']), # Bias towards delivered
                    shipping_address=buyer.addresses.first().street1 if buyer.addresses.exists() else "Default Address",
                    payment_ref=f'ref_{uuid.uuid4().hex[:10]}'
                )
                
                # Backdate orders
                order.created_at = timezone.now() - timedelta(days=random.randint(1, 60))
                order.save()

                for p in order_products:
                    OrderItem.objects.create(
                        order=order,
                        product=p,
                        quantity=1,
                        unit_price=p.price,
                        subtotal=p.price
                    )
                    
                    # Add a review for delivered orders
                    if order.status == 'delivered':
                        Review.objects.get_or_create(
                            product=p,
                            buyer=buyer,
                            defaults={
                                'stars': random.randint(4, 5),
                                'comment': random.choice([
                                    "Amazing product, super fast delivery!",
                                    "Exactly what I was looking for. Quality is top notch.",
                                    "Great value for money. Highly recommended.",
                                    "TechZone never disappoints. Best service ever.",
                                    "Very fresh and well packaged. Will buy again."
                                ])
                            }
                        )
        self.stdout.write(self.style.SUCCESS('  - Activity simulated successfully'))
