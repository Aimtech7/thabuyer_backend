# 📚 The Buyer: Backend Documentation & Software Requirements Specification (SRS)
**Version:** 1.0.0
**Architecture:** Django 5.x / Django REST Framework / PostgreSQL (Supabase) / ASGI WebSockets
**State:** Production-Ready

---

## 1. Executive Summary
"Tha Buyer" is a multi-vendor E-Commerce platform backend designed to facilitate seamless transactions between verified Sellers and Buyers. It utilizes a fully decoupled architecture, acting as a headless REST & Real-Time API to an independent frontend service (such as React/Next.js/React Native).

Key features include Role-Based Access Control (RBAC), multi-store product listings, real-time WebSocket notifications, Stripe payment integration, automated EasyPost shipping pipelines, custom coupon/promotion engines, and a native AI integration engine.

---

## 2. System Architecture
The application runs on a scalable asynchronous ASGI protocol (Daphne/Channels), allowing for simultaneous HTTP REST routing and persistent WebSocket connections.

### 2.1 Technology Stack
*   **Core Framework:** Django 5.x, Django REST Framework (DRF)
*   **Database:** PostgreSQL (Hosted on Supabase -> `eu-north-1`)
*   **Real-time Protocol:** Django Channels + Redis Pub/Sub
*   **Authentication:** JWT (SimpleJWT) + Social Sign-On (dj-rest-auth / django-allauth)
*   **Payments:** Stripe (via Webhooks and PaymentIntents)
*   **Fulfillment:** EasyPost API
*   **Task Queues:** Celery + Redis (Planned/Configured)

---

## 3. Functional Requirements (FR)

### Module 1: Identity & Authentication (`users` app)
*   **FR-1.01:** The system shall authenticate users using JWT access and refresh tokens.
*   **FR-1.02:** The system shall support Google OAuth sign-in and account merging without requiring manual password creation.
*   **FR-1.03:** The system strictly defines three user roles: `buyer`, `seller`, and `admin`. 
*   **FR-1.04:** The system shall persist structured User Addresses to automatically resolve EasyPost shipping coordinates.

### Module 2: Vendor Management (`sellers`, `products` app)
*   **FR-2.01:** Users possessing the `seller` role shall have access to create and manage products, inventories, and specific stores.
*   **FR-2.02:** Sellers can upload digital media (images/videos) associated with product SKUs.
*   **FR-2.03:** Buyers can query aggregated paginated listings from multiple sellers simultaneously via search mechanisms.

### Module 3: Checkout, Payments & Fulfillment (`cart`, `orders`, `pricing` apps)
*   **FR-3.01:** The system shall maintain stateful shopping carts natively in the database before checkout.
*   **FR-3.02:** Upon checkout, the system constructs a single *Stripe PaymentIntent*, dynamically applying relevant coupons and calculating sub-totals per vendor.
*   **FR-3.03:** The system securely listens to asynchronous `stripe_webhooks` to elevate an order's status from `pending` to `processing`.
*   **FR-3.04:** Sellers or Admins can trigger the `/fulfill/` endpoint to purchase tracking labels via EasyPost automatically.
*   **FR-3.05:** The system tracks historic price drops and changes for dynamic client alerts.

### Module 4: Promotions & Coupons (`promotions` app)
*   **FR-4.01:** Admins can generate sitewide coupons.
*   **FR-4.02:** Sellers can generate vendor-locked coupons that dynamically only apply to *their* products in a mixed-merchant checkout cart.
*   **FR-4.03:** Coupons support both `fixed` (flat fee subtraction) and `percentage` (ratio subtraction) algorithms.

### Module 5: Real-Time Mechanics (`notifications` app via WebSockets)
*   **FR-5.01:** The system maintains persistent `/ws/notifications/` channels using Redis.
*   **FR-5.02:** The system multiplexes websocket streams to send global broadcasts and targeted (user-specific) event payloads (e.g. "Your package shipped!").

---

## 4. Non-Functional Requirements (NFR)

*   **NFR-1 (Security):** All mutating API endpoints require `Bearer` token authorization. Password hashes use modern algorithms (`bcrypt`/`argon2`).
*   **NFR-2 (Performance):** Average API response times for standard read queries (listing products) must remain under `150ms`. Database limits concurrent blocking via Supabase IPv4 Transaction Pooler mapping.
*   **NFR-3 (Scalability):** The backend relies heavily on ASGI and externalized media configurations to be 100% stateless and horizontally scalable inside Docker containers.

---

## 5. Overview of Schema and Key Models

### `users.User`
*   Inherits from `AbstractBaseUser`. Uses `email` as the PK identifier.
*   Fields: `id` (UUID), `name`, `email`, `role`, `phone`, `verified`.

### `users.UserAddress`
*   Fields: `user` (FK), `street1`, `city`, `state`, `zip_code`, `is_default`.

### `orders.Order`
*   Fields: `buyer` (FK), `total_amount`, `status` (`pending`, `shipped`, `delivered`), `stripe_payment_id`.
*   *Shipping Fields:* `carrier`, `tracking_number`, `shipping_rate_id`.
*   *Discount Fields:* `coupon_applied` (FK -> `promotions.Coupon`), `discount_amount`.

### `promotions.Coupon`
*   Fields: `code`, `seller` (FK nullable), `discount_type` (`fixed`, `percentage`), `discount_value`, `active`, `expiration_date`.

---

## 6. Endpoints & Integrations Summary

**Important WebHooks:**
*   `POST /api/v1/orders/stripe/webhook/` -> Catches PaymentIntent successes. Requires Stripe-Signature header.

**Important OAuth Endpoints:**
*   `POST /api/auth/google/` -> Intercepts Google `access_token` and maps to Django `User`, returning internal JWTs.

**WebSockets Routing:**
*   `ws://{hostname}/ws/notifications/` -> Base ASGI mounting point.

---

## 7. Deployment Protocol

1.  **Environment Variables:** Ensure `.env` is securely provided.
    *   `DATABASE_URL` uses the **Supabase Transaction Pooler (Port 6543/5432)** for IPv4 network bridges.
    *   `STRIPE_SECRET_KEY` and `EASYPOST_API_KEY` must be populated.
    *   `REDIS_URL` must point to an active Redis instance (Upstash/Local) for WebSockets to process channels.
2.  **Server Wrapper:** Application *MUST* be run with an ASGI server (`daphne` or `uvicorn`) in production, *not* Gunicorn WSGI.
    *   Command: `daphne -b 0.0.0.0 -p 8000 core.asgi:application`
3.  **Migrations:** Execute `python manage.py migrate` upon fresh deployment environments to sync relations.
