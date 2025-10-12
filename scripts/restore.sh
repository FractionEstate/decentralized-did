#!/bin/bash

# Restore Script for Biometric DID System
# Restores backups created by backup.sh

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/biometric-did}"

echo "==================================="
echo "Biometric DID Restore Script"
echo "==================================="
echo ""

# Check for backup name argument
if [ -z "$1" ]; then
    echo "Usage: $0 <backup-name>"
    echo ""
    echo "Available backups:"
    ls -1 "$BACKUP_DIR" | grep -o "biometric-did_[0-9_]*" | sort -u | sed 's/^/  - /'
    exit 1
fi

BACKUP_NAME="$1"

echo "Restoring from backup: $BACKUP_NAME"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Verify backup files exist
MISSING_FILES=()

[ -f "$BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz" ] || MISSING_FILES+=("logs")
[ -f "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" ] || MISSING_FILES+=("data")
[ -f "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" ] || MISSING_FILES+=("config")

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo "⚠️  Warning: Some backup files are missing:"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - ${file}"
    done
    echo ""
    read -p "Continue with partial restore? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Confirm restore
echo ""
echo "⚠️  WARNING: This will overwrite existing data!"
echo ""
read -p "Are you sure you want to restore from backup $BACKUP_NAME? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Stop services
echo ""
echo "🛑 Stopping services..."
docker compose down

# Restore configuration
if [ -f "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" ]; then
    echo ""
    echo "📝 Restoring configuration files..."
    tar xzf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz"
    echo "✅ Configuration restored"
fi

# Restore SSL certificates
if [ -f "$BACKUP_DIR/${BACKUP_NAME}_ssl.tar.gz" ]; then
    echo ""
    echo "🔐 Restoring SSL certificates..."
    tar xzf "$BACKUP_DIR/${BACKUP_NAME}_ssl.tar.gz"
    echo "✅ SSL certificates restored"
fi

# Restore logs
if [ -f "$BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz" ]; then
    echo ""
    echo "📄 Restoring logs..."

    # Remove existing logs volume
    docker volume rm biometric-did_logs 2>/dev/null || true

    # Create new volume and restore
    docker volume create biometric-did_logs
    docker run --rm \
        -v biometric-did_logs:/data \
        -v "$BACKUP_DIR":/backup \
        alpine tar xzf "/backup/${BACKUP_NAME}_logs.tar.gz" -C /data

    echo "✅ Logs restored"
fi

# Restore data
if [ -f "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" ]; then
    echo ""
    echo "💾 Restoring data..."

    # Remove existing data volume
    docker volume rm biometric-did_data 2>/dev/null || true

    # Create new volume and restore
    docker volume create biometric-did_data
    docker run --rm \
        -v biometric-did_data:/data \
        -v "$BACKUP_DIR":/backup \
        alpine tar xzf "/backup/${BACKUP_NAME}_data.tar.gz" -C /data

    echo "✅ Data restored"
fi

# Restart services
echo ""
echo "🚀 Restarting services..."
docker compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo ""
echo "🏥 Checking service health..."

if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API is healthy"
else
    echo "⚠️  Backend API health check failed"
fi

if curl -f -s http://localhost:3003 > /dev/null; then
    echo "✅ Demo Wallet is accessible"
else
    echo "⚠️  Demo Wallet health check failed"
fi

echo ""
echo "✅ Restore completed successfully!"
echo ""
echo "Service status:"
docker compose ps
echo ""
