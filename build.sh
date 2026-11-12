#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "=========================================================="
echo "==> Axoora Sovereign Fintech Backend - Render Build Phase"
echo "=========================================================="

# 1. Upgrade pip
echo "==> [1/6] Upgrading pip package manager..."
python -m pip install --upgrade pip

# 2. Install Python dependencies
echo "==> [2/6] Installing Python dependencies from requirements.txt..."
pip install --no-cache-dir -r requirements.txt

# 3. Collect static files for WhiteNoise
echo "==> [3/6] Collecting static files with WhiteNoise..."
python manage.py collectstatic --noinput --clear

# 4. Apply database migrations
echo "==> [4/6] Running database migrations..."
python manage.py migrate --noinput

# 5. Check or create default admin superuser
echo "==> [5/6] Verifying admin superuser account..."
python manage.py create_default_admin || echo "Admin creation skipped or already configured."

# 6. Auto-seed initial platform data if enabled
if [ "${AUTO_SEED_DATA:-true}" = "true" ]; then
    echo "==> [6/6] Seeding platform data & initial content..."
    python manage.py seed_axoora_data || echo "CMS data seeding completed or skipped."
    python manage.py seed_roles_and_team || echo "Role & team seeding completed or skipped."
    python manage.py sync_rag_knowledge || echo "RAG knowledge sync completed or skipped."
else
    echo "==> [6/6] AUTO_SEED_DATA is false. Skipping seed step."
fi

echo "=========================================================="
echo "==> Axoora Backend build finished successfully!"
echo "=========================================================="
