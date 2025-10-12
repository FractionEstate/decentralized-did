#!/bin/bash

# Development Deployment Script for Biometric DID System
# Simplified version for dev container environments without Docker

set -e  # Exit on error

echo "==================================="
echo "Biometric DID Development Deployment"
echo "==================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found."
    exit 1
fi
echo "✅ .env file found"

# Source environment variables
source .env

# Check Python
echo ""
echo "📋 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    exit 1
fi
echo "✅ Python installed: $(python3 --version)"

# Check Node.js (for demo-wallet)
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed."
    exit 1
fi
echo "✅ Node.js installed: $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed."
    exit 1
fi
echo "✅ npm installed: $(npm --version)"

# Create required directories
echo ""
echo "📁 Creating required directories..."
mkdir -p logs data
chmod 755 logs data
echo "✅ Directories created"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip3 install -q -r requirements.txt
    echo "✅ Python dependencies installed"
else
    echo "⚠️  requirements.txt not found, skipping Python dependencies"
fi

# Install demo-wallet dependencies
echo ""
echo "📦 Installing demo-wallet dependencies..."
if [ -d demo-wallet ]; then
    cd demo-wallet
    if [ ! -d node_modules ]; then
        echo "Installing npm packages (this may take a few minutes)..."
        npm install
        echo "✅ Demo wallet dependencies installed"
    else
        echo "✅ Demo wallet dependencies already installed"
    fi
    cd ..
else
    echo "⚠️  demo-wallet directory not found"
fi

# Check if API server exists
echo ""
echo "🔍 Checking API server..."
if [ -f api_server_secure.py ]; then
    echo "✅ api_server_secure.py found"
elif [ -f api_server.py ]; then
    echo "✅ api_server.py found (using non-secure version)"
else
    echo "❌ No API server found (api_server_secure.py or api_server.py)"
    exit 1
fi

echo ""
echo "==================================="
echo "✅ Development Setup Complete!"
echo "==================================="
echo ""
echo "To start the services:"
echo ""
echo "1. Start Backend API (Terminal 1):"
if [ -f api_server_secure.py ]; then
    echo "   python3 api_server_secure.py"
else
    echo "   python3 api_server.py"
fi
echo "   Access at: http://localhost:8000"
echo "   Health check: curl http://localhost:8000/health"
echo ""
echo "2. Start Demo Wallet (Terminal 2):"
echo "   cd demo-wallet"
echo "   npm run dev"
echo "   Access at: http://localhost:3003"
echo ""
echo "3. Monitor Logs (Terminal 3):"
echo "   tail -f logs/api_server.log"
echo "   tail -f logs/audit.log"
echo ""
echo "==================================="
echo "Development URLs:"
echo "==================================="
echo "Backend API:   $API_URL"
echo "Demo Wallet:   http://localhost:3003"
echo "API Health:    $API_URL/health"
echo ""
