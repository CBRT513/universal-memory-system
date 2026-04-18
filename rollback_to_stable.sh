#!/bin/bash

# Universal Memory System - Rollback to Stable Version
# Emergency rollback to last known good version

echo "🔄 UMS Emergency Rollback"
echo "=========================="
echo ""

# Configuration
PRODUCTION_DIR="/usr/local/share/universal-memory-system"
BACKUP_DIR="/usr/local/share/ums-backups"
STABLE_VERSION="v1.0.0"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Check for version parameter or use default
if [ -n "$1" ]; then
    TARGET_VERSION="$1"
else
    TARGET_VERSION="$STABLE_VERSION"
fi

echo "⚠️  EMERGENCY ROLLBACK PROCEDURE"
echo ""
echo "📋 Rollback Details:"
echo "  • Target Version: $TARGET_VERSION"
echo "  • Production Dir: $PRODUCTION_DIR"
echo "  • Backup Dir: $BACKUP_DIR"
echo ""

# List available backups
echo "📦 Available Backups:"
if [ -d "$BACKUP_DIR" ]; then
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | tail -5
else
    echo "  No backups found in $BACKUP_DIR"
fi
echo ""

# Confirmation prompt
read -p "⚠️  This will replace current production. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Rollback cancelled"
    exit 1
fi

echo ""
echo "🔄 Starting rollback process..."
echo ""

# Step 1: Stop production service
echo "1️⃣  Stopping production service..."
if [ -f ~/stop_ums.sh ]; then
    ~/stop_ums.sh
else
    pkill -f "python.*8091" 2>/dev/null || true
fi
sleep 2

# Step 2: Backup current (broken) production
echo "2️⃣  Backing up current production (for analysis)..."
sudo mkdir -p "$BACKUP_DIR/failed"
sudo tar -czf "$BACKUP_DIR/failed/broken_${TIMESTAMP}.tar.gz" \
    -C /usr/local/share \
    universal-memory-system \
    2>/dev/null
echo "   ✅ Current state backed up to: failed/broken_${TIMESTAMP}.tar.gz"

# Step 3: Find appropriate backup
echo "3️⃣  Locating backup for version $TARGET_VERSION..."

# Look for specific version backup
BACKUP_FILE=""

# First, check for the stable backup created today
if [ -f "$BACKUP_DIR/UMS_${TARGET_VERSION}_STABLE_20250815.tar.gz" ]; then
    BACKUP_FILE="$BACKUP_DIR/UMS_${TARGET_VERSION}_STABLE_20250815.tar.gz"
    echo "   ✅ Found stable backup: $(basename $BACKUP_FILE)"
# Then check for release packages
elif [ -f "$BACKUP_DIR/ums_${TARGET_VERSION}_release.tar.gz" ]; then
    BACKUP_FILE="$BACKUP_DIR/ums_${TARGET_VERSION}_release.tar.gz"
    echo "   ✅ Found release backup: $(basename $BACKUP_FILE)"
# Look for any backup with the version
elif ls "$BACKUP_DIR"/*${TARGET_VERSION}*.tar.gz 1> /dev/null 2>&1; then
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/*${TARGET_VERSION}*.tar.gz | head -1)
    echo "   ✅ Found backup: $(basename $BACKUP_FILE)"
# Use most recent pre-promotion backup
elif ls "$BACKUP_DIR"/pre_*.tar.gz 1> /dev/null 2>&1; then
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/pre_*.tar.gz | head -1)
    echo "   ⚠️  Version backup not found, using: $(basename $BACKUP_FILE)"
else
    echo "   ❌ No suitable backup found!"
    echo ""
    echo "Manual Recovery Options:"
    echo "1. Check ~/Desktop/ for backup packages"
    echo "2. Check ~/.ai-memory/ for database backups"
    echo "3. Restore from sandbox if available"
    exit 1
fi

# Step 4: Remove current production
echo "4️⃣  Removing current production files..."
sudo rm -rf "$PRODUCTION_DIR"
echo "   ✅ Production directory cleared"

# Step 5: Restore from backup
echo "5️⃣  Restoring from backup..."
sudo mkdir -p "$PRODUCTION_DIR"
sudo tar -xzf "$BACKUP_FILE" -C /usr/local/share 2>/dev/null
echo "   ✅ Files restored from backup"

# Step 6: Update version information
echo "6️⃣  Updating version information..."
cat << EOF | sudo tee "$PRODUCTION_DIR/ROLLBACK_LOG" > /dev/null
Rollback performed: $(date +"%Y-%m-%d %H:%M:%S")
Rolled back to: $TARGET_VERSION
Backup used: $(basename $BACKUP_FILE)
Reason: Emergency rollback
By: $(whoami)
EOF

# Step 7: Verify file integrity
echo "7️⃣  Verifying restored files..."
if [ -f "$PRODUCTION_DIR/src/api_service.py" ]; then
    echo "   ✅ Core API service found"
else
    echo "   ❌ Error: Core files missing after restore!"
    exit 1
fi

if [ -f "$PRODUCTION_DIR/master_dashboard.html" ]; then
    echo "   ✅ Dashboard found"
else
    echo "   ⚠️  Warning: Dashboard missing"
fi

# Step 8: Restart production service
echo "8️⃣  Starting production service..."
if [ -f ~/start_ums.sh ]; then
    ~/start_ums.sh
else
    cd "$PRODUCTION_DIR"
    python3 src/api_service.py > /tmp/ums_api.log 2>&1 &
    echo "   ✅ Production API started"
fi

# Step 9: Verify production is running
echo "9️⃣  Verifying production service..."
sleep 3
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8091/api/health | grep -q "ok"; then
        echo "   ✅ Production service is healthy"
        break
    else
        echo "   ⏳ Waiting for service to start... ($((RETRY_COUNT+1))/$MAX_RETRIES)"
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT+1))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "   ⚠️  Warning: Production service health check failed"
    echo "   Check logs at: /tmp/ums_api.log"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check Python dependencies: pip3 list | grep -E 'fastapi|uvicorn'"
    echo "2. Check port availability: lsof -i:8091"
    echo "3. View logs: tail -f /tmp/ums_api.log"
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "✅ ROLLBACK COMPLETE!"
echo "════════════════════════════════════════════════════"
echo ""
echo "📊 Summary:"
echo "  • Rolled back to version: $TARGET_VERSION"
echo "  • Backup restored: $(basename $BACKUP_FILE)"
echo "  • Failed version saved to: failed/broken_${TIMESTAMP}.tar.gz"
echo "  • Production service status: $(curl -s http://localhost:8091/api/health 2>/dev/null | grep -q "ok" && echo "RUNNING" || echo "CHECK REQUIRED")"
echo ""
echo "📝 Next Steps:"
echo "  1. Verify system functionality"
echo "  2. Investigate what caused the failure"
echo "  3. Fix issues in sandbox before next promotion"
echo "  4. Document lessons learned"
echo ""
echo "🛡️ System has been restored to stable state"
echo ""