#!/bin/sh
# Single-container start (Render & similar): migrate, seed, then serve API + bot webhook + web.
set -e

echo "==> Database migrations"
alembic upgrade head

echo "==> Reference data (categories, cities, plans, admin account)"
if [ "${SEED_DEMO:-false}" = "true" ]; then
  python -m scripts.seed --demo
else
  python -m scripts.seed
fi

echo "==> Starting the application on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="*"
