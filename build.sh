#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies and build Tailwind CSS
npm install
npm run build:css

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
