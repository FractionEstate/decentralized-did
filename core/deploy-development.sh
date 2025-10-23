#!/bin/bash
# Biometric DID Development Deployment Script
# This script sets up a local development environment

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CORE_DIR="${PROJECT_DIR}/core"
ENV_FILE="${PROJECT_DIR}/.env.development"
COMPOSE_FILE="${CORE_DIR}/docker-compose.yml"

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

# Check if .env.development exists, create from template if not
setup_env() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_info "Creating development environment file from template..."
        cp "${PROJECT_DIR}/.env.example" "$ENV_FILE"
        log_warning "Please review and update $ENV_FILE with your settings."
        log_info "Using default development settings for now..."
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
        log_info "Alternatively, run: sudo usermod -aG docker $USER && newgrp docker"
        exit 1
    fi

    check_docker_compose
}

# Create required directories
create_directories() {
    log_info "Creating required directories..."
    mkdir -p "$CORE_DIR/logs"
    mkdir -p "$CORE_DIR/data"
    log_success "Directories created."
}

# Check if Docker Compose is available (new or old syntax)
check_docker_compose() {
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        log_info "Using Docker Compose (new syntax)"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        log_info "Using docker-compose (legacy)"
    else
        log_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
}

# Deploy the development environment
deploy_dev() {
    log_info "Deploying Biometric DID development environment..."

    cd "$CORE_DIR"

    # Check Docker Compose command
    check_docker_compose

    # Build and start development services
    $COMPOSE_CMD -f "$COMPOSE_FILE" --profile development up -d --build

    # Wait for services to start
    log_info "Waiting for services to start..."
    sleep 15

    # Check service health
    if $COMPOSE_CMD -f "$COMPOSE_FILE" --profile development ps | grep -q "Up"; then
        log_success "Development environment deployed successfully!"
        echo
        log_info "Services running:"
        $COMPOSE_CMD -f "$COMPOSE_FILE" --profile development ps
        echo
        log_info "Access your application:"
        echo "  Frontend: http://localhost:3003"
        echo "  API:      http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        echo "  Health:   http://localhost:8000/health"
    else
        log_error "Some services failed to start."
        log_info "Check logs with: $COMPOSE_CMD -f $COMPOSE_FILE --profile development logs"
        exit 1
    fi
}

# Show usage information
show_usage() {
    echo "Biometric DID Development Deployment Script"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  start    Start the development environment (default)"
    echo "  stop     Stop the development environment"
    echo "  restart  Restart the development environment"
    echo "  logs     Show logs from all services"
    echo "  status   Show status of all services"
    echo "  clean    Stop and remove all containers and volumes"
    echo
    echo "Examples:"
    echo "  $0              # Start development environment"
    echo "  $0 stop         # Stop all services"
    echo "  $0 logs         # Show logs"
}

# Main function
main() {
    case "${1:-start}" in
        start)
            log_info "Starting Biometric DID development deployment..."
            setup_env
            install_docker
            create_directories
            deploy_dev
            ;;
        stop)
            log_info "Stopping development environment..."
            cd "$CORE_DIR"
            check_docker_compose
            $COMPOSE_CMD -f "$COMPOSE_FILE" --profile development down
            log_success "Development environment stopped."
            ;;
        restart)
            log_info "Restarting development environment..."
            $0 stop
            sleep 2
            $0 start
            ;;
        logs)
            log_info "Showing development environment logs..."
            cd "$CORE_DIR"
            check_docker_compose
            $COMPOSE_CMD -f "$COMPOSE_FILE" --profile development logs -f
            ;;
        status)
            log_info "Development environment status:"
            cd "$CORE_DIR"
            check_docker_compose
            $COMPOSE_CMD -f "$COMPOSE_FILE" --profile development ps
            ;;
        clean)
            log_warning "This will stop and remove all containers, networks, and volumes."
            read -p "Are you sure? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Cleaning development environment..."
                cd "$CORE_DIR"
                check_docker_compose
                $COMPOSE_CMD -f "$COMPOSE_FILE" --profile development down -v --remove-orphans
                log_success "Development environment cleaned."
            fi
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
