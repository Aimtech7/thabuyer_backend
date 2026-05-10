# THA BUYER - Comprehensive System Report
**Date:** May 2026
**Architecture:** Django REST Framework (Backend) + React/Vite (Frontend) + Postgres/Redis + Docker

## 1. Executive Summary
THA BUYER is a production-ready, multi-store e-commerce and price comparison platform. The architecture is fully decoupled, featuring a high-performance React frontend and a robust Django backend. Recent scale-up efforts have integrated local Open Source Artificial Intelligence (Ollama) and real-world payment processing (Paystack), alongside full infrastructure Dockerization.

---

## 2. Backend Infrastructure (Django)

### Core Modules & Apps
- **`ai_engine`**: Features a custom `ollama_adapter.py` that interfaces with local Open Source LLMs (default `llama3`). It automatically generates rich product descriptions and acts as the foundation for the platform's intelligent "Best Value" analytics.
- **`payments`**: Replaces standard checkout flows with a direct **Paystack** integration. Initializes secure payment sessions and prepares for asynchronous payment verification via `PaystackWebhookView`.
- **`products`**: A deeply robust catalog system supporting `Category`, `Product`, and `StoreListing`. It supports complex `Q` object search queries and a robust Bulk Upload engine (`.xlsx` parser).
- **`users` & `sellers`**: Custom user models utilizing TOTP 2FA and JWT token rotation. 

### Security & Authentication
- **dj-rest-auth & simplejwt**: Handles authentication via HttpOnly cookies.
- **Cross-Origin Configuration**: Cookies are secured with `JWT_AUTH_SECURE = True` and `JWT_AUTH_SAMESITE = 'None'` to allow seamless authorization between cloud-hosted frontend platforms (e.g., Vercel) and backend servers (e.g., Render).

### Automated Testing
- Integrated `pytest` and `pytest-django`. The test suite strictly validates database constraints (e.g., unique category slugs) and endpoint response codes (e.g., `AIDescribeView`).

---

## 3. Frontend Architecture (React / Vite)

### Core User Interfaces
- **Seller Dashboard**: A centralized hub where vendors can bulk upload inventory, view financial metrics, and leverage the AI Engine to instantly write product descriptions.
- **Buyer Storefront (Search & Cart)**: Features a dynamic search interface heavily coupled with the backend's `ProductSearchView`. The `CartPage` acts as the final funnel, successfully bridging the user to the Paystack secure checkout environment.
- **Admin OS**: An expansive control panel managing user statuses, commission rates, and global platform health analytics.

### State & API Management
- **Hybrid API Layer (`services/api.ts`)**: Designed to seamlessly toggle between offline mock data and the live Django backend (`DJANGO_CONFIG.enabled`).
- **State**: Utilizes `zustand` for lightweight, instantaneous cart and theme management.

---

## 4. DevOps & CI/CD Pipeline

### Dockerization
- **Backend**: Containerized with Gunicorn/Uvicorn compatibility, running alongside PostgreSQL and Redis layers.
- **Frontend**: Utilizes a multi-stage `Dockerfile`. It builds the Vite project via Node and securely serves the static assets using an optimized Nginx alpine container.
- **Root Compose**: A unified `docker-compose.yml` allows developers to spin up the entire ecosystem (DB, Cache, Task Queue, Backend, Frontend) using a single `docker-compose up` command.

### Continuous Integration
- **GitHub Actions**: A unified `.github/workflows/ci.yml` pipeline triggers automatically on commits to `main` and `develop`. It provisions an Ubuntu runner, sets up Python/Node, installs dependencies, and runs the Pytest/Vitest suites to guarantee deployment integrity.

---

## 5. Next Steps / Future Roadmap
1. **Live Deployment**: Deploy the database to a managed service (AWS RDS / Supabase Postgres), the backend to Render, and the frontend to Vercel.
2. **Paystack Webhook Expansion**: Fulfill the webhook logic to actively mark pending orders as "Paid" in the database upon receiving the `charge.success` callback from Paystack.
3. **Advanced AI**: Fine-tune the Ollama models to understand specific vendor product niches better to produce higher-converting copy.
