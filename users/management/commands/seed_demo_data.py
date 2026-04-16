"""
Management command: seed_demo_data
Creates a complete set of demo data for development and testing.
"""
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from sellers.models import SellerProfile
from products.models import Product, Category
from pricing.models import PriceHistory, PriceAlert
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from reviews.models import Review, DiscussionThread, DiscussionReply

User = get_user_model()

CATEGORIES = [
    ('Electronics', 'electronics'),
    ('Clothing', 'clothing'),
    ('Books', 'books'),
    ('Home & Garden', 'home-garden'),
    ('Sports', 'sports'),
    ('Toys', 'toys'),
]

PRODUCTS = [
    # (name, description, price_range_min, price_range_max, category_slug, sku_prefix)
    ('Wireless Headphones Pro', 'Premium noise-cancelling wireless headphones with 40hr battery', 89.99, 249.99, 'electronics', 'WHP'),
    ('Wireless Headphones Lite', 'Affordable wireless headphones with solid sound quality', 29.99, 79.99, 'electronics', 'WHL'),
    ('Smartphone Case Ultra', 'Shock-resistant premium phone case with MagSafe compatibility', 14.99, 49.99, 'electronics', 'SCU'),
    ('USB-C Fast Charger', '65W GaN fast charger with 3 ports', 19.99, 59.99, 'electronics', 'UCF'),
    ('Cotton T-Shirt Classic', 'Premium 100% organic cotton unisex t-shirt', 12.99, 39.99, 'clothing', 'CTC'),
    ('Running Shoes Air', 'Lightweight running shoes with responsive cushioning', 49.99, 149.99, 'sports', 'RSA'),
    ('Python Programming Guide', 'Comprehensive guide to Python 3.12 for all levels', 19.99, 44.99, 'books', 'PPG'),
    ('Smart LED Bulb Pack', 'WiFi smart LED bulb 4-pack, RGB, voice controlled', 24.99, 69.99, 'home-garden', 'SLB'),
    ('Building Blocks Set', '500-piece creative building blocks set for ages 5+', 19.99, 59.99, 'toys', 'BBS'),
    ('Yoga Mat Premium', 'Non-slip eco-friendly yoga mat, 6mm thick', 24.99, 79.99, 'sports', 'YMP'),
]

REVIEW_COMMENTS = [
    'Excellent product! Highly recommend.',
    'Good quality for the price.',
    'Fast shipping, product as described.',
    'Decent product, could be better.',
    'Works perfectly, very happy with my purchase.',
    'Great value, would buy again.',
    'Solid build quality, no complaints.',
    'Better than expected!',
    'Just okay, nothing special.',
    'Love it! Best purchase this year.',
]


