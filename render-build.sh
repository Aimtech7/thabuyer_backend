#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# --- MIGRATION RECOVERY SECTION ---
echo "🔍 Auditing migration state..."
python manage.py showmigrations sites
python manage.py showmigrations socialaccount

# Fix InconsistentMigrationHistory for django.contrib.sites/allauth
# We use --fake-initial to ensure the sites record is present if the table exists
echo "🛠️ Repairing migration dependencies (Safe Recovery)..."
python manage.py migrate sites --fake-initial || echo "⚠️ Sites migration repair skipped or failed"

# Run standard migrations
echo "🚀 Running full migration suite..."
python manage.py migrate

# --- VALIDATION SECTION ---
echo "✅ Validating Sites framework..."
python manage.py shell -c "from django.contrib.sites.models import Site; print(f'Default Site: {Site.objects.get_current()}')" || echo "⚠️ Sites validation failed"

# Collect static files
python manage.py collectstatic --no-input
