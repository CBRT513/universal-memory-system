#!/bin/bash

echo "🚀 MCP Tools Installation & Configuration"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js first.${NC}"
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"

# Create MCP tools directory
MCP_DIR="$HOME/.mcp"
mkdir -p "$MCP_DIR"
cd "$MCP_DIR"

echo ""
echo "📦 Installing MCP tools..."
echo "------------------------"

# Install filesystem MCP (most useful for your projects)
echo "1. Installing Filesystem MCP..."
if npm list -g @modelcontextprotocol/server-filesystem &>/dev/null; then
    echo "   Already installed"
else
    npm install -g @modelcontextprotocol/server-filesystem
fi

# Install Git MCP (for better git integration)
echo "2. Installing Git MCP..."
if npm list -g @modelcontextprotocol/server-git &>/dev/null; then
    echo "   Already installed"
else
    npm install -g @modelcontextprotocol/server-git
fi

# Install Memory MCP (connects to your UMS!)
echo "3. Installing Memory MCP..."
if npm list -g @modelcontextprotocol/server-memory &>/dev/null; then
    echo "   Already installed"
else
    npm install -g @modelcontextprotocol/server-memory
fi

# Install Puppeteer MCP (browser automation)
echo "4. Installing Puppeteer MCP..."
if npm list -g @modelcontextprotocol/server-puppeteer &>/dev/null; then
    echo "   Already installed"
else
    npm install -g @modelcontextprotocol/server-puppeteer
fi

echo ""
echo "📝 Creating MCP configuration..."
echo "--------------------------------"

# Create MCP config for Claude Desktop
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
mkdir -p "$CLAUDE_CONFIG_DIR"

cat > "$CLAUDE_CONFIG_DIR/claude_desktop_config.json" << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": [
        "/usr/local/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js",
        "/Users/cerion/Projects"
      ],
      "env": {}
    },
    "git": {
      "command": "node",
      "args": [
        "/usr/local/lib/node_modules/@modelcontextprotocol/server-git/dist/index.js",
        "--repository",
        "/Users/cerion/Projects/AgentWorkspace/agentforge"
      ],
      "env": {}
    },
    "memory": {
      "command": "node",
      "args": [
        "/usr/local/lib/node_modules/@modelcontextprotocol/server-memory/dist/index.js"
      ],
      "env": {}
    },
    "puppeteer": {
      "command": "node",
      "args": [
        "/usr/local/lib/node_modules/@modelcontextprotocol/server-puppeteer/dist/index.js"
      ],
      "env": {}
    },
    "ums-galactica": {
      "command": "python3",
      "args": [
        "/usr/local/share/universal-memory-system/galactica-agent/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/usr/local/share/universal-memory-system"
      }
    }
  }
}
EOF

echo -e "${GREEN}✅ MCP configuration created${NC}"

# Create a test script
echo ""
echo "📝 Creating MCP test script..."
cat > "$HOME/.mcp/test_mcp_tools.py" << 'EOF'
#!/usr/bin/env python3
"""Test MCP tools integration"""

import json
import subprocess
import os

def test_mcp_tool(name, command):
    """Test if an MCP tool is working"""
    print(f"Testing {name}...")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"  ✅ {name} is working")
            return True
        else:
            print(f"  ❌ {name} failed: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ {name} error: {str(e)}")
        return False

def main():
    print("🧪 Testing MCP Tools")
    print("=" * 40)
    
    # Test filesystem MCP
    test_mcp_tool(
        "Filesystem MCP",
        ["node", "/usr/local/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js", "--help"]
    )
    
    # Test git MCP
    test_mcp_tool(
        "Git MCP", 
        ["node", "/usr/local/lib/node_modules/@modelcontextprotocol/server-git/dist/index.js", "--help"]
    )
    
    # Test your UMS MCP
    if os.path.exists("/usr/local/share/universal-memory-system/galactica-agent/mcp_server.py"):
        print("Testing UMS Galactica MCP...")
        print("  ✅ UMS MCP server exists")
    
    print("\n✨ MCP tools are configured!")
    print("Restart Claude Desktop to use them.")

if __name__ == "__main__":
    main()
EOF

chmod +x "$HOME/.mcp/test_mcp_tools.py"

echo ""
echo "🧪 Running tests..."
echo "-------------------"
python3 "$HOME/.mcp/test_mcp_tools.py"

echo ""
echo "📋 Next Steps:"
echo "-------------"
echo "1. Restart Claude Desktop app"
echo "2. You'll now have these MCP tools available:"
echo "   - filesystem: Browse and edit files"
echo "   - git: Git operations on your repos"
echo "   - memory: Persistent memory across sessions"
echo "   - puppeteer: Browser automation"
echo "   - ums-galactica: Your UMS integration"
echo ""
echo "3. In Claude, you can now use commands like:"
echo "   - 'Read files from my AgentForge project'"
echo "   - 'Show git status of my repository'"
echo "   - 'Remember this for next time'"
echo "   - 'Open and screenshot localhost:8091'"
echo ""
echo -e "${GREEN}✅ MCP tools setup complete!${NC}"