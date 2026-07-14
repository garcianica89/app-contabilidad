#!/bin/bash
# Deploy script for App Contabilidad
# Run this on the server where Docker is available

set -e

echo "=== Pulling latest code ==="
git pull origin main

echo "=== Building backend image ==="
docker compose build backend

echo "=== Stopping old container ==="
docker compose down backend 2>/dev/null || true

echo "=== Starting backend ==="
docker compose up -d backend

echo "=== Running pending migrations ==="
docker compose exec -T backend alembic upgrade head

echo "=== Done ==="
echo "Backend running at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
