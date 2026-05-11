#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Fix InconsistentMigrationHistory for django.contrib.sites/allauth
# This fakes the sites migration if it's already in the DB but not marked as migrated, 
# or if allauth was applied first.
python manage.py migrate sites --fake-initial || true

# Run standard migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input
