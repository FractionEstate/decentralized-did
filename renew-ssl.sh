#!/bin/bash
# SSL Certificate Renewal Script for Biometric DID
# This script renews Let's Encrypt SSL certificates and reloads nginx

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PROJECT_DIR}/.env.production"
LOG_FILE="${PROJECT_DIR}/logs/ssl-renewal.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Load environment variables
load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        set -a
        source "$ENV_FILE"
        set +a
        log_info "Environment variables loaded from $ENV_FILE"
    else
        log_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
}

# Check if certificates need renewal (Let's Encrypt recommends renewal when < 30 days left)
check_cert_expiry() {
    local cert_file="${PROJECT_DIR}/nginx/ssl/fullchain.pem"
    local domain="$DOMAIN"

    if [[ ! -f "$cert_file" ]]; then
        log_info "SSL certificate not found. Running initial certificate generation..."
        return 0
    fi

    # Check certificate expiry date
    local expiry_date=$(openssl x509 -in "$cert_file" -noout -enddate 2>/dev/null | cut -d= -f2)
    local expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
    local current_epoch=$(date +%s)
    local days_left=$(( (expiry_epoch - current_epoch) / 86400 ))

    log_info "SSL certificate expires on: $expiry_date"
    log_info "Days remaining: $days_left"

    if [[ $days_left -lt 30 ]]; then
        log_info "Certificate expires in less than 30 days. Renewal needed."
        return 0
    else
        log_info "Certificate is still valid for $days_left days. No renewal needed."
        return 1
    fi
}

# Renew SSL certificates
renew_certificates() {
    log_info "Starting SSL certificate renewal process..."

    cd "$PROJECT_DIR"

    # Stop nginx to free port 80
    log_info "Stopping nginx to free port 80..."
    docker-compose --profile production stop nginx

    # Run certbot renewal
    log_info "Running certbot certificate renewal..."
    if docker-compose --profile production run --rm certbot renew; then
        log_success "SSL certificates renewed successfully."

        # Start nginx again
        log_info "Starting nginx..."
        docker-compose --profile production start nginx

        # Test nginx configuration
        sleep 5
        if curl -f -k https://$DOMAIN/health &>/dev/null; then
            log_success "Nginx restarted successfully. SSL renewal complete."
            return 0
        else
            log_error "Nginx failed to start properly after SSL renewal."
            return 1
        fi
    else
        log_error "SSL certificate renewal failed."

        # Start nginx again even if renewal failed
        log_info "Starting nginx (even though renewal failed)..."
        docker-compose --profile production start nginx

        return 1
    fi
}

# Setup cron job for automatic renewal
setup_cron() {
    local cron_job="0 12 * * * $PROJECT_DIR/renew-ssl.sh"
    local current_cron=$(crontab -l 2>/dev/null || true)

    if echo "$current_cron" | grep -q "$PROJECT_DIR/renew-ssl.sh"; then
        log_info "SSL renewal cron job already exists."
    else
        log_info "Setting up automatic SSL renewal cron job..."
        (echo "$current_cron"; echo "$cron_job") | crontab -
        log_success "SSL renewal cron job added (runs daily at 12:00)."
    fi
}

# Main renewal process
main() {
    log_info "=== SSL Certificate Renewal Started ==="

    load_env

    if [[ -z "$DOMAIN" ]]; then
        log_error "DOMAIN environment variable not set."
        exit 1
    fi

    if check_cert_expiry; then
        if renew_certificates; then
            log_success "SSL certificate renewal completed successfully."
        else
            log_error "SSL certificate renewal failed."
            exit 1
        fi
    else
        log_info "SSL certificates are still valid. No renewal needed."
    fi

    # Setup cron job for future renewals
    setup_cron

    log_info "=== SSL Certificate Renewal Finished ==="
}

# Run main function
main "$@"
