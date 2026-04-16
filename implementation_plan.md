# Expansion Architecture & Implementation Plan

Our goal is to build out the remaining advanced functionality required for a modern e-commerce platform. Because the scope is extensive, this plan segments the work into distinct, manageable phases.

## User Review Required

> [!IMPORTANT]
> The features outlined below span payments, auth, and real-time infrastructure. Since implementing all phases simultaneously would be a massive structural change, **please review the phases below and confirm if you want me to execute Phase 1 (Payments & Coupons) first, or if you prefer to tackle a different phase.**

---

## Proposed Changes by Phase

### Phase 1: Payments & Coupons Engine 💳 🎟️
Before handling inventory mapping physically or user identity externally, getting Stripe integrated and allowing discounts is the logical next step for e-commerce.

#### `orders/`
- **[MODIFY]** `checkout/` endpoint: Right now, checkout creates an order and decrements stock. We will update it to generate a **Stripe PaymentIntent** or Checkout session and hold the order in a `payment_pending` state.
- **[NEW]** Stripe Webhook Endpoint: An endpoint to listen for `payment_intent.succeeded` from Stripe to transition the order to `paid` and finalize the transaction.

#### `promotions/` (New App)
- **[NEW]** Models: `Coupon` (code, discount_amount, discount_type(fixed/percent), active).
- **[NEW]** Integration with Checkout: Pass a `coupon_code` during checkout, validation logic to deduct the amount from the `Order.total_amount` before charging Stripe.

---

### Phase 2: Shipping & Fulfillment 📦
Once payments are captured, the platform needs dynamic shipping calculation.
- **[NEW]** Integration via Shippo or EasyPost.
- **[MODIFY]** `users/models.py` to add `Address` objects (instead of raw text).
- **[MODIFY]** Checkout flow to query shipping rates dynamically based on Buyer and Seller ZIP codes and package geometries.
- **[MODIFY]** Order models to track `.tracking_number` and `.carrier`.

---

### Phase 3: Third-Party Auth (OAuth) 🔐
Allow users to sign up using Google/OAuth.
- **[NEW]** Install `dj-rest-auth` & `django-allauth`.
- **[MODIFY]** `users/urls.py` and views to expose `/auth/google/` routes.
- **[MODIFY]** Map social accounts to the current unified `User` model, bypassing password requirements if signed in socially.

---

### Phase 4: WebSockets & Real-time Notifications 🔔
- **[MODIFY]** Upgrade to `channels` and `daphne` server. Configure `core/asgi.py`.
- **[NEW]** Consumers to push Real-Time pricing alerts to buyers (so they don't have to reload to see an alert triggered by celery).
- **[NEW]** Action-driven notifications (e.g., Seller marks item as "shipped" -> Buyer gets a WS event).

---

## Open Questions

> [!CAUTION]
> 1. **Payments**: Will we use Stripe as the primary payment gateway, or do you have another provider in mind?
> 2. **Coupons**: Should coupons be created centrally by an Admin, or should Sellers be able to issue coupons specifically for their own products?
> 3. **Execution**: **Shall I begin executing Phase 1 (Stripe Payments + Promotions Engine) immediately?** 

---

## Verification Plan

### Automated Tests
- We will add Mock objects to mock Stripe's API responses in Pytest to ensure checkout handles payment errors or successes correctly without hitting live endpoints.
- We will write test scenarios for valid, expired, and invalid coupon codes during the checkout process.

### Manual Verification
- We will run the Django server, add an item to the cart, invoke checkout with a test Coupon code, retrieve the `client_secret` from Stripe, and simulate a successful payment using the Stripe CLI to ensure the webhook marks the order as paid.
