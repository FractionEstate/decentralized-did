#!/bin/bash

# MCP Server Connectivity Test Script
echo "🧪 Testing MCP Server Connectivity..."

# Test environment setup
echo "=== Environment Test ==="
echo "PATH: $PATH"
echo "NODE_PATH: $NODE_PATH"

# Test system binaries
echo -e "\n=== System Binaries Test ==="
echo "✓ Testing /usr/local/bin/npx:"
/usr/local/bin/npx --version || echo "❌ FAILED"

echo "✓ Testing /usr/local/bin/node:"
/usr/local/bin/node --version || echo "❌ FAILED"

echo "✓ Testing /home/codespace/.local/bin/uvx:"
/home/codespace/.local/bin/uvx --version || echo "❌ FAILED"

# Test MCP servers
echo -e "\n=== MCP Server Test ==="

echo "✓ Testing Playwright MCP server spawn:"
PATH="/usr/local/bin:/usr/bin:/bin" timeout 10s /usr/local/bin/npx --yes @playwright/test --version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Playwright server can be spawned"
else
    echo "  ❌ Playwright server spawn failed"
fi

echo "✓ Testing filesystem MCP server spawn:"
PATH="/usr/local/bin:/usr/bin:/bin:/home/codespace/.local/bin" timeout 10s /home/codespace/.local/bin/uvx --from mcp mcp-server-filesystem --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Filesystem server can be spawned"
else
    echo "  ❌ Filesystem server spawn failed"
fi

echo -e "\n🎯 MCP connectivity test completed!"
echo "If any tests failed, the MCP extension may still have issues."
echo "Try reloading VS Code window after configuration changes."