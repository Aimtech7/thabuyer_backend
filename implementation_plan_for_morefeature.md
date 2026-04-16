# Backend Feature Expansion — All Features (Except Payments)

## Summary

Add 8 major feature areas to the existing Django backend (10 apps, 116 tests, 40+ endpoints). Each feature becomes a new Django app or extends existing apps.

## Proposed Changes

### Phase 1: New Django Apps (Core Features)

---

#### [NEW] `wishlists/` — Wishlist & Favorites
- `models.py`: Wishlist model (user → product, M2M with timestamps)
- `serializers.py`: Add/remove/list serializers
- `views.py`: Add to wishlist, remove, list all, check if wishlisted
- `urls.py`: 4 endpoints
- **Endpoints:**
  - `GET /api/v1/wishlists/` — List user's wishlist
  - `POST /api/v1/wishlists/add/` — Add product
  - `DELETE /api/v1/wishlists/remove/<product_id>/` — Remove product
  - `GET /api/v1/wishlists/check/<product_id>/` — Check if wishlisted

---

#### [NEW] `notifications/` — In-App & Email Notifications
- `models.py`: Notification model (user, type, title, message, read, created_at)
- `serializers.py`: NotificationSerializer
- `views.py`: List, mark read, mark all read, unread count
- `signals.py`: Auto-create notifications on order status change, new review, price drop
- `email.py`: Email sending utilities (order confirmation, shipping update, welcome)
- **Endpoints:**
  - `GET /api/v1/notifications/` — List user notifications
  - `POST /api/v1/notifications/<id>/read/` — Mark as read
  - `POST /api/v1/notifications/read-all/` — Mark all as read
  - `GET /api/v1/notifications/unread-count/` — Get unread count
  - `DELETE /api/v1/notifications/<id>/` — Delete notification

---

#### [NEW] `shipping/` — Shipping & Delivery Tracking
- `models.py`: ShippingAddress, ShipmentTracker, TrackingEvent models
- `serializers.py`: Address CRUD, tracking serializers
- `views.py`: Manage addresses, track shipments, update status (seller)
- **Endpoints:**
  - `GET/POST /api/v1/shipping/addresses/` — List/Create addresses
  - `PUT/DELETE /api/v1/shipping/addresses/<id>/` — Update/Delete address
  - `GET /api/v1/shipping/track/<order_id>/` — Track shipment
  - `POST /api/v1/shipping/update/<order_id>/` — Update tracking (seller)

---

#### [NEW] `coupons/` — Coupons & Promotions
- `models.py`: Coupon (code, type, value, min_order, max_uses, expiry, seller), FlashSale
- `serializers.py`: Coupon validation, FlashSale serializer
- `views.py`: Apply coupon, validate, seller CRUD, flash sales
- **Endpoints:**
  - `POST /api/v1/coupons/validate/` — Validate coupon code
  - `POST /api/v1/coupons/apply/` — Apply coupon to order
  - `GET/POST /api/v1/coupons/seller/` — Seller manage coupons
  - `GET /api/v1/coupons/active/` — List active public coupons
  - `GET /api/v1/coupons/flash-sales/` — List active flash sales

---

#### [NEW] `messaging/` — Buyer ↔ Seller Chat
- `models.py`: Conversation, Message models
- `serializers.py`: Conversation & message serializers
- `views.py`: REST endpoints for conversations and messages
- `consumers.py`: WebSocket consumer for real-time chat (Django Channels)
- `routing.py`: WebSocket URL routing
- **Endpoints (REST fallback):**
  - `GET /api/v1/messages/conversations/` — List conversations
  - `POST /api/v1/messages/conversations/` — Start conversation
  - `GET /api/v1/messages/conversations/<id>/` — Get messages
  - `POST /api/v1/messages/conversations/<id>/send/` — Send message
- **WebSocket:** `ws://.../ws/chat/<conversation_id>/`

---

#### [NEW] `analytics/` — Reports & Exports
- `models.py`: SalesReport (cached daily aggregates)
- `views.py`: Dashboard stats, sales reports, CSV/PDF exports
- `utils.py`: PDF invoice generator (ReportLab), CSV builder
- **Endpoints:**
  - `GET /api/v1/analytics/dashboard/` — Admin dashboard stats
  - `GET /api/v1/analytics/sales-report/` — Sales report with date range
  - `GET /api/v1/analytics/export/orders/` — CSV export of orders
  - `GET /api/v1/analytics/export/products/` — CSV export of products
  - `GET /api/v1/analytics/invoice/<order_id>/` — PDF invoice download

---

### Phase 2: Enhanced Security

#### [MODIFY] `users/` — 2FA, Social Auth, Password Reset
- Add TOTP 2FA model & views (django-otp)
- Add password reset with email token flow
- Add social auth endpoints (Google, GitHub via `dj-rest-auth` + `allauth`)
- **New Endpoints:**
  - `POST /api/v1/auth/password-reset/` — Request password reset
  - `POST /api/v1/auth/password-reset/confirm/` — Confirm reset with token
  - `POST /api/v1/auth/2fa/setup/` — Generate TOTP secret + QR
  - `POST /api/v1/auth/2fa/verify/` — Verify TOTP token
  - `POST /api/v1/auth/2fa/disable/` — Disable 2FA
  - `POST /api/v1/auth/social/google/` — Google OAuth
  - `POST /api/v1/auth/social/github/` — GitHub OAuth

---

### Phase 3: Performance & Infrastructure

#### [MODIFY] `core/settings.py` — Redis caching, Channels
- Add Django Channels for WebSocket support
- Add Redis cache backend configuration
- Add cache decorators on product list, categories, seller profiles

#### [MODIFY] `products/views.py` — Search & Caching
- Add `django.core.cache` caching on expensive queries
- Improve full-text search with PostgreSQL trigram similarity

---

### Phase 4: Multi-Currency

#### [NEW] `currencies/` — Multi-Currency Support
- `models.py`: Currency, ExchangeRate models
- `views.py`: List currencies, convert price
- `middleware.py`: Currency preference middleware
- **Endpoints:**
  - `GET /api/v1/currencies/` — List supported currencies
  - `GET /api/v1/currencies/convert/` — Convert price
  - `POST /api/v1/currencies/preference/` — Set user currency preference

---

## Dependencies to Add

```
django-channels[daphne]>=4.0
channels-redis>=4.0
django-otp>=1.2
qrcode>=7.4
reportlab>=4.0
django-allauth>=0.57
dj-rest-auth[with_social]>=5.0
```

## Verification Plan

### Automated Tests
- Add test files for each new app (target: 50+ new tests)
- Run full suite: `pytest tests/ -v`
- Run Django system check: `python manage.py check`

### Manual Verification
- Run server and test endpoints via Swagger docs
- Verify WebSocket chat with a test client
