#!/bin/bash

echo "=== Athena Health Check ==="

# Backend
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend: healthy"
else
    echo "✗ Backend: FAILED"
    exit 1
fi

# Frontend
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Frontend: healthy"
else
    echo "✗ Frontend: FAILED"
    exit 1
fi

# PostgreSQL
if docker exec athena-postgres-1 pg_isready -U athena > /dev/null 2>&1; then
    echo "✓ PostgreSQL: healthy"
else
    echo "✗ PostgreSQL: FAILED"
    exit 1
fi

# Redis
if docker exec athena-redis-1 redis-cli ping | grep -q PONG; then
    echo "✓ Redis: healthy"
else
    echo "✗ Redis: FAILED"
    exit 1
fi

echo "=== All services healthy ==="
