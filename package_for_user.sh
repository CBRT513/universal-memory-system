#!/bin/bash

# Package Universal Memory System for Distribution
# Creates a clean package for a new user with all necessary files

echo "📦 Packaging Universal Memory System for Distribution"
echo "====================================================="
echo ""

# Set source and destination directories
SOURCE_DIR="/usr/local/share/universal-memory-system"
PACKAGE_NAME="universal-memory-system-$(date +%Y%m%d)"
TEMP_DIR="/tmp/$PACKAGE_NAME"
OUTPUT_FILE="$HOME/Desktop/$PACKAGE_NAME.tar.gz"

# Create temporary directory
echo "📁 Creating package structure..."
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copy essential files only (no user data)
echo "📋 Copying system files..."

# Core system files
mkdir -p "$TEMP_DIR/src"
cp -r "$SOURCE_DIR/src/"*.py "$TEMP_DIR/src/" 2>/dev/null || true

# Configuration files
cp "$SOURCE_DIR/requirements.txt" "$TEMP_DIR/"
cp "$SOURCE_DIR/setup.py" "$TEMP_DIR/" 2>/dev/null || true

# Dashboard files
cp "$SOURCE_DIR/master_dashboard.html" "$TEMP_DIR/"
cp "$SOURCE_DIR/action_plans_viewer.html" "$TEMP_DIR/"

# Documentation
cp "$SOURCE_DIR/NEW_USER_GUIDE.md" "$TEMP_DIR/"
cp "$SOURCE_DIR/README.md" "$TEMP_DIR/" 2>/dev/null || true

# Installation script
cp "$SOURCE_DIR/install_clean_ums.sh" "$TEMP_DIR/"
chmod +x "$TEMP_DIR/install_clean_ums.sh"

# Global capture app
echo "📱 Copying Global Capture app..."
mkdir -p "$TEMP_DIR/global-capture"
cp -r "$SOURCE_DIR/global-capture/"*.swift "$TEMP_DIR/global-capture/" 2>/dev/null || true
cp -r "$SOURCE_DIR/global-capture/"*.sh "$TEMP_DIR/global-capture/" 2>/dev/null || true
cp "$SOURCE_DIR/global-capture/README.md" "$TEMP_DIR/global-capture/" 2>/dev/null || true

# Browser extension (optional)
if [ -d "$SOURCE_DIR/browser-extension" ]; then
    echo "🌐 Copying browser extension..."
    mkdir -p "$TEMP_DIR/browser-extension"
    cp -r "$SOURCE_DIR/browser-extension/"* "$TEMP_DIR/browser-extension/" 2>/dev/null || true
fi

# Create quick start script
echo "🚀 Creating quick start script..."
cat > "$TEMP_DIR/QUICK_START.sh" << 'EOF'
#!/bin/bash

echo "🧠 Universal Memory System - Quick Start"
echo "========================================"
echo ""
echo "Welcome! This will set up UMS on your Mac."
echo ""
echo "📋 Steps:"
echo "1. Install dependencies and set up UMS"
echo "2. Grant permissions for Global Capture"
echo "3. Start the system"
echo ""
read -p "Ready to begin? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./install_clean_ums.sh
else
    echo "Installation cancelled. Run this script when ready!"
fi
EOF

chmod +x "$TEMP_DIR/QUICK_START.sh"

# Create a README for the package
cat > "$TEMP_DIR/README_FIRST.txt" << 'EOF'
🧠 UNIVERSAL MEMORY SYSTEM - INSTALLATION PACKAGE
=================================================

This package contains everything needed to install the Universal Memory System
on your Mac - your personal AI-powered knowledge management system.

📋 WHAT'S INCLUDED:
- Universal Memory System core files
- Global Capture app for system-wide text capture
- Web dashboard for searching and managing memories
- Installation scripts and documentation

🚀 TO GET STARTED:
1. Open Terminal
2. Navigate to this directory: cd universal-memory-system-[date]
3. Run: ./QUICK_START.sh
4. Follow the prompts

📚 DOCUMENTATION:
- NEW_USER_GUIDE.md - Complete guide on what UMS is and how to use it
- README.md - Technical documentation
- After installation: http://localhost:8091/dashboard

⚡ QUICK INSTALLATION (if you know what you're doing):
   ./install_clean_ums.sh

💡 REQUIREMENTS:
- macOS 10.15 or later
- Python 3 installed
- Admin access for permissions

🔧 SUPPORT:
- Check NEW_USER_GUIDE.md for detailed instructions
- Dashboard has built-in help at http://localhost:8091/dashboard
- Logs are at ~/.ai-memory/ums.log after installation

Happy memory capturing! 🎉
EOF

# Create the package
echo "📦 Creating compressed package..."
cd /tmp
tar -czf "$OUTPUT_FILE" "$PACKAGE_NAME"

# Calculate package size
PACKAGE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

# Clean up
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Package created successfully!"
echo ""
echo "📦 Package Details:"
echo "   Location: $OUTPUT_FILE"
echo "   Size: $PACKAGE_SIZE"
echo "   Name: $PACKAGE_NAME.tar.gz"
echo ""
echo "📋 Distribution Instructions:"
echo "   1. Send the file: $PACKAGE_NAME.tar.gz"
echo "   2. Have user extract: tar -xzf $PACKAGE_NAME.tar.gz"
echo "   3. Have user run: cd $PACKAGE_NAME && ./QUICK_START.sh"
echo ""
echo "📚 The package includes:"
echo "   - Complete installation guide (NEW_USER_GUIDE.md)"
echo "   - Quick start script for easy setup"
echo "   - Clean installation (no existing user data)"
echo "   - All necessary system files"
echo ""
echo "🎯 Ready to share with your test user!"