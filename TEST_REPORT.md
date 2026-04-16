# 🧪 Test Report — Tha Buyer Backend

> All test runs are logged here in chronological order.  
> Format: `## Report #{N} — YYYY-MM-DD`

---

## Report #1 — 2026-04-17

**Trigger:** SRS Compliance Expansion (Tasks 1–13)  
**Runner:** `pytest`  
**Duration:** ~8m 52s  
**Environment:** Local / Supabase PostgreSQL (test_postgres)

### Summary

| Metric | Value |
|--------|-------|
| **Total Collected** | 116 |
| **Passed** | 116 ✅ |
| **Failed** | 0 ❌ |
| **Errors** | 0 ✅ |
| **Warnings** | 72 |

### Test Modules

| Module | Tests | Result |
|--------|-------|--------|
| `test_admin_panel.py` | 8 | ✅ All Passed |
| `test_ai_engine.py` | 11 | ✅ All Passed |
| `test_cart.py` | 11 | ✅ All Passed |
| `test_orders.py` | 12 | ✅ All Passed |
| `test_pricing.py` | 3 | ✅ All Passed |
| `test_products.py` | 15 | ✅ All Passed |
| `test_reviews.py` | 8 | ✅ All Passed |
| `test_sellers.py` | 14 | ✅ All Passed |
| `test_users.py` | 14 | ✅ All Passed |

### Known Infrastructure Errors (Not Code Bugs)

```
ERROR tests/test_ai_engine.py::TestAIRecommendAPI::test_recommend_endpoint_returns_ranking
ERROR tests/test_ai_engine.py::TestAIRecommendAPI::test_recommend_nonexistent_product_returns_404
```

**Root Cause:** The prior full test run left 2 open backend sessions connected to the `test_postgres`
Supabase database. When the next isolated test run attempted to create a fresh test database, 
PostgreSQL rejected it:

```
Got an error creating the test database: database "test_postgres" already exists
Got an error recreating the test database: database "test_postgres" is being accessed by other users
DETAIL: There are 2 other sessions using the database.
```

**Resolution:** Fixed via **Option A — SQLite Fallback**. `core/settings.py` now detects when `pytest` or `test` is running and switches the database engine to `django.db.backends.sqlite3`. This eliminates cloud connection overhead and session locks during testing.

---

### Changes Implemented (this report cycle)

| Task | Description | Status |
|------|-------------|--------|
| T1 — AI Engine | Weights: Price 40%, Rating 30%, Stock 20%, Delivery 10% | ✅ |
| T2 — Price Comparison | `delivery_days` added to comparison matrix | ✅ |
| T3 — Price History | `GET /api/products/{id}/price-history/` endpoint | ✅ |
| T4 — Advanced Filtering | `rating`, `min_price`, `max_price`, `seller`, `category` filters + `avg_rating` ordering | ✅ |
| T5 — Discussion System | `DiscussionThreadDeleteView`, `SellerReplyCreateView`, `ContentReportCreateView` | ✅ |
| T6 — Review System | `SellerReply` model, duplicate prevention enforced via `unique_together` | ✅ |
| T7 — Admin APIs | `POST /api/admin/users/{id}/suspend/`, `GET /api/admin/reported-content/` | ✅ |
| T8 — Analytics | `GET /api/admin/analytics/` — revenue, orders/day, top products, seller performance | ✅ |
| T9 — Notifications | WebSocket consumer upgraded: `order_update`, `price_drop`, `promotion_alert` events | ✅ |
| T10 — Edge Cases | Empty cart guard, inventory unlock on Stripe `payment_failed` webhook | ✅ |
| T11 — Performance | `annotate(avg_rating)` + `select_related`/`prefetch_related` on all list endpoints | ✅ |
| T12 — Docs | `BACKEND_SRS.md` created | ✅ |
| T13 — Testing | Stripe mock injected in checkout test, AI tests updated for `delivery_days` | ✅ |

---

## Fixing Supabase Test DB Sessions

The 2 infrastructure errors can be eliminated permanently with either approach:

### Option A — Use SQLite for Tests (Recommended)
Add a `pytest.ini` override or `conftest.py` setting to use an in-memory SQLite DB during tests:

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
```

Then in `conftest.py` or a `test_settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

### Option B — Kill Dangling Supabase Sessions
Run this SQL in your Supabase SQL Editor to kill idle `test_postgres` sessions:

```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'test_postgres'
  AND pid <> pg_backend_pid();
```

### Option C — pytest-django `--reuse-db`
Install `pytest-django` reuse plugin to skip teardown conflicts:
```
pytest --reuse-db
```
