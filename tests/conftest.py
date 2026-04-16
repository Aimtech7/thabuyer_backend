"""
tests/conftest.py — Shared pytest fixtures for the entire test suite.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ─── Client helpers ───────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


def _get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def _auth_client(user):
    client = APIClient()
    access, _ = _get_tokens_for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    return client


# ─── User fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def buyer(db):
    return User.objects.create_user(
        email='buyer@test.com',
        password='TestPass123!',
        name='Test Buyer',
        role='buyer',
        verified=True,
    )


@pytest.fixture
def seller_user(db):
    return User.objects.create_user(
        email='seller@test.com',
        password='TestPass123!',
        name='Test Seller',
        role='seller',
        verified=True,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email='admin@test.com',
        password='TestPass123!',
        name='Test Admin',
    )


@pytest.fixture
def buyer_client(buyer):
    return _auth_client(buyer)


@pytest.fixture
def seller_client(seller_user):
    return _auth_client(seller_user)


@pytest.fixture
def admin_client(admin_user):
    return _auth_client(admin_user)


# ─── Seller profile fixture ────────────────────────────────────────────────────

@pytest.fixture
def seller_profile(seller_user):
    from sellers.models import SellerProfile
    return SellerProfile.objects.create(
        user=seller_user,
        business_name='Test Store',
        verified=True,
        commission_rate=Decimal('5.00'),
    )


# ─── Product fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def category(db):
    from products.models import Category
    return Category.objects.create(name='Electronics', slug='electronics')


@pytest.fixture
def product(seller_user, seller_profile, category):
    from products.models import Product
    return Product.objects.create(
        seller=seller_user,
        category=category,
        name='Wireless Headphones',
        description='Premium noise cancelling headphones.',
        price=Decimal('199.99'),
        stock_qty=50,
        SKU='WH-001',
        is_active=True,
    )


@pytest.fixture
def product_out_of_stock(seller_user, seller_profile, category):
    from products.models import Product
    return Product.objects.create(
        seller=seller_user,
        category=category,
        name='Wireless Headphones',
        description='Out of stock version.',
        price=Decimal('149.99'),
        stock_qty=0,
        SKU='WH-002',
        is_active=True,
    )


# ─── Cart fixture ──────────────────────────────────────────────────────────────

@pytest.fixture
def buyer_cart(buyer):
    from cart.models import Cart
    cart, _ = Cart.objects.get_or_create(buyer=buyer)
    return cart


@pytest.fixture
def cart_with_item(buyer_cart, product):
    from cart.models import CartItem
    CartItem.objects.create(
        cart=buyer_cart,
        product=product,
        quantity=2,
        price_at_add=product.price,
    )
    return buyer_cart


# ─── Order fixture ─────────────────────────────────────────────────────────────

@pytest.fixture
def completed_order(buyer, product):
    from orders.models import Order, OrderItem
    order = Order.objects.create(
        buyer=buyer,
        total_amount=Decimal('399.98'),
        status='delivered',
        shipping_address='123 Test Street',
        payment_ref='PAY-TEST-001',
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        unit_price=product.price,
        subtotal=Decimal('399.98'),
    )
    return order
