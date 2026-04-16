# ── Build Stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# ── Runtime Stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings

WORKDIR /app

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Create non-root user
RUN addgroup --system ecommerce && adduser --system --ingroup ecommerce ecommerce

# Copy source
COPY --chown=ecommerce:ecommerce . .

# Create directories for logs and media
RUN mkdir -p logs media staticfiles && chown -R ecommerce:ecommerce logs media staticfiles

USER ecommerce

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/products/')"

# Collect static files at build time
RUN python manage.py collectstatic --noinput --clear || true

CMD ["gunicorn", "core.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
