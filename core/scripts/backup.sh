#!/bin/bash

# Backup Script for Biometric DID System
# Creates compressed backups of volumes, configuration, and SSL certificates

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/biometric-did}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="biometric-did_${TIMESTAMP}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

echo "==================================="
echo "Biometric DID Backup Script"
echo "==================================="
echo ""
echo "Backup directory: $BACKUP_DIR"
echo "Timestamp: $TIMESTAMP"
echo "Retention: $RETENTION_DAYS days"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Cannot backup volumes."
    exit 1
fi

echo "📦 Backing up Docker volumes..."

# Backup logs volume
if docker volume ls | grep -q "biometric-did_logs"; then
    docker run --rm \
        -v biometric-did_logs:/data \
        -v "$BACKUP_DIR":/backup \
        alpine tar czf "/backup/${BACKUP_NAME}_logs.tar.gz" -C /data .
    echo "✅ Logs volume backed up"
else
    echo "⚠️  Logs volume not found, backing up local logs directory"
    if [ -d logs ]; then
        tar czf "$BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz" logs/
        echo "✅ Local logs backed up"
    fi
fi

# Backup data volume
if docker volume ls | grep -q "biometric-did_data"; then
    docker run --rm \
        -v biometric-did_data:/data \
        -v "$BACKUP_DIR":/backup \
        alpine tar czf "/backup/${BACKUP_NAME}_data.tar.gz" -C /data .
    echo "✅ Data volume backed up"
else
    echo "⚠️  Data volume not found, backing up local data directory"
    if [ -d data ]; then
        tar czf "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" data/
        echo "✅ Local data backed up"
    fi
fi

echo ""
echo "📝 Backing up configuration files..."

# Backup configuration files
tar czf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" \
    .env \
    docker-compose.yml \
    Dockerfile.backend \
    nginx/ \
    2>/dev/null || true

echo "✅ Configuration files backed up"

echo ""
echo "🔐 Backing up SSL certificates..."

# Backup SSL certificates
if [ -d nginx/ssl ] && [ "$(ls -A nginx/ssl)" ]; then
    tar czf "$BACKUP_DIR/${BACKUP_NAME}_ssl.tar.gz" nginx/ssl/
    echo "✅ SSL certificates backed up"
else
    echo "⚠️  SSL certificates not found"
fi

echo ""
echo "🧹 Cleaning up old backups (older than $RETENTION_DAYS days)..."

# Remove old backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
REMOVED=$(find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
echo "✅ Removed $REMOVED old backups"

echo ""
echo "📊 Backup summary:"
ls -lh "$BACKUP_DIR"/${BACKUP_NAME}_* 2>/dev/null || echo "No backup files found"

echo ""
echo "✅ Backup completed successfully!"
echo ""
echo "Backup files:"
echo "  - Logs:   $BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz"
echo "  - Data:   $BACKUP_DIR/${BACKUP_NAME}_data.tar.gz"
echo "  - Config: $BACKUP_DIR/${BACKUP_NAME}_config.tar.gz"
echo "  - SSL:    $BACKUP_DIR/${BACKUP_NAME}_ssl.tar.gz"
echo ""
echo "To restore from this backup, run:"
echo "  ./scripts/restore.sh ${BACKUP_NAME}"
echo ""
