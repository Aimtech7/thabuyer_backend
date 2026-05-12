#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
echo "📦 Installing requirements..."
pip install -r requirements.txt

# --- CLEAN REBUILD SECTION ---
echo "🧹 Cleaning up old migrations..."
# This ensures we start with a clean slate as requested
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

echo "🏗️ Generating fresh migrations..."
python manage.py makemigrations --no-input

# --- MIGRATION SECTION ---
echo "🚀 Applying fresh migrations to the database..."
# On a fresh DB, this will create all tables from scratch
python manage.py migrate --no-input

# --- VALIDATION SECTION ---
echo "✅ Validating Sites framework..."
# Ensure the sites framework is correctly initialized for allauth
python manage.py shell -c "from django.contrib.sites.models import Site; s, _ = Site.objects.get_or_create(id=1, defaults={'domain': 'thabuyer.vercel.app', 'name': 'THA BUYER'}); print(f'Site configured: {s.domain}')"

# --- DATA SEEDING ---
echo "🌱 Seeding production-safe data..."
python seed_mock_data.py || echo "⚠️ Seeding failed (expected if data already exists)"

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --no-input

echo "✨ Deployment preparation complete!"
