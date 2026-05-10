#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Node dependencies and build Tailwind CSS
# This is critical because your templates rely on tailwind.css
npm install
npm run build:css

# 3. Collect static files for WhiteNoise
python manage.py collectstatic --no-input

# 4. Run migrations (This creates the tables in your PostgreSQL database)
python manage.py migrate