class Command(BaseCommand):
    help = 'Seed the database with demo data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Review.objects.all().delete()
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            CartItem.objects.all().delete()
            Cart.objects.all().delete()
            PriceAlert.objects.all().delete()
            PriceHistory.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            SellerProfile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write('Creating categories...')
        categories = {}
        for name, slug in CATEGORIES:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'slug': slug})
            categories[slug] = cat

        self.stdout.write('Creating sellers...')
        sellers = []
        for i in range(1, 4):
            user, created = User.objects.get_or_create(
                email=f'seller{i}@demo.com',
                defaults={
                    'name': f'Demo Seller {i}',
                    'role': 'seller',
                    'verified': True,
                },
            )
            if created:
                user.set_password('DemoPass123!')
                user.save()
            profile, _ = SellerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'business_name': f'Demo Store {i}',
                    'business_description': f'Premium products from Demo Store {i}',
                    'verified': True,
                    'commission_rate': Decimal('5.00'),
                    'rating_avg': Decimal(str(round(random.uniform(3.5, 5.0), 2))),
                    'rating_count': random.randint(10, 200),
                },
            )
            sellers.append(user)

        self.stdout.write('Creating buyers...')
        buyers = []
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                email=f'buyer{i}@demo.com',
                defaults={
                    'name': f'Demo Buyer {i}',
                    'role': 'buyer',
                    'verified': True,
                },
            )
            if created:
                user.set_password('DemoPass123!')
                user.save()
            buyers.append(user)

        self.stdout.write('Creating admin...')
        admin, created = User.objects.get_or_create(
            email='admin@demo.com',
            defaults={
                'name': 'Demo Admin',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'verified': True,
            },
        )
        if created:
            admin.set_password('AdminPass123!')
            admin.save()

        self.stdout.write('Creating products...')
        all_products = []
        sku_counter = 0
        for product_def in PRODUCTS:
            name, desc, price_min, price_max, cat_slug, sku_prefix = product_def
            for seller in sellers:
                sku_counter += 1
                price = Decimal(str(round(random.uniform(price_min, price_max), 2)))
                product, _ = Product.objects.get_or_create(
                    SKU=f'{sku_prefix}-{sku_counter:04d}',
                    defaults={
                        'seller': seller,
                        'category': categories[cat_slug],
                        'name': name,
                        'description': desc,
                        'price': price,
                        'stock_qty': random.randint(0, 200),
                        'is_active': True,
                    },
                )
                all_products.append(product)

        self.stdout.write('Creating orders & reviews...')
        for buyer in buyers:
            # Create 1-3 orders for each buyer
            for _ in range(random.randint(1, 3)):
                selected = random.sample(all_products, k=min(random.randint(1, 4), len(all_products)))
                total = Decimal('0.00')
                order = Order.objects.create(
                    buyer=buyer,
                    total_amount=Decimal('0.00'),
                    status=random.choice(['delivered', 'shipped', 'processing']),
                    shipping_address=f'{random.randint(1, 999)} Demo Street, City {random.randint(1, 50)}',
                    payment_ref=f'PAY-DEMO-{random.randint(10000, 99999)}',
                )
                for prod in selected:
                    qty = random.randint(1, 3)
                    subtotal = prod.price * qty
                    total += subtotal
                    OrderItem.objects.create(
                        order=order,
                        product=prod,
                        quantity=qty,
                        unit_price=prod.price,
                        subtotal=subtotal,
                    )
                order.total_amount = total
                order.save(update_fields=['total_amount'])

                # Leave a review on some of those products
                if order.status == 'delivered':
                    for prod in selected[:2]:
                        if not Review.objects.filter(product=prod, buyer=buyer).exists():
                            Review.objects.create(
                                product=prod,
                                buyer=buyer,
                                stars=random.randint(3, 5),
                                comment=random.choice(REVIEW_COMMENTS),
                            )

        self.stdout.write('Creating discussion threads...')
        for product in random.sample(all_products, k=min(5, len(all_products))):
            thread = DiscussionThread.objects.create(
                product=product,
                user=random.choice(buyers),
                title=f'Question about {product.name}',
                body=f'Does this product come with a warranty? Any tips for using {product.name}?',
            )
            DiscussionReply.objects.create(
                thread=thread,
                user=product.seller,
                body='Yes, it comes with a 1-year manufacturer warranty. Feel free to ask any other questions!',
            )

        self.stdout.write('Creating price alerts...')
        for buyer in buyers[:2]:
            for product in random.sample(all_products, k=min(3, len(all_products))):
                target = product.price * Decimal('0.80')
                PriceAlert.objects.get_or_create(
                    buyer=buyer,
                    product=product,
                    defaults={'target_price': target.quantize(Decimal('0.01'))},
                )

        self.stdout.write(self.style.SUCCESS(
            f'\n[OK] Demo data seeded successfully!\n'
            f'   Sellers: {len(sellers)} (seller1@demo.com ... seller3@demo.com / DemoPass123!)\n'
            f'   Buyers:  {len(buyers)} (buyer1@demo.com ... buyer5@demo.com / DemoPass123!)\n'
            f'   Admin:   admin@demo.com / AdminPass123!\n'
            f'   Products: {len(all_products)}\n'
            f'   Categories: {len(categories)}\n'
        ))
