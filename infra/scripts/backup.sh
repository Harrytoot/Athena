#!/bin/bash
set -e

echo "=== Athena Backup ==="
echo "Date: $(date)"

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Load env
if [ -f .env.production ]; then
    export $(grep -v '^#' .env.production | xargs)
fi

# PostgreSQL backup
echo "Backing up PostgreSQL..."
docker exec athena-postgres-1 pg_dump -U "${POSTGRES_USER:-athena}" "${POSTGRES_DB:-athena}" > "$BACKUP_DIR/database.sql"

# MinIO backup (if mc client available)
echo "Backing up MinIO..."
if command -v mc &> /dev/null; then
    mc mirror athena/athena "$BACKUP_DIR/minio/"
fi

# Compress
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

# Cleanup old backups (>30 days)
find ./backups -name "*.tar.gz" -mtime +30 -delete

echo "=== Backup Complete: $BACKUP_DIR.tar.gz ==="
