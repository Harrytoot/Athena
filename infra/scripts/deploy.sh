#!/bin/bash
set -e

echo "=== Athena Deploy ==="
echo "Date: $(date)"

# Load env
if [ -f .env.production ]; then
    export $(grep -v '^#' .env.production | xargs)
fi

# Pull latest
git pull origin master

# Build and start
docker compose -f docker-compose.prod.yml up -d --build

# Wait for healthy
echo "Waiting for services..."
sleep 10

# Health check
./infra/scripts/healthcheck.sh

echo "=== Deploy Complete ==="
