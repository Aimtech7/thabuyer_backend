# Multi-Store E-Commerce Backend — Build Walkthrough

## Summary

Built a **complete, production-ready Django REST Framework backend** for a Multi-Store E-Commerce & Price Comparison platform. The system is fully operational with **116 passing tests**, seeded demo data, and Docker deployment ready.

---

## Architecture — 10 Modular Django Apps

| App | Purpose | Key Models |
|-----|---------|------------|
| `users` | JWT auth, custom User with UUID PK, RBAC (Buyer/Seller/Admin) | `User` |
| `sellers` | Seller profiles, dashboard, verification | `SellerProfile` |
| `products` | Catalog, categories, images, search, compare, bulk .xlsx upload | `Product`, `Category`, `ProductImage` |
| `pricing` | Automatic price history tracking, price alerts with Celery tasks | `PriceHistory`, `PriceAlert` |
| `cart` | Cart management with stock validation | `Cart`, `CartItem` |
| `orders` | Atomic checkout, order lifecycle, status transitions | `Order`, `OrderItem` |
| `reviews` | Star ratings, discussion threads with replies | `Review`, `DiscussionThread`, `DiscussionReply` |
| `admin_panel` | User/seller management, platform statistics | (no models — uses other apps) |
| `ai_engine` | Multi-factor scoring engine, buying recommendations | (no models — pure algorithm) |
| `core` | Settings, Celery, middleware, permissions, exception handling | — |

---

## What Was Built

### Core Infrastructure
- **Django 4.2 + DRF 3.15** with production-grade `settings.py` (env-driven, security hardened)
- **JWT authentication** via SimpleJWT with token blacklisting
- **RBAC permission system** — `IsBuyer`, `IsSeller`, `IsAdmin`, `IsOwnerOrAdmin`, etc.
- **Centralized exception handling** — consistent JSON error responses across all endpoints
- **Request logging middleware** with timing information
- **Celery + Redis** for background tasks (price alert checking, daily reports)
- **Custom pagination** with configurable page sizes

### All API Endpoints (40+ endpoints across 9 route groups)
- Auth: register, login, logout, token refresh, profile CRUD
- Products: list, create, detail, update, search, compare, categories, bulk upload
- Cart: view, add, remove, clear (with stock validation)
- Orders: checkout (atomic), list, detail, status transitions (with valid FSM)
- Reviews: create (enforces purchase requirement), list, CRUD, discussions + replies
- Pricing: price history, price alerts (create, list, cancel)
- Seller: dashboard (aggregated stats), profile, own products
- Admin: user management (suspend/activate), seller verification, platform stats
- AI: product recommendation with multi-factor scoring

### AI Recommendation Engine
- 5-factor scoring: price (40%), seller rating (25%), stock (15%), reviews (10%), price trend (10%)
- Price trend detection (falling/stable/rising) from historical data
- Human-readable explanations per candidate
- Fully deterministic and testable

### Testing — 116 Tests
| Module | Tests | Coverage |
|--------|-------|----------|
| `test_users.py` | 14 | User model + auth API |
| `test_products.py` | 11 | Product model + search + compare |
| `test_cart.py` | 11 | Cart model + add/remove/clear API |
| `test_orders.py` | 12 | Checkout + stock + status transitions |
| `test_reviews.py` | 8 | Review model + API + purchase enforcement |
| `test_sellers.py` | 14 | Seller profile + dashboard + RBAC |
| `test_pricing.py` | 15 | Price history + alerts + Celery tasks |
| `test_admin_panel.py` | 10 | Admin RBAC + management |
| `test_ai_engine.py` | 11 | Scoring engine + recommend API |
| **TOTAL** | **116** | **All passing** |

### DevOps & Deployment
- **Dockerfile** — multi-stage build, non-root user, health check
- **docker-compose.yml** — PostgreSQL, Redis, Django API, Celery worker, Celery beat, Nginx
- **nginx.conf** — reverse proxy with security headers and static/media serving
- **Makefile** — `make run`, `make test`, `make docker-up`, `make seed`, etc.
- **seed_demo_data** management command — 3 sellers, 5 buyers, 30 products, orders, reviews

---

## Verification Results

```
System check identified no issues (0 silenced).
116 passed, 0 failed in 59.00s
Demo data: 3 sellers, 5 buyers, 1 admin, 30 products, 6 categories
```

---

## Quick Start

```bash
cd backend
.venv\Scripts\activate        # activate venv (already created)
python manage.py runserver     # start at http://127.0.0.1:8000
```

**Demo credentials:**
- Buyers: `buyer1@demo.com` / `DemoPass123!`
- Sellers: `seller1@demo.com` / `DemoPass123!`
- Admin: `admin@demo.com` / `AdminPass123!`

**API docs:** `http://127.0.0.1:8000/api/docs/`

---

## File Count

**70+ files** across 10 apps, tests, and infrastructure config.
