#!/bin/bash

# Production Deployment Script for Biometric DID System
# This script automates the deployment process

set -e  # Exit on error

echo "==================================="
echo "Biometric DID Production Deployment"
echo "==================================="
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  Warning: Running as root. Consider using a non-root user for better security."
fi

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✅ Docker installed: $(docker --version)"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose plugin is not installed. Please install Docker Compose first."
    exit 1
fi
echo "✅ Docker Compose installed: $(docker compose version)"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "⚠️  Please edit .env file with your configuration before continuing."
        echo "   Run: nano .env"
        exit 1
    else
        echo "❌ .env.example not found. Cannot proceed."
        exit 1
    fi
fi
echo "✅ .env file found"

# Source environment variables
source .env

# Validate required environment variables
echo ""
echo "🔍 Validating environment configuration..."

REQUIRED_VARS=("API_SECRET_KEY" "JWT_SECRET_KEY" "CORS_ORIGINS" "DOMAIN")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please edit .env file and set all required variables."
    exit 1
fi

# Check if secrets are still default values
if [[ "$API_SECRET_KEY" == *"CHANGE_ME"* ]] || [[ "$JWT_SECRET_KEY" == *"CHANGE_ME"* ]]; then
    echo "❌ Secrets still contain default values. Please generate secure secrets."
    echo ""
    echo "Run the following commands to generate secrets:"
    echo "  python3 -c \"import secrets; print('API_SECRET_KEY=' + secrets.token_urlsafe(32))\""
    echo "  python3 -c \"import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))\""
    exit 1
fi

echo "✅ All required environment variables are set"

# Create required directories
echo ""
echo "📁 Creating required directories..."
mkdir -p logs data nginx/ssl nginx/logs nginx/conf.d
chmod 755 logs data
chmod 700 nginx/ssl
echo "✅ Directories created"

# Check SSL certificates
echo ""
echo "🔐 Checking SSL certificates..."
if [ ! -f nginx/ssl/fullchain.pem ] || [ ! -f nginx/ssl/privkey.pem ]; then
    echo "⚠️  SSL certificates not found."
    echo ""
    echo "For production, you should obtain SSL certificates from Let's Encrypt:"
    echo "  sudo certbot certonly --standalone -d $DOMAIN -d api.$DOMAIN"
    echo ""
    echo "For development, you can generate self-signed certificates:"
    read -p "Generate self-signed certificates for development? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        openssl req -x509 -nodes -days 365 \
            -newkey rsa:2048 \
            -keyout nginx/ssl/privkey.pem \
            -out nginx/ssl/fullchain.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
        chmod 600 nginx/ssl/privkey.pem
        chmod 644 nginx/ssl/fullchain.pem
        echo "✅ Self-signed certificates generated"
    else
        echo "⚠️  Skipping SSL certificate generation. Deployment may fail without certificates."
    fi
else
    echo "✅ SSL certificates found"
fi

# Build Docker images
echo ""
echo "🔨 Building Docker images..."
docker compose build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Docker image build failed. Please check the logs above."
    exit 1
fi
echo "✅ Docker images built successfully"

# Start services
echo ""
echo "🚀 Starting services..."

# Start without nginx first (for testing)
docker compose up -d backend-api demo-wallet

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "🏥 Checking service health..."

# Check backend API
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API is healthy"
else
    echo "❌ Backend API health check failed"
    echo "Logs:"
    docker compose logs backend-api | tail -20
    exit 1
fi

# Check demo wallet
if curl -f -s http://localhost:3003 > /dev/null; then
    echo "✅ Demo Wallet is accessible"
else
    echo "❌ Demo Wallet health check failed"
    echo "Logs:"
    docker compose logs demo-wallet | tail -20
    exit 1
fi

# Start nginx if in production mode
if [ -f nginx/ssl/fullchain.pem ] && [ "$HTTPS_ONLY" = "true" ]; then
    echo ""
    echo "🌐 Starting Nginx reverse proxy..."
    docker compose --profile production up -d nginx

    # Wait for nginx
    sleep 5

    # Check nginx
    if docker compose ps nginx | grep -q "Up"; then
        echo "✅ Nginx is running"
    else
        echo "❌ Nginx failed to start"
        docker compose logs nginx | tail -20
        exit 1
    fi
fi

# Display status
echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "==================================="
echo "Service Status"
echo "==================================="
docker compose ps

echo ""
echo "==================================="
echo "Access Information"
echo "==================================="
echo "Backend API:   http://localhost:8000"
echo "Demo Wallet:   http://localhost:3003"
if [ -f nginx/ssl/fullchain.pem ]; then
    echo "Frontend:      https://$DOMAIN"
    echo "API:           https://api.$DOMAIN"
fi

echo ""
echo "==================================="
echo "Useful Commands"
echo "==================================="
echo "View logs:     docker compose logs -f [service-name]"
echo "Stop services: docker compose down"
echo "Restart:       docker compose restart [service-name]"
echo "Shell access:  docker compose exec [service-name] sh"
echo ""
echo "For production monitoring, check:"
echo "  - Logs:      tail -f logs/*.log"
echo "  - Audit:     tail -f logs/audit.log"
echo "  - Nginx:     tail -f nginx/logs/*.log"
echo ""
