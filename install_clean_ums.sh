#!/bin/bash

# Universal Memory System - Clean Installation Script
# Creates a fresh UMS installation with empty database for a new user

set -e

echo "🧠 Universal Memory System - Clean Installation"
echo "================================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS only"
    exit 1
fi

# Check for required tools
echo "🔍 Checking system requirements..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "   Please install Python 3 from https://python.org"
    exit 1
fi

# Check for pip3
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

# Check for Ollama (optional but recommended)
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found - semantic search will be disabled"
    echo "   Install from https://ollama.ai for enhanced features"
else
    echo "✅ Ollama found - semantic search will be enabled"
fi

echo "✅ System requirements check passed"
echo ""

# Get installation directory
UMS_DIR="/usr/local/share/universal-memory-system"
USER_DATA_DIR="$HOME/.ai-memory"

echo "📁 Installation directories:"
echo "   System: $UMS_DIR"
echo "   User Data: $USER_DATA_DIR"
echo ""

# Create user data directory with clean database
echo "🗄️  Setting up clean user database..."
mkdir -p "$USER_DATA_DIR"

# Remove any existing database to ensure clean start
if [ -f "$USER_DATA_DIR/memories.db" ]; then
    echo "   Removing existing database for clean start..."
    rm -f "$USER_DATA_DIR/memories.db"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --break-system-packages fastapi uvicorn requests hnswlib numpy pydantic sqlite3

# Check if UMS system files exist
if [ ! -d "$UMS_DIR" ]; then
    echo "❌ UMS system files not found at $UMS_DIR"
    echo "   Please ensure the Universal Memory System is properly installed"
    exit 1
fi

# Set up Global Capture permissions
echo "🔐 Setting up Global Capture permissions..."
cd "$UMS_DIR/global-capture"

# Build Global Capture if not already built
if [ ! -f "build/UniversalMemoryCapture" ]; then
    echo "   Building Global Capture app..."
    ./build.sh
fi

# Install Global Capture
if [ -d "build" ]; then
    echo "   Installing Global Capture app..."
    ./build/install.sh
fi

# Create user-specific startup script
echo "🚀 Creating startup script..."
cat > "$HOME/start_ums.sh" << 'EOF'
#!/bin/bash

# Universal Memory System Startup Script
# Start all UMS services for this user

echo "🧠 Starting Universal Memory System..."

# Start API service in background
cd /usr/local/share/universal-memory-system
python3 src/api_service.py --port 8091 > ~/.ai-memory/ums.log 2>&1 &
UMS_PID=$!

echo "✅ UMS API started on port 8091 (PID: $UMS_PID)"
echo "📊 Dashboard: http://localhost:8091/dashboard"
echo "📚 API Docs: http://localhost:8091/docs"
echo "🔍 Health: http://localhost:8091/api/health"
echo ""
echo "💡 Use ⌘⇧M hotkey to capture text from any app"
echo "📝 Logs: ~/.ai-memory/ums.log"
echo ""
echo "To stop UMS: kill $UMS_PID"

# Save PID for easy stopping
echo $UMS_PID > ~/.ai-memory/ums.pid

# Open dashboard in browser
sleep 3
open "http://localhost:8091/dashboard"
EOF

chmod +x "$HOME/start_ums.sh"

# Create stop script
cat > "$HOME/stop_ums.sh" << 'EOF'
#!/bin/bash

echo "🛑 Stopping Universal Memory System..."

