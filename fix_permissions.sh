#!/bin/bash

# Fix permissions for Universal Memory System
# This script ensures all users can properly access and run the system

echo "Fixing permissions for Universal Memory System..."

# Get the directory of this script
UMS_DIR="/usr/local/share/universal-memory-system"

# Detect the actual user (not root from sudo)
if [ -n "$SUDO_USER" ]; then
    ACTUAL_USER="$SUDO_USER"
else
    ACTUAL_USER=$(whoami)
fi

echo "Setting ownership to: $ACTUAL_USER"

# Fix ownership for all files and directories
sudo chown -R "$ACTUAL_USER:staff" "$UMS_DIR"

# Set proper directory permissions (755 - readable and executable by all)
find "$UMS_DIR" -type d -exec chmod 755 {} \;

# Set proper file permissions
# Python files should be readable and executable
find "$UMS_DIR" -name "*.py" -exec chmod 755 {} \;

# Shell scripts should be executable
find "$UMS_DIR" -name "*.sh" -exec chmod 755 {} \;

# Config files should be readable by all
find "$UMS_DIR" -name "*.json" -exec chmod 644 {} \;
find "$UMS_DIR" -name "*.yaml" -exec chmod 644 {} \;
find "$UMS_DIR" -name "*.md" -exec chmod 644 {} \;

# Make CLI tools executable
chmod 755 "$UMS_DIR/subagents/cli/subagent_cli.py" 2>/dev/null || true
chmod 755 "$UMS_DIR/src/memory_cli.py" 2>/dev/null || true
chmod 755 "$UMS_DIR/src/api_service.py" 2>/dev/null || true

# Create a shared directory for cross-user data with proper permissions
SHARED_DIR="$UMS_DIR/shared_data"
if [ ! -d "$SHARED_DIR" ]; then
    mkdir -p "$SHARED_DIR"
fi
chmod 777 "$SHARED_DIR"

# Fix the memory database permissions if it exists
if [ -f "$UMS_DIR/memories.db" ]; then
    chmod 666 "$UMS_DIR/memories.db"
fi

# Ensure log directory is writable by all
LOG_DIR="$UMS_DIR/logs"
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi
chmod 777 "$LOG_DIR"

# Fix virtual environment if it exists
if [ -d "$UMS_DIR/venv" ]; then
    chmod -R 755 "$UMS_DIR/venv"
fi

echo "Permissions fixed!"
echo ""
echo "Summary of changes:"
echo "- All files owned by: $ACTUAL_USER:staff"
echo "- Directories: 755 (readable/executable by all)"
echo "- Python files: 755 (executable)"
echo "- Config files: 644 (readable by all)"
echo "- Shared data dir: 777 (writable by all)"
echo ""
echo "The system should now work for all users."
echo ""
echo "To test with another account, run:"
echo "  python3 $UMS_DIR/src/memory_cli.py list"