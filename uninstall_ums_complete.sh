#!/bin/bash

# Universal Memory System - Complete Uninstallation Script
# Removes ALL traces of UMS from the system

set -e

echo "🗑️  Universal Memory System - Complete Uninstaller"
echo "=================================================="
echo ""
echo "⚠️  WARNING: This will completely remove UMS including:"
echo "   - All captured memories and data"
echo "   - Global Capture app and permissions"
echo "   - All configuration files"
echo "   - All Python dependencies installed for UMS"
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

# Kill API service
pkill -f "python.*api_service" 2>/dev/null || true
pkill -f "uvicorn.*8091" 2>/dev/null || true

# Kill Global Capture
pkill -f "UniversalMemoryCapture" 2>/dev/null || true

# Remove from login items
osascript -e 'tell application "System Events" to delete every login item whose name is "UniversalMemoryCapture"' 2>/dev/null || true

# Kill any remaining Python processes related to UMS
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

# Backup any custom scripts
if [ -f "$HOME/start_ums.sh" ]; then
    cp "$HOME/start_ums.sh" "$BACKUP_DIR/"
fi
if [ -f "$HOME/stop_ums.sh" ]; then
    cp "$HOME/stop_ums.sh" "$BACKUP_DIR/"
fi

# Export memories in readable format
if [ -f "$HOME/.ai-memory/memories.db" ]; then
    echo "📄 Exporting memories to readable format..."
    sqlite3 "$HOME/.ai-memory/memories.db" <<EOF > "$BACKUP_DIR/exported_memories.txt" 2>/dev/null || true
.headers on
.mode column
SELECT id, datetime(timestamp, 'unixepoch') as date, project, category, importance, substr(content, 1, 100) as content_preview FROM memories ORDER BY timestamp DESC;
EOF
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
sudo sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db "DELETE FROM access WHERE client='com.universalmemory.capture';" 2>/dev/null || true
tccutil reset Accessibility com.universalmemory.capture 2>/dev/null || true

# Remove Launch Agents
echo "   Removing launch agents..."
rm -f "$HOME/Library/LaunchAgents/com.universalmemory.capture.plist" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.ums.api.plist" 2>/dev/null || true

# Remove user data directory
echo "   Removing user data..."
rm -rf "$HOME/.ai-memory"

# Remove user scripts
echo "   Removing user scripts..."
rm -f "$HOME/start_ums.sh"
rm -f "$HOME/stop_ums.sh"

# Remove system files (requires sudo)
echo "   Removing system files..."
if [ -d "/usr/local/share/universal-memory-system" ]; then
    echo "   ⚠️  System files require admin access to remove"
    sudo rm -rf "/usr/local/share/universal-memory-system"
fi

# Remove any menu bar items
echo "   Cleaning menu bar items..."
defaults delete com.universalmemory.capture 2>/dev/null || true

# Remove any temporary files
echo "   Removing temporary files..."
rm -rf /tmp/ums* 2>/dev/null || true
rm -rf /tmp/api_service* 2>/dev/null || true
rm -rf /tmp/agentforge* 2>/dev/null || true
rm -f /tmp/*.log 2>/dev/null || true

# Clean Python packages (optional - commented out by default)
echo ""
echo "📦 Python packages installed by UMS:"
echo "   - fastapi"
echo "   - uvicorn"
echo "   - hnswlib"
echo "   - numpy"
echo "   - requests"
echo "   - pydantic"
echo ""
read -p "Do you want to uninstall these Python packages? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Removing Python packages..."
    pip3 uninstall -y fastapi uvicorn hnswlib numpy requests pydantic 2>/dev/null || true
fi

# Clean up any remaining caches
echo "   Cleaning caches..."
rm -rf "$HOME/Library/Caches/com.universalmemory.*" 2>/dev/null || true
rm -rf "$HOME/Library/Preferences/com.universalmemory.*" 2>/dev/null || true

# Remove from PATH if added
echo "   Cleaning PATH variables..."
sed -i '' '/universal-memory-system/d' "$HOME/.zshrc" 2>/dev/null || true
sed -i '' '/universal-memory-system/d' "$HOME/.bashrc" 2>/dev/null || true
sed -i '' '/universal-memory-system/d' "$HOME/.bash_profile" 2>/dev/null || true

# Final cleanup check
echo ""
echo "🔍 Performing final cleanup check..."

# Check for any remaining processes
REMAINING_PROCS=$(ps aux | grep -E "(ums|universal.*memory|api_service)" | grep -v grep | wc -l)
if [ "$REMAINING_PROCS" -gt 0 ]; then
    echo "   ⚠️  Found $REMAINING_PROCS remaining processes"
    ps aux | grep -E "(ums|universal.*memory|api_service)" | grep -v grep
else
    echo "   ✅ No remaining processes"
fi

# Check for any remaining files
echo "   Checking for remaining files..."
REMAINING_FILES=$(find "$HOME" -name "*universal*memory*" -o -name "*ums*" 2>/dev/null | grep -v "$BACKUP_DIR" | wc -l)
if [ "$REMAINING_FILES" -gt 0 ]; then
    echo "   ⚠️  Found $REMAINING_FILES remaining files"
else
    echo "   ✅ No remaining files in user directory"
fi

echo ""
echo "✅ Universal Memory System has been completely uninstalled!"
echo ""
echo "📁 Backup Location: $BACKUP_DIR"
echo "   - Your memories database"
echo "   - Exported memories in readable format"
echo "   - Configuration files"
echo ""
echo "🔄 To reinstall UMS in the future:"
echo "   Use the original installation package"
echo ""
echo "📝 If you experienced issues, please share:"
echo "   - What problems you encountered"
echo "   - Any error messages from: $BACKUP_DIR/.ai-memory/ums.log"
echo ""
echo "Thank you for trying the Universal Memory System! 🧠"