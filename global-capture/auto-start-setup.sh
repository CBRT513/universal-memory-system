#!/bin/bash
#
# Universal AI Memory - Auto-Start Setup Script
# Configures the Global Capture Service to start automatically
#

set -e

echo "🚀 Setting up Universal Memory Capture Auto-Start"
echo "═══════════════════════════════════════════════"

USER_HOME="$HOME"
LAUNCH_AGENTS_DIR="$USER_HOME/Library/LaunchAgents"
PLIST_NAME="com.universalmemory.globalcapture.plist"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$PLIST_NAME"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy and customize the plist file
echo "📝 Creating launch agent plist..."
sed "s|%USER%|$(whoami)|g" launch-daemon.plist > "$PLIST_PATH"

# Load the launch agent
echo "🔄 Loading launch agent..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true  # Ignore errors if not loaded
launchctl load "$PLIST_PATH"

echo "✅ Auto-start configured successfully!"
echo ""
echo "📋 What this does:"
echo "   • Universal Memory Capture will start automatically when you log in"
echo "   • The service will restart if it crashes"
echo "   • Logs will be saved to ~/Library/Logs/"
echo ""
echo "🔧 Management commands:"
echo "   • Stop:  launchctl unload $PLIST_PATH"
echo "   • Start: launchctl load $PLIST_PATH"
echo "   • Check: launchctl list | grep universalmemory"
echo ""
echo "🗑️  To remove auto-start:"
echo "   launchctl unload $PLIST_PATH && rm $PLIST_PATH"