if [ -f ~/.ai-memory/ums.pid ]; then
    PID=$(cat ~/.ai-memory/ums.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ UMS stopped (PID: $PID)"
    else
        echo "ℹ️  UMS was not running"
    fi
    rm -f ~/.ai-memory/ums.pid
else
    # Fallback: kill any UMS processes
    pkill -f "python.*api_service"
    echo "✅ UMS processes terminated"
fi
EOF

chmod +x "$HOME/stop_ums.sh"

# Create uninstall script
cat > "$HOME/uninstall_ums.sh" << 'EOF'
#!/bin/bash

echo "🗑️  Universal Memory System - Complete Uninstaller"
echo "=================================================="
echo ""
echo "⚠️  WARNING: This will completely remove UMS including:"
echo "   - All captured memories and data"
echo "   - Global Capture app and permissions"
echo "   - All configuration files"
echo ""
read -p "Are you sure you want to completely uninstall UMS? (type 'yes' to confirm): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "❌ Uninstallation cancelled"
    exit 0
fi

echo ""
echo "📊 Creating backup before uninstallation..."

# Create final backup
BACKUP_DIR="$HOME/Desktop/UMS_FINAL_BACKUP_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Stop all UMS processes
echo "🛑 Stopping all UMS processes..."
pkill -f "python.*api_service" 2>/dev/null || true
pkill -f "uvicorn.*8091" 2>/dev/null || true
pkill -f "UniversalMemoryCapture" 2>/dev/null || true

if [ -f "$HOME/.ai-memory/ums.pid" ]; then
    PID=$(cat "$HOME/.ai-memory/ums.pid")
    kill $PID 2>/dev/null || true
fi

echo "✅ All processes stopped"

# Backup user data
echo "💾 Backing up user data..."
if [ -d "$HOME/.ai-memory" ]; then
    cp -r "$HOME/.ai-memory" "$BACKUP_DIR/"
    echo "   Backed up memories to: $BACKUP_DIR/.ai-memory"
fi

# Export memories in readable format
if [ -f "$HOME/.ai-memory/memories.db" ]; then
    echo "📄 Exporting memories to readable format..."
    sqlite3 "$HOME/.ai-memory/memories.db" <<SQL > "$BACKUP_DIR/exported_memories.txt" 2>/dev/null || true
.headers on
.mode column
SELECT id, datetime(timestamp, 'unixepoch') as date, project, category, importance, 
       substr(content, 1, 100) as content_preview 
FROM memories ORDER BY timestamp DESC;
SQL
    echo "   Exported memories to: $BACKUP_DIR/exported_memories.txt"
fi

echo ""
echo "🧹 Removing UMS components..."

# Remove Global Capture app
echo "   Removing Global Capture app..."
rm -rf "$HOME/Applications/UniversalMemoryCapture.app" 2>/dev/null || true
rm -rf "/Applications/UniversalMemoryCapture.app" 2>/dev/null || true

# Remove from Accessibility permissions
echo "   Removing Accessibility permissions..."
tccutil reset Accessibility com.universalmemory.capture 2>/dev/null || true

# Remove Launch Agents
echo "   Removing launch agents..."
rm -f "$HOME/Library/LaunchAgents/com.universalmemory.capture.plist" 2>/dev/null || true

# Remove user data directory
echo "   Removing user data..."
rm -rf "$HOME/.ai-memory"

# Remove user scripts
echo "   Removing user scripts..."
rm -f "$HOME/start_ums.sh"
rm -f "$HOME/stop_ums.sh"
rm -f "$HOME/uninstall_ums.sh"

# Remove system files if they exist
echo "   Removing system files..."
if [ -d "/usr/local/share/universal-memory-system" ]; then
    echo "   ⚠️  System files require admin access to remove"
    sudo rm -rf "/usr/local/share/universal-memory-system"
fi

# Remove temporary files
echo "   Removing temporary files..."
rm -rf /tmp/ums* 2>/dev/null || true
rm -f /tmp/*api*.log 2>/dev/null || true

# Clean up caches
echo "   Cleaning caches..."
rm -rf "$HOME/Library/Caches/com.universalmemory.*" 2>/dev/null || true
rm -rf "$HOME/Library/Preferences/com.universalmemory.*" 2>/dev/null || true

echo ""
echo "✅ Universal Memory System has been completely uninstalled!"
echo ""
echo "📁 Backup saved to: $BACKUP_DIR"
echo "   - Your memories database (can be restored if needed)"
echo "   - Exported memories in readable format"
echo ""
echo "Thank you for trying the Universal Memory System! 🧠"
EOF

chmod +x "$HOME/uninstall_ums.sh"

# Create user configuration
echo "⚙️  Creating user configuration..."
cat > "$USER_DATA_DIR/config.json" << EOF
{
    "user_id": "$(whoami)",
    "installation_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "version": "1.0.0",
    "database_path": "$USER_DATA_DIR/memories.db",
    "api_port": 8091,
    "global_capture_enabled": true,
    "semantic_search_enabled": $(command -v ollama &> /dev/null && echo "true" || echo "false"),
    "embedding_provider": "ollama",
    "ollama_model": "nomic-embed-text"
}
EOF

# Test the installation
echo "🧪 Testing installation..."
cd "$UMS_DIR"

# Start API briefly to initialize database
python3 src/api_service.py --port 8091 &
API_PID=$!
sleep 5

# Test health endpoint
if curl -s "http://localhost:8091/api/health" > /dev/null; then
    echo "✅ API test passed"
else
    echo "❌ API test failed"
fi

# Stop test instance
kill $API_PID 2>/dev/null || true

echo ""
echo "🎉 Universal Memory System installation complete!"
echo ""
echo "📋 Quick Start:"
echo "   1. Run: ~/start_ums.sh"
echo "   2. Open dashboard: http://localhost:8091/dashboard"
echo "   3. Use ⌘⇧M to capture text from any app"
echo "   4. Stop with: ~/stop_ums.sh"
echo ""
echo "📁 Your data is stored in: $USER_DATA_DIR"
echo "📊 Dashboard: http://localhost:8091/dashboard"
echo "📚 API Documentation: http://localhost:8091/docs"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Check logs: tail -f ~/.ai-memory/ums.log"
echo "   - Health check: curl http://localhost:8091/api/health"
echo "   - Global Capture permissions: System Preferences > Security & Privacy > Accessibility"
echo ""
echo "Happy memory capturing! 🧠✨"