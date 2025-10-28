# Production Deployment Guide
## Biometric DID System

This guide provides comprehensive instructions for deploying the Biometric DID system to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Development Deployment](#development-deployment)
4. [Production Deployment](#production-deployment)
5. [SSL Certificate Management](#ssl-certificate-management)
6. [Backup and Recovery](#backup-and-recovery)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Security Checklist](#security-checklist)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ or Debian 11+
- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB+ (8GB+ recommended)
- **Storage**: 20GB+ available space
- **Network**: Public IP with DNS configuration

### Software Requirements

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- curl
- openssl

### Domain Requirements

- Registered domain name
- DNS A records pointing to your server:
  - `yourdomain.com` → server IP
  - `api.yourdomain.com` → server IP

### SSL Certificate Requirements

- Email address for Let's Encrypt notifications
- Ports 80 and 443 open and accessible

## Environment Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git ufw

# Configure firewall (allow SSH, HTTP, HTTPS)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create deployment user (optional but recommended)
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
sudo mkdir -p /home/deploy/.ssh
# Copy your SSH public key to /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys
```

### 2. Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/decentralized-did.git
cd decentralized-did

# Create necessary directories
mkdir -p logs data backups nginx/ssl nginx/acme
```

### 3. Configure Environment

```bash
# Copy and edit production environment file
cp .env.example .env.production

# Edit with your settings
nano .env.production
```

**Required Settings:**

```bash
# API Security (Generate secure random keys)
API_SECRET_KEY=your_generated_32_byte_key
JWT_SECRET_KEY=your_generated_32_byte_key

# Domain Configuration
DOMAIN=yourdomain.com
API_URL=https://api.yourdomain.com

# SSL Configuration
SSL_EMAIL=admin@yourdomain.com

# Cardano Configuration
KOIOS_BASE_URL=https://api.koios.rest/api/v1
KOIOS_METADATA_LABEL=674
KOIOS_METADATA_BLOCK_LIMIT=1000
CARDANO_NETWORK=mainnet

# CORS Origins (your production domains)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**Generate secure keys:**

```bash
# Generate API and JWT secrets
python3 -c "import secrets; print('API_SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

## Development Deployment

For local development and testing:

```bash
# Copy development environment
cp .env.example .env.development

# Edit development settings if needed
nano .env.development

# Run development deployment
./deploy-development.sh

# Or manually with docker-compose
docker-compose --profile development up -d --build
```

**Development URLs:**
- Frontend: http://localhost:3003
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Production Deployment

### Automated Deployment

```bash
# Run the production deployment script
./deploy-production.sh
```

This script will:
1. Validate environment configuration
2. Install Docker if needed
3. Create required directories
4. Obtain SSL certificates from Let's Encrypt
5. Deploy all services with proper configuration

### Manual Deployment

If you prefer manual control:

```bash
# 1. Validate environment
python3 -c "
import os
from pathlib import Path
env_file = Path('.env.production')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key = line.split('=')[0]
                if 'SECRET' in key or 'PASSWORD' in key or 'KEY' in key:
                    if 'CHANGE_ME' in line:
                        print(f'ERROR: {key} still has placeholder value')
                        exit(1)
                elif key in ['DOMAIN', 'SSL_EMAIL', 'KOIOS_BASE_URL']:
                    if 'CHANGE_ME' in line or not line.split('=', 1)[1].strip():
                        print(f'ERROR: {key} is required but not set')
                        exit(1)
    print('Environment validation passed')
else:
    print('ERROR: .env.production file not found')
    exit(1)
"

# 2. Create required directories
sudo mkdir -p nginx/ssl nginx/acme
sudo chown -R $USER:$USER nginx/ssl nginx/acme logs data backups

# 3. Obtain SSL certificates
docker-compose --profile production run --rm certbot

# 4. Deploy services
docker-compose --profile production up -d --build

# 5. Verify deployment
curl -f https://yourdomain.com/health
curl -f https://api.yourdomain.com/health
```

### Service Verification

```bash
# Check service status
docker-compose --profile production ps

# Check service logs
docker-compose --profile production logs

# Test API endpoints
curl https://api.yourdomain.com/health
curl https://api.yourdomain.com/docs  # API documentation
```

## SSL Certificate Management

### Initial Certificate Generation

Certificates are automatically obtained during deployment using the `certbot` service.

### Certificate Renewal

Certificates are valid for 90 days and should be renewed when < 30 days remain.

#### Automatic Renewal

The deployment script sets up a cron job for automatic renewal:

```bash
# Check current cron jobs
crontab -l

# Should show:
# 0 12 * * * /path/to/decentralized-did/renew-ssl.sh
```

#### Manual Renewal

```bash
# Run renewal script
./renew-ssl.sh

# Or manually with docker-compose
docker-compose --profile production run --rm certbot renew
docker-compose --profile production restart nginx
```

### Certificate Status

```bash
# Check certificate expiry
openssl x509 -in nginx/ssl/fullchain.pem -noout -dates

# Check certificate details
openssl x509 -in nginx/ssl/fullchain.pem -text -noout
```

## Backup and Recovery

### Automated Backups

The system includes automated backup scripts:

```bash
# Run backup manually
./backup.sh

# Setup automated backups (add to cron)
echo "0 2 * * * /path/to/decentralized-did/backup.sh" | crontab -
```

### Backup Contents

- Application data (`data/` directory)
- Application logs (`logs/` directory)
- Configuration files (sanitized)
- SSL certificates
- Docker volumes

### Recovery Procedure

```bash
# 1. Stop services
docker-compose --profile production down

# 2. Restore from backup
tar -xzf backups/biometric-did-backup-20231201_020000.tar.gz
cp -r biometric-did-backup-20231201_020000/* .

# 3. Restore SSL certificates
cp -r ssl/* nginx/ssl/

# 4. Start services
docker-compose --profile production up -d

# 5. Verify restoration
curl https://yourdomain.com/health
```

## Monitoring and Maintenance

### Health Checks

```bash
# Application health
curl https://yourdomain.com/health
curl https://api.yourdomain.com/health

# Service status
docker-compose --profile production ps

# Resource usage
docker stats
```

### Log Management

```bash
# View application logs
docker-compose --profile production logs -f

# View nginx logs
tail -f nginx/logs/access.log
tail -f nginx/logs/error.log

# Log rotation (configure in docker-compose.yml or use logrotate)
```

### Updates and Maintenance

```bash
# Update application
git pull origin main
docker-compose --profile production build --no-cache
docker-compose --profile production up -d

# Update SSL certificates
./renew-ssl.sh

# Update system packages
sudo apt update && sudo apt upgrade -y
```

### Performance Monitoring

The API servers include built-in metrics endpoints:

```bash
# Koios API metrics
curl https://api.yourdomain.com/metrics/koios

# Response includes:
# - Request count and latency
# - Cache hit/miss ratios
# - Error rates
```

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check service logs
docker-compose --profile production logs

# Check resource usage
docker system df
docker stats

# Restart services
docker-compose --profile production restart
```

#### SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in nginx/ssl/fullchain.pem -noout -dates

# Renew certificates
./renew-ssl.sh

# Check nginx SSL configuration
docker-compose --profile production exec nginx nginx -t
```

#### API Connection Issues

```bash
# Test API connectivity
curl -v https://api.yourdomain.com/health

# Check nginx configuration
docker-compose --profile production exec nginx nginx -T

# Check API server logs
docker-compose --profile production logs backend-api-secure
```

#### Database Issues (if using external DB)

```bash
# Test database connectivity
docker-compose --profile production exec postgres pg_isready

# Check database logs
docker-compose --profile production logs postgres
```

### Log Analysis

```bash
# Search for errors
docker-compose --profile production logs 2>&1 | grep -i error

# Check nginx access patterns
tail -f nginx/logs/access.log | grep " 5.. "

# Monitor API performance
docker-compose --profile production logs backend-api-secure | grep "metrics"
```

### Emergency Recovery

```bash
# Quick restart all services
docker-compose --profile production down
docker-compose --profile production up -d

# Restore from latest backup
LATEST_BACKUP=$(ls -t backups/biometric-did-backup-*.tar.gz | head -1)
tar -xzf "$LATEST_BACKUP"
cp -r biometric-did-backup-*/* .
docker-compose --profile production up -d
```

## Security Checklist

### Pre-Deployment

- [ ] Environment variables configured with secure random keys
- [ ] Domain DNS configured correctly
- [ ] Firewall configured (only necessary ports open)
- [ ] SSL certificates obtained and valid
- [ ] Backup system configured and tested

### Post-Deployment

- [ ] HTTPS redirect working correctly
- [ ] Security headers present in responses
- [ ] API endpoints protected with authentication
- [ ] Rate limiting active and configured
- [ ] Audit logging enabled
- [ ] Backup automation running
- [ ] SSL certificate auto-renewal configured

### Ongoing Maintenance

- [ ] Regular security updates applied
- [ ] SSL certificates renewed before expiry
- [ ] Backups verified regularly
- [ ] Logs monitored for security events
- [ ] Performance metrics reviewed
- [ ] Dependencies kept up-to-date

### Security Headers Verification

```bash
# Check security headers
curl -I https://yourdomain.com

# Should include:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# Content-Security-Policy: ...
```

### Penetration Testing

```bash
# Run basic security tests
docker run --rm -ti instrumentisto/nmap -sV -p 80,443 yourdomain.com
docker run --rm -ti instrumentisto/nmap --script ssl-enum-ciphers -p 443 yourdomain.com

# Check SSL configuration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com < /dev/null
```

---

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review service logs: `docker-compose --profile production logs`
3. Check the project documentation in `docs/`
4. Create an issue in the project repository

## Version Information

- **Application Version**: 1.1.0
- **Docker Images**: Python 3.11, Node 18, Nginx Alpine
- **SSL**: Let's Encrypt with auto-renewal
- **Security**: Rate limiting, JWT auth, security headers
