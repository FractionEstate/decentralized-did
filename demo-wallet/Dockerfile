# Demo Wallet Dockerfile
# Production-ready container for React/Ionic frontend

FROM node:18-alpine AS builder

LABEL maintainer="Biometric DID Team"
LABEL version="1.1.0"
LABEL description="Production demo wallet for Biometric DID system"

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --production=false --no-audit --no-fund

# Copy source code
COPY . .

# Build for production
ENV NODE_ENV=production
RUN npm run build

# Security scan (optional)
# RUN npm audit --audit-level high

# Production stage
FROM nginx:alpine

LABEL maintainer="Biometric DID Team"
LABEL version="1.1.0"
LABEL description="Production demo wallet for Biometric DID system"

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache curl

# Create nginx user and directories
RUN addgroup -g 1001 -S appgroup && \
  adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G appgroup -g appuser appuser

# Copy built files to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Create default nginx configuration for SPA routing with security headers
RUN echo 'server { \
  listen 80; \
  server_name localhost; \
  root /usr/share/nginx/html; \
  index index.html; \
  \
  # Security headers \
  add_header X-Frame-Options "DENY" always; \
  add_header X-Content-Type-Options "nosniff" always; \
  add_header X-XSS-Protection "1; mode=block" always; \
  add_header Referrer-Policy "strict-origin-when-cross-origin" always; \
  add_header Content-Security-Policy "default-src '\''self'\''; script-src '\''self'\'' '\''unsafe-inline'\'' '\''unsafe-eval'\''; style-src '\''self'\'' '\''unsafe-inline'\''; img-src '\''self'\'' data: https:; font-src '\''self'\'' data:; connect-src '\''self'\'' https:;" always; \
  \
  # SPA routing \
  location / { \
  try_files $uri $uri/ /index.html; \
  } \
  \
  # Static assets with caching \
  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ { \
  expires 1y; \
  add_header Cache-Control "public, immutable"; \
  access_log off; \
  } \
  \
  # Health check \
  location /health { \
  access_log off; \
  return 200 "healthy\n"; \
  add_header Content-Type text/plain; \
  } \
  }' > /etc/nginx/conf.d/default.conf

# Set proper permissions
RUN chown -R appuser:appuser /usr/share/nginx/html && \
  chown -R appuser:appuser /var/cache/nginx && \
  chown -R appuser:appuser /var/log/nginx && \
  chown -R appuser:appuser /etc/nginx/conf.d && \
  touch /var/run/nginx.pid && \
  chown appuser:appuser /var/run/nginx.pid

USER appuser

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
