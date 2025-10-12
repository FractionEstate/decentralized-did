#!/bin/bash

# Health Check Script for Biometric DID System
# Checks the health of all services and reports status

set -e

echo "==================================="
echo "Biometric DID Health Check"
echo "==================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
echo "📦 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Check containers
echo ""
echo "🐳 Checking containers..."

CONTAINERS=("biometric-did-api" "biometric-did-wallet" "biometric-did-nginx")
ALL_HEALTHY=true

for container in "${CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-healthcheck")

        if [ "$STATUS" = "healthy" ] || [ "$STATUS" = "no-healthcheck" ]; then
            UPTIME=$(docker inspect --format='{{.State.StartedAt}}' "$container" | xargs -I {} date -d {} '+%Y-%m-%d %H:%M:%S')
            echo -e "${GREEN}✅ $container${NC} (up since $UPTIME)"
        else
            echo -e "${RED}❌ $container${NC} (status: $STATUS)"
            ALL_HEALTHY=false
        fi
    else
        echo -e "${RED}❌ $container${NC} (not running)"
        ALL_HEALTHY=false
    fi
done

# Check backend API endpoint
echo ""
echo "🔌 Checking API endpoints..."

if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    RESPONSE=$(curl -s http://localhost:8000/health)
    echo -e "${GREEN}✅ Backend API /health${NC}: $RESPONSE"
else
    echo -e "${RED}❌ Backend API /health is not responding${NC}"
    ALL_HEALTHY=false
fi

# Check demo wallet
if curl -f -s http://localhost:3003 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Demo Wallet${NC} is accessible"
else
    echo -e "${RED}❌ Demo Wallet is not accessible${NC}"
    ALL_HEALTHY=false
fi

# Check disk space
echo ""
echo "💾 Checking disk space..."
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo -e "${RED}⚠️  Disk usage: ${DISK_USAGE}% (critical)${NC}"
    ALL_HEALTHY=false
elif [ "$DISK_USAGE" -gt 60 ]; then
    echo -e "${YELLOW}⚠️  Disk usage: ${DISK_USAGE}% (warning)${NC}"
else
    echo -e "${GREEN}✅ Disk usage: ${DISK_USAGE}%${NC}"
fi

# Check log sizes
echo ""
echo "📄 Checking log sizes..."
if [ -d logs ]; then
    LOG_SIZE=$(du -sh logs | awk '{print $1}')
    echo -e "${GREEN}✅ Log directory size: $LOG_SIZE${NC}"

    # Warn if logs are too large
    LOG_SIZE_MB=$(du -sm logs | awk '{print $1}')
    if [ "$LOG_SIZE_MB" -gt 1000 ]; then
        echo -e "${YELLOW}⚠️  Logs exceed 1GB, consider rotation${NC}"
    fi
fi

# Check SSL certificates
echo ""
echo "🔐 Checking SSL certificates..."
if [ -f nginx/ssl/fullchain.pem ]; then
    EXPIRY=$(openssl x509 -in nginx/ssl/fullchain.pem -noout -enddate | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

    if [ "$DAYS_LEFT" -lt 7 ]; then
        echo -e "${RED}❌ SSL certificate expires in $DAYS_LEFT days${NC}"
        ALL_HEALTHY=false
    elif [ "$DAYS_LEFT" -lt 30 ]; then
        echo -e "${YELLOW}⚠️  SSL certificate expires in $DAYS_LEFT days${NC}"
    else
        echo -e "${GREEN}✅ SSL certificate valid for $DAYS_LEFT days${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No SSL certificate found${NC}"
fi

# Check memory usage
echo ""
echo "🧠 Checking memory usage..."
MEMORY_USAGE=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | tail -n +2)
echo "$MEMORY_USAGE"

# Final status
echo ""
echo "==================================="
if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✅ All systems operational${NC}"
    exit 0
else
    echo -e "${RED}❌ Some issues detected${NC}"
    echo ""
    echo "To view logs:"
    echo "  docker compose logs -f [service-name]"
    echo ""
    echo "To restart services:"
    echo "  docker compose restart [service-name]"
    exit 1
fi
