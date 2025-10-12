# Production Deployment Guide

**Date**: October 12, 2025
**Phase**: Phase 13 - Production Hardening, Task 10
**Status**: ✅ **COMPLETE**
**Version**: 1.0.0

---

## Overview

This guide provides step-by-step instructions for deploying the Biometric DID system to a production environment. The deployment uses Docker containers, Nginx reverse proxy, Let's Encrypt SSL/TLS certificates, and includes monitoring, backup, and maintenance procedures.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Docker Setup](#docker-setup)
4. [Nginx Reverse Proxy](#nginx-reverse-proxy)
5. [SSL/TLS Certificates](#ssltls-certificates)
6. [Environment Configuration](#environment-configuration)
7. [Deployment Steps](#deployment-steps)
8. [Monitoring & Alerting](#monitoring--alerting)
9. [Backup & Recovery](#backup--recovery)
10. [Maintenance Procedures](#maintenance-procedures)
11. [Troubleshooting](#troubleshooting)
12. [Security Checklist](#security-checklist)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet (HTTPS)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │    Nginx Reverse Proxy       │
          │  (SSL/TLS Termination)       │
          │  Port 443 (HTTPS)            │
          └──────────────┬───────────────┘
                         │
          ┌──────────────┴───────────────┐
          │                              │
          ▼                              ▼
┌─────────────────────┐      ┌─────────────────────┐
│  Demo Wallet        │      │  Backend API        │
│  (React/Ionic)      │      │  (FastAPI)          │
│  Container          │      │  Container          │
│  Port 3003          │      │  Port 8000          │
└─────────────────────┘      └──────────┬──────────┘
                                        │
                                        ▼
                            ┌───────────────────────┐
                            │  Persistent Storage   │
                            │  - Audit logs         │
                            │  - Helper data        │
                            │  - Configuration      │
                            └───────────────────────┘
```

**Components**:
- **Nginx**: Reverse proxy, SSL/TLS termination, static file serving
- **Backend API**: FastAPI server with security hardening
- **Demo Wallet**: React/Ionic SPA served as static files
- **Persistent Storage**: Docker volumes for logs and data

---

## Prerequisites

### System Requirements

**Hardware**:
- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4 GB minimum (8 GB recommended)
- **Disk**: 20 GB minimum (50 GB recommended for logs/backups)
- **Network**: Public IP address with ports 80, 443 open

**Operating System**:
- Ubuntu 22.04 LTS (recommended)
- Debian 11+
- CentOS 8+
- Any Linux with Docker support

### Software Requirements

```bash
# Docker Engine 24.0+
docker --version

# Docker Compose 2.20+
docker compose version

# Git (for cloning repository)
git --version

# Certbot (for Let's Encrypt certificates)
certbot --version
```

### Domain Name

- **Required**: A registered domain name (e.g., `biometric-did.example.com`)
- **DNS**: A record pointing to server IP address
- **Verification**: `dig biometric-did.example.com +short` should return server IP

---

## Docker Setup

### 1. Install Docker

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
sudo docker run hello-world
```

### 2. Configure Docker

```bash
# Add current user to docker group (optional, for non-root access)
sudo usermod -aG docker $USER
newgrp docker

# Enable Docker to start on boot
sudo systemctl enable docker
sudo systemctl start docker

# Verify Docker Compose
docker compose version
```

### 3. Create Docker Network

```bash
# Create bridge network for containers
docker network create biometric-did-network
```

---

## Docker Compose Configuration

### Create `docker-compose.yml`

```yaml
version: '3.8'

services:
  # Backend API
  backend-api:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: biometric-did-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - API_SECRET_KEY=${API_SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - JWT_EXPIRATION_HOURS=${JWT_EXPIRATION_HOURS:-24}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - RATE_LIMIT_ENABLED=true
      - AUDIT_LOG_ENABLED=true
      - HTTPS_ONLY=true
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - biometric-did-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Demo Wallet (Frontend)
  demo-wallet:
    build:
      context: ./demo-wallet
      dockerfile: Dockerfile
    container_name: biometric-did-wallet
    restart: unless-stopped
    ports:
      - "3003:80"
    environment:
      - VITE_API_URL=https://api.${DOMAIN}
    networks:
      - biometric-did-network
    depends_on:
      - backend-api

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: biometric-did-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    networks:
      - biometric-did-network
    depends_on:
      - backend-api
      - demo-wallet

networks:
  biometric-did-network:
    driver: bridge

volumes:
  logs:
  data:
```

### Create `Dockerfile.backend`

```dockerfile
# Backend API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "api_server_secure.py"]
```

### Create `demo-wallet/Dockerfile`

```dockerfile
# Demo Wallet Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## Nginx Reverse Proxy

### 1. Create Nginx Configuration

**File**: `nginx/nginx.conf`

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
}
```

**File**: `nginx/conf.d/biometric-did.conf`

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name biometric-did.example.com api.biometric-did.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# Frontend (Demo Wallet)
server {
    listen 443 ssl http2;
    server_name biometric-did.example.com;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Root directory
    root /usr/share/nginx/html;
    index index.html;

    # Frontend routing (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
}

# Backend API
server {
    listen 443 ssl http2;
    server_name api.biometric-did.example.com;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy to backend API
    location / {
        proxy_pass http://backend-api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting (additional layer)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
}
```

---

## SSL/TLS Certificates

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get install -y certbot

# Stop Nginx temporarily
sudo systemctl stop nginx

# Obtain certificate (standalone mode)
sudo certbot certonly --standalone \
    -d biometric-did.example.com \
    -d api.biometric-did.example.com \
    --email admin@example.com \
    --agree-tos \
    --non-interactive

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/biometric-did.example.com/fullchain.pem \
    ./nginx/ssl/fullchain.pem
sudo cp /etc/letsencrypt/live/biometric-did.example.com/privkey.pem \
    ./nginx/ssl/privkey.pem

# Set permissions
sudo chmod 644 ./nginx/ssl/fullchain.pem
sudo chmod 600 ./nginx/ssl/privkey.pem

# Restart Nginx
sudo systemctl start nginx
```

### Option 2: Self-Signed Certificates (Development)

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=biometric-did.example.com"

# Set permissions
chmod 600 nginx/ssl/privkey.pem
chmod 644 nginx/ssl/fullchain.pem
```

### Certificate Renewal (Let's Encrypt)

```bash
# Create renewal script
cat > /etc/cron.daily/certbot-renew << 'EOF'
#!/bin/bash
certbot renew --quiet --post-hook "docker compose -f /path/to/docker-compose.yml restart nginx"
EOF

# Make executable
chmod +x /etc/cron.daily/certbot-renew

# Test renewal
sudo certbot renew --dry-run
```

---

## Environment Configuration

### 1. Create `.env` File

```bash
# Create environment file
cat > .env << 'EOF'
# API Security
API_SECRET_KEY=<generate_with_secrets.token_urlsafe(32)>
JWT_SECRET_KEY=<generate_with_secrets.token_urlsafe(32)>
JWT_EXPIRATION_HOURS=24

# CORS Configuration
CORS_ORIGINS=https://biometric-did.example.com

# Domain Configuration
DOMAIN=biometric-did.example.com

# Feature Flags
RATE_LIMIT_ENABLED=true
AUDIT_LOG_ENABLED=true
HTTPS_ONLY=true
EOF

# Set secure permissions
chmod 600 .env
```

### 2. Generate Secrets

```bash
# Generate API secret key
python3 << 'PYTHON'
import secrets
print(f"API_SECRET_KEY={secrets.token_urlsafe(32)}")
PYTHON

# Generate JWT secret key
python3 << 'PYTHON'
import secrets
print(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}")
PYTHON
```

### 3. Update `.env` File

Replace `<generate_with_secrets.token_urlsafe(32)>` with generated values.

---

## Deployment Steps

### 1. Clone Repository

```bash
# Clone repository
git clone https://github.com/FractionEstate/decentralized-did.git
cd decentralized-did
```

### 2. Create Required Directories

```bash
# Create directories
mkdir -p logs data nginx/ssl nginx/logs nginx/conf.d

# Set permissions
chmod 755 logs data
chmod 700 nginx/ssl
```

### 3. Configure Environment

```bash
# Copy and edit .env file
cp .env.example .env
nano .env  # Edit with actual values
```

### 4. Build and Start Containers

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# Verify containers are running
docker compose ps
```

### 5. Verify Deployment

```bash
# Check container logs
docker compose logs -f backend-api
docker compose logs -f demo-wallet
docker compose logs -f nginx

# Test health endpoint
curl -k https://api.biometric-did.example.com/health

# Test frontend
curl -k https://biometric-did.example.com
```

### 6. Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

---

## Monitoring & Alerting

### 1. Container Health Monitoring

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Monitor container resources
docker stats
```

### 2. Log Monitoring

```bash
# Tail API logs
docker compose logs -f backend-api | grep ERROR

# Tail audit logs
tail -f logs/audit.log

# Tail Nginx logs
tail -f nginx/logs/access.log
tail -f nginx/logs/error.log
```

### 3. Prometheus & Grafana (Optional)

**Add to `docker-compose.yml`**:

```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - biometric-did-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - biometric-did-network
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  grafana-data:
```

**Create `prometheus/prometheus.yml`**:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend-api'
    static_configs:
      - targets: ['backend-api:8000']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']  # Requires nginx-prometheus-exporter
```

### 4. Uptime Monitoring

**Use external services**:
- **UptimeRobot**: Free monitoring, 5-minute checks
- **Pingdom**: Professional monitoring with alerting
- **StatusCake**: Multi-location monitoring

**Configure health check endpoint**:
```
URL: https://api.biometric-did.example.com/health
Expected: 200 OK
Interval: 5 minutes
```

---

## Backup & Recovery

### 1. Backup Script

**Create `backup.sh`**:

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/backups/biometric-did"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="biometric-did_${TIMESTAMP}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Docker volumes
docker run --rm \
    -v biometric-did_logs:/data/logs \
    -v biometric-did_data:/data/data \
    -v "$BACKUP_DIR":/backup \
    alpine tar czf "/backup/${BACKUP_NAME}_volumes.tar.gz" -C /data .

# Backup configuration files
tar czf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" \
    .env \
    docker-compose.yml \
    nginx/

# Backup SSL certificates
tar czf "$BACKUP_DIR/${BACKUP_NAME}_ssl.tar.gz" \
    nginx/ssl/

# Remove backups older than 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_NAME}"
```

**Make executable**:
```bash
chmod +x backup.sh
```

**Schedule daily backups**:
```bash
# Add to crontab
crontab -e

# Run daily at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/biometric-did-backup.log 2>&1
```

### 2. Restore Procedure

```bash
#!/bin/bash

# Stop services
docker compose down

# Restore volumes
cd /backups/biometric-did
tar xzf biometric-did_TIMESTAMP_volumes.tar.gz -C /

# Restore configuration
tar xzf biometric-did_TIMESTAMP_config.tar.gz

# Restore SSL certificates
tar xzf biometric-did_TIMESTAMP_ssl.tar.gz

# Restart services
docker compose up -d

echo "Restore completed"
```

---

## Maintenance Procedures

### 1. Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker compose build

# Restart with zero downtime (rolling update)
docker compose up -d --no-deps --build backend-api
docker compose up -d --no-deps --build demo-wallet
```

### 2. Database Cleanup

```bash
# Cleanup old audit logs (keep 90 days)
find logs/audit.log* -mtime +90 -delete

# Rotate logs
logrotate /etc/logrotate.d/biometric-did
```

**Create `/etc/logrotate.d/biometric-did`**:

```
/path/to/logs/*.log {
    daily
    rotate 90
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker compose restart backend-api
    endscript
}
```

### 3. Security Updates

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update Docker images
docker compose pull
docker compose up -d

# Check for vulnerabilities
docker scout cves biometric-did-api
```

---

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker compose logs backend-api

# Common causes:
# - Missing environment variables
# - Port already in use
# - Permission issues

# Solution: Check .env file and port availability
netstat -tuln | grep 8000
```

#### 2. SSL Certificate Errors

```bash
# Verify certificate
openssl s_client -connect api.biometric-did.example.com:443 -showcerts

# Check certificate expiration
openssl x509 -in nginx/ssl/fullchain.pem -noout -dates

# Renew certificate
sudo certbot renew --force-renewal
```

#### 3. Rate Limiting Too Aggressive

```bash
# Temporarily disable rate limiting
# Edit .env
RATE_LIMIT_ENABLED=false

# Restart API
docker compose restart backend-api
```

#### 4. CORS Errors

```bash
# Check CORS configuration
echo $CORS_ORIGINS

# Update .env with correct origins
CORS_ORIGINS=https://biometric-did.example.com,https://www.biometric-did.example.com

# Restart API
docker compose restart backend-api
```

#### 5. High Memory Usage

```bash
# Check container resource usage
docker stats

# Limit container resources (add to docker-compose.yml)
services:
  backend-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## Security Checklist

### Pre-Deployment

- [ ] Generate strong API_SECRET_KEY and JWT_SECRET_KEY (32+ bytes)
- [ ] Configure CORS with specific origins (no wildcards)
- [ ] Enable HTTPS_ONLY mode
- [ ] Set secure file permissions (600 for .env, 700 for ssl/)
- [ ] Review and update Nginx security headers
- [ ] Enable rate limiting
- [ ] Configure audit logging
- [ ] Set up firewall rules (ufw or iptables)

### Post-Deployment

- [ ] Verify SSL/TLS certificate is valid and not self-signed
- [ ] Test all API endpoints with authentication
- [ ] Verify rate limiting is working
- [ ] Check audit logs are being written
- [ ] Test CORS configuration from allowed origins
- [ ] Verify security headers in HTTP responses
- [ ] Run security scan (Nmap, Nikto, or similar)
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Document all credentials in secure password manager

### Ongoing Maintenance

- [ ] Monitor audit logs weekly for suspicious activity
- [ ] Review and rotate API keys quarterly
- [ ] Update Docker images monthly
- [ ] Renew SSL certificates (automated with Let's Encrypt)
- [ ] Test backup restoration procedure quarterly
- [ ] Review and update security headers annually
- [ ] Conduct security audit annually

---

## Performance Optimization

### 1. Nginx Caching

```nginx
# Add to nginx.conf
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

# In server block
location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_use_stale error timeout updating;
    add_header X-Cache-Status $upstream_cache_status;

    proxy_pass http://backend-api:8000;
}
```

### 2. Database Connection Pooling

```python
# In api_server_secure.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### 3. CDN Integration

```bash
# Use CloudFlare or AWS CloudFront for static assets
# Configure in demo-wallet build:
VITE_CDN_URL=https://cdn.biometric-did.example.com npm run build
```

---

## Scaling Considerations

### Horizontal Scaling

```yaml
# docker-compose.yml with multiple API instances
services:
  backend-api:
    deploy:
      replicas: 3
    ...

  # Add load balancer
  load-balancer:
    image: haproxy:latest
    ports:
      - "8000:8000"
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg
```

### Database Clustering

```yaml
# Add PostgreSQL for persistent storage
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: biometric_did
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

---

## Conclusion

This deployment guide provides a production-ready setup for the Biometric DID system with:
- ✅ Docker containerization for easy deployment
- ✅ Nginx reverse proxy with SSL/TLS termination
- ✅ Let's Encrypt automated certificate management
- ✅ Comprehensive monitoring and logging
- ✅ Automated backup procedures
- ✅ Security hardening throughout
- ✅ Troubleshooting and maintenance guides

**Production Readiness**: 🟢 **Ready for deployment**

**Estimated Deployment Time**: **2-3 hours** (including SSL setup)

---

**Prepared by**: GitHub Copilot
**Date**: October 12, 2025
**Phase**: Phase 13, Task 10
**Status**: ✅ **COMPLETE**
**Version**: 1.0.0
