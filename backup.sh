#!/bin/bash
# Backup Script for Biometric DID Production Deployment
# This script creates backups of application data, logs, and configurations

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PROJECT_DIR}/.env.production"
BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="biometric-did-backup-${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${RED}[ERROR]${NC} $1"
}

# Load environment variables
load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        set -a
        source "$ENV_FILE"
        set +a
        log_info "Environment variables loaded from $ENV_FILE"
    else
        log_warning "Environment file not found: $ENV_FILE (using defaults)"
    fi
}

# Create backup directory
create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    log_info "Backup directory: $BACKUP_DIR"
}

# Backup application data
backup_data() {
    log_info "Backing up application data..."

    mkdir -p "${BACKUP_PATH}/data"

    # Copy data directory if it exists
    if [[ -d "${PROJECT_DIR}/data" ]]; then
        cp -r "${PROJECT_DIR}/data" "${BACKUP_PATH}/"
        log_info "Application data backed up."
    else
        log_info "No application data directory found."
    fi
}

# Backup logs
backup_logs() {
    log_info "Backing up application logs..."

    mkdir -p "${BACKUP_PATH}/logs"

    # Copy logs directory if it exists
    if [[ -d "${PROJECT_DIR}/logs" ]]; then
        cp -r "${PROJECT_DIR}/logs" "${BACKUP_PATH}/"
        log_info "Application logs backed up."
    else
        log_info "No logs directory found."
    fi
}

# Backup configuration files
backup_config() {
    log_info "Backing up configuration files..."

    mkdir -p "${BACKUP_PATH}/config"

    # Backup environment files (but not secrets)
    cp "${PROJECT_DIR}/.env.example" "${BACKUP_PATH}/config/" 2>/dev/null || true
    cp "${PROJECT_DIR}/docker-compose.yml" "${BACKUP_PATH}/config/"
    cp "${PROJECT_DIR}/Dockerfile.backend" "${BACKUP_PATH}/config/"
    cp -r "${PROJECT_DIR}/nginx" "${BACKUP_PATH}/config/" 2>/dev/null || true

    # Create sanitized env file (remove secrets)
    if [[ -f "$ENV_FILE" ]]; then
        grep -v -E "(SECRET|PASSWORD|KEY)" "$ENV_FILE" > "${BACKUP_PATH}/config/env.sanitized"
        log_info "Configuration files backed up (secrets sanitized)."
    fi
}

# Backup SSL certificates
backup_ssl() {
    log_info "Backing up SSL certificates..."

    mkdir -p "${BACKUP_PATH}/ssl"

    # Copy SSL certificates if they exist
    if [[ -d "${PROJECT_DIR}/nginx/ssl" ]]; then
        cp -r "${PROJECT_DIR}/nginx/ssl" "${BACKUP_PATH}/"
        log_info "SSL certificates backed up."
    else
        log_info "No SSL certificates found."
    fi
}

# Create backup archive
create_archive() {
    log_info "Creating backup archive..."

    cd "$BACKUP_DIR"

    # Create compressed archive
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

    # Remove uncompressed backup
    rm -rf "$BACKUP_NAME"

    local archive_size=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    log_success "Backup archive created: ${BACKUP_NAME}.tar.gz (${archive_size})"
}

# Clean old backups
cleanup_old_backups() {
    local retention_days=${BACKUP_RETENTION_DAYS:-30}

    log_info "Cleaning up backups older than $retention_days days..."

    cd "$BACKUP_DIR"

    # Find and remove old backups
    local old_backups=$(find . -name "biometric-did-backup-*.tar.gz" -mtime +$retention_days)
    if [[ -n "$old_backups" ]]; then
        echo "$old_backups" | xargs rm -f
        local count=$(echo "$old_backups" | wc -l)
        log_info "Removed $count old backup(s)."
    else
        log_info "No old backups to clean up."
    fi
}

# Upload to S3 (optional)
upload_to_s3() {
    if [[ -n "${BACKUP_S3_BUCKET}" ]] && command -v aws &> /dev/null; then
        log_info "Uploading backup to S3..."

        if aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" "s3://${BACKUP_S3_BUCKET}/" --quiet; then
            log_success "Backup uploaded to S3 successfully."
        else
            log_error "Failed to upload backup to S3."
        fi
    fi
}

# Show backup information
show_backup_info() {
    log_success "Backup completed successfully!"
    echo
    log_info "Backup Details:"
    echo "  Location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    echo "  Timestamp: $TIMESTAMP"
    echo "  Size: $(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)"
    echo
    log_info "Contents:"
    tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | head -20
    if [[ $(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | wc -l) -gt 20 ]]; then
        echo "  ... (and $(($(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | wc -l) - 20)) more files)"
    fi
}

# Main backup process
main() {
    log_info "=== Biometric DID Backup Started ==="

    load_env
    create_backup_dir
    backup_data
    backup_logs
    backup_config
    backup_ssl
    create_archive
    cleanup_old_backups
    upload_to_s3
    show_backup_info

    log_info "=== Biometric DID Backup Finished ==="
}

# Run main function
main "$@"
