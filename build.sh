#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies and build Tailwind CSS
npm install
npm run build:css

# Collect static files
python manage.py collectstatic --no-input

# Run migrations automatically (Crucial for Free Tier)
python manage.py migrate
