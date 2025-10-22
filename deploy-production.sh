#!/bin/bash
# Biometric DID Production Deployment Script
# This script handles the complete production deployment process

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root (not recommended for production)
if [[ $EUID -eq 0 ]]; then
    log_error "This script should not be run as root for security reasons."
    log_info "Please run as a regular user with sudo privileges when needed."
    exit 1
fi

# Check if .env.production exists
if [[ ! -f "$ENV_FILE" ]]; then
    log_error "Production environment file not found: $ENV_FILE"
    log_info "Please copy .env.example to .env.production and configure your settings."
    exit 1
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Validate required environment variables
validate_env() {
    local required_vars=("API_SECRET_KEY" "JWT_SECRET_KEY" "DOMAIN" "SSL_EMAIL" "BLOCKFROST_API_KEY")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]] || [[ "${!var}" == CHANGE_ME* ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing or placeholder values for required environment variables:"
        printf '  - %s\n' "${missing_vars[@]}"
        log_info "Please update $ENV_FILE with proper values."
        exit 1
    fi
}

# Install Docker and Docker Compose if not present
install_docker() {
    if ! command -v docker &> /dev/null; then
        log_info "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        log_success "Docker installed. Please log out and back in for group changes to take effect."
    else
        log_info "Docker is already installed."
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_info "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        log_success "Docker Compose installed."
    else
        log_info "Docker Compose is already installed."
    fi
}

# Create required directories
create_directories() {
    log_info "Creating required directories..."
    sudo mkdir -p /etc/nginx/ssl
    sudo mkdir -p /var/log/nginx
    sudo mkdir -p /var/www/certbot

    # Set proper permissions
    sudo chown -R $USER:$USER "$PROJECT_DIR/logs" 2>/dev/null || true
    sudo chown -R $USER:$USER "$PROJECT_DIR/data" 2>/dev/null || true
    sudo chown -R $USER:$USER "$PROJECT_DIR/nginx/ssl" 2>/dev/null || true
    sudo chown -R $USER:$USER "$PROJECT_DIR/nginx/logs" 2>/dev/null || true

    log_success "Directories created and permissions set."
}

# Generate SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."

    # Stop nginx if running to free port 80
    cd "$PROJECT_DIR"
    docker-compose --profile production down nginx 2>/dev/null || true

    # Start certbot to get certificates
    log_info "Obtaining SSL certificates from Let's Encrypt..."
    docker-compose --profile production run --rm certbot

    if [[ $? -eq 0 ]]; then
        log_success "SSL certificates obtained successfully."
    else
        log_error "Failed to obtain SSL certificates."
        log_info "Please check your domain configuration and DNS settings."
        exit 1
    fi
}

# Deploy the application
deploy_app() {
    log_info "Deploying Biometric DID application..."

    cd "$PROJECT_DIR"

    # Pull latest images
    docker-compose --profile production pull

    # Build and start services
    docker-compose --profile production up -d --build

    # Wait for services to be healthy
    log_info "Waiting for services to start..."
    sleep 30

    # Check service health
    if docker-compose --profile production ps | grep -q "Up"; then
        log_success "Application deployed successfully!"
        log_info "Services running:"
        docker-compose --profile production ps
    else
        log_error "Some services failed to start."
        log_info "Check logs with: docker-compose --profile production logs"
        exit 1
    fi
}

# Setup monitoring (optional)
setup_monitoring() {
    if [[ "${PROMETHEUS_ENABLED}" == "true" ]]; then
        log_info "Setting up monitoring services..."
        # Add monitoring services to docker-compose if needed
        log_info "Monitoring setup not yet implemented in this version."
    fi
}

# Main deployment process
main() {
    log_info "Starting Biometric DID production deployment..."
    echo "Project Directory: $PROJECT_DIR"
    echo "Environment File: $ENV_FILE"
    echo "Domain: $DOMAIN"
    echo

    validate_env
    install_docker
    create_directories
    setup_ssl
    deploy_app
    setup_monitoring

    log_success "🎉 Deployment completed successfully!"
    echo
    log_info "Next steps:"
    echo "  1. Verify your domain DNS points to this server"
    echo "  2. Test the application: https://$DOMAIN"
    echo "  3. Test the API: https://api.$DOMAIN/health"
    echo "  4. Monitor logs: docker-compose --profile production logs -f"
    echo "  5. Setup automated backups (see documentation)"
    echo
    log_info "Useful commands:"
    echo "  Start:  docker-compose --profile production up -d"
    echo "  Stop:   docker-compose --profile production down"
    echo "  Logs:   docker-compose --profile production logs -f"
    echo "  Update: docker-compose --profile production pull && docker-compose --profile production up -d --build"
}

# Run main function
main "$@"
