#!/usr/bin/env bash
# ===========================================================================
# render-build.sh — THA BUYER Production Build Script
# Designed for a FRESH Supabase database.
# ===========================================================================
set -o errexit

echo "============================================================"
echo "  THA BUYER — Render Build Script"
echo "============================================================"

# ---------------------------------------------------------------------------
# STEP 1: Install dependencies
# ---------------------------------------------------------------------------
echo ""
echo "📦 [1/5] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
python -c "import django; print(f'✅ Django {django.__version__} | Python $(python --version 2>&1)')"

# ---------------------------------------------------------------------------
# STEP 2: Generate fresh migrations for all custom apps
# ---------------------------------------------------------------------------
echo ""
echo "🏗️  [2/5] Generating fresh migrations..."
python manage.py makemigrations --no-input
echo "✅ Migrations generated"

# ---------------------------------------------------------------------------
# STEP 3: Apply all migrations cleanly
# ---------------------------------------------------------------------------
echo ""
echo "🚀 [3/5] Applying migrations..."
python manage.py migrate --no-input
echo "✅ Migrations applied"

# ---------------------------------------------------------------------------
# STEP 4: Initialize Sites framework (required by allauth)
# ---------------------------------------------------------------------------
echo ""
echo "🌐 [4/5] Initializing Sites framework..."
python manage.py shell -c "
from django.contrib.sites.models import Site
s, created = Site.objects.get_or_create(
    id=1,
    defaults={'domain': 'thabuyer-backend-cj2s.onrender.com', 'name': 'THA BUYER'}
)
if not created:
    s.domain = 'thabuyer-backend-cj2s.onrender.com'
    s.name = 'THA BUYER'
    s.save()
print(f'✅ Site configured: {s.domain}')
"

# ---------------------------------------------------------------------------
# STEP 5: Collect static files
# ---------------------------------------------------------------------------
echo ""
echo "🎨 [5/5] Collecting static files..."
python manage.py collectstatic --no-input
echo "✅ Static files collected"

echo ""
echo "============================================================"
echo "  ✨ Build complete — THA BUYER is ready to serve"
echo "============================================================"
