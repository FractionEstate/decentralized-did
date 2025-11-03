#!/bin/bash

# Decentralized DID Development Environment Setup Script
echo "🚀 Setting up Decentralized DID development environment..."

# Ensure we're in the workspace directory
cd /workspaces/decentralized-did

# Create system-wide symlinks for Node.js tools (MCP compatibility)
echo "📦 Setting up Node.js tools for MCP compatibility..."
sudo ln -sf /home/codespace/nvm/current/bin/node /usr/local/bin/node 2>/dev/null || true
sudo ln -sf /home/codespace/nvm/current/bin/npm /usr/local/bin/npm 2>/dev/null || true  
sudo ln -sf /home/codespace/nvm/current/bin/npx /usr/local/bin/npx 2>/dev/null || true

# Install Python SDK in development mode
echo "🐍 Installing Python SDK..."
if [ -d "sdk" ]; then
    cd sdk
    pip install -e . 2>/dev/null || echo "SDK installation skipped (may need manual setup)"
    cd ..
fi

# Install demo wallet dependencies
echo "💳 Installing demo wallet dependencies..."
if [ -d "demo-wallet" ]; then
    cd demo-wallet
    npm ci 2>/dev/null || echo "Wallet dependencies installation skipped (may need manual setup)"
    cd ..
fi

# Make test scripts executable
echo "🧪 Setting up test scripts..."
chmod +x test-mcp-servers.sh 2>/dev/null || true

# Create MCP configuration directories
echo "⚙️ Setting up MCP configuration..."
mkdir -p /home/codespace/.config/mcp

# Set proper permissions
chown -R codespace:codespace /home/codespace/.config 2>/dev/null || true

# Verify Node.js tools are accessible
echo "✅ Verification:"
echo "   Node.js: $(node --version 2>/dev/null || echo 'Not found')"
echo "   npm: $(npm --version 2>/dev/null || echo 'Not found')" 
echo "   npx: $(npx --version 2>/dev/null || echo 'Not found')"
echo "   uvx: $(uvx --version 2>/dev/null || echo 'Not found')"

echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Reload VS Code window to apply MCP configuration"
echo "2. Run './test-mcp-servers.sh' to verify MCP tools"
echo "3. Use VS Code tasks to start development servers"