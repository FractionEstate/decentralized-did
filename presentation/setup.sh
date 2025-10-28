#!/bin/bash

# Biometric DID Presentation - Quick Setup Script
# For Cardano Summit 2025

set -e

echo "🚀 Setting up Biometric DID Presentation..."
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found"
    echo "Please run this script from /workspaces/decentralized-did/presentation/"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check for errors
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🏗️  Building for production..."
npm run build

# Check build status
if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
else
    echo "❌ Build failed"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo ""
echo "1. Start development server:"
echo "   npm run dev"
echo "   → http://localhost:3000"
echo ""
echo "2. Deploy to Vercel:"
echo "   npm run deploy"
echo ""
echo "3. Or push to GitHub and connect Vercel:"
echo "   git add ."
echo "   git commit -m 'Add presentation website'"
echo "   git push"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Overview and features"
echo "   - DEPLOYMENT.md - Deployment guide"
echo "   - STAGE_SCRIPT.md - Presentation script"
echo ""
echo "🎤 Good luck at Cardano Summit 2025!"
echo ""
