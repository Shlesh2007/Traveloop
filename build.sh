
#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations (This is where it usually crashes if psycopg2 is missing)
python manage.py migrate

python manage.py collectstatic --no-input
