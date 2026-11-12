#!/bin/sh
set -e

echo "==> Axoora Sovereign Fintech Backend Initializing..."

# 1. Ensure persistent data and media directories exist
mkdir -p /app/data
mkdir -p /app/media
mkdir -p /app/staticfiles

# 2. Run database migrations
echo "==> Running database migrations..."
python manage.py migrate --noinput

# 3. Create default admin superuser if not exists
echo "==> Checking default admin credentials..."
python manage.py create_default_admin || echo "Admin creation skipped or already exists."

# 4. Seed initial CMS platform data if needed
if [ "${AUTO_SEED_DATA:-true}" = "true" ]; then
    echo "==> Seeding initial platform data..."
    python manage.py seed_axoora_data || echo "Data seeding completed or skipped."
    python manage.py seed_roles_and_team || echo "Role & team seeding completed or skipped."
    python manage.py sync_rag_knowledge || echo "RAG knowledge sync completed or skipped."
fi

# 5. Collect static files for WhiteNoise
echo "==> Collecting static assets..."
python manage.py collectstatic --noinput --clear

echo "==> Backend ready. Starting application server..."
if [ $# -eq 0 ]; then
    PORT="${PORT:-8000}"
    echo "==> Starting Gunicorn on port $PORT..."
    exec gunicorn config.wsgi:application --bind "0.0.0.0:$PORT" --workers 3 --timeout 120
fi

exec "$@"
