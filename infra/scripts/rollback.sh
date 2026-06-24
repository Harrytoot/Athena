#!/bin/bash
set -e

echo "=== Athena Rollback ==="

if [ -z "$1" ]; then
    echo "Usage: ./rollback.sh <commit-hash>"
    exit 1
fi

TARGET=$1

echo "Rolling back to: $TARGET"
git checkout $TARGET

docker compose -f docker-compose.prod.yml up -d --build

echo "=== Rollback Complete ==="
