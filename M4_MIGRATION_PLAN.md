# 🚀 M4 MacBook Migration Plan - Universal Memory System

## Overview
Complete migration guide for transferring the Universal AI Memory System ("Encyclopedia Galactica") from your current Mac to new M4 MacBook, ensuring all components work perfectly.

## 📋 Pre-Migration Checklist (On Current Mac)

### 1. Backup Critical Data
```bash
# Create complete backup of memory system
cd /Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system
tar -czf ~/Desktop/universal-memory-backup-$(date +%Y%m%d).tar.gz .

# Export memory database separately (CRITICAL!)
cp memories.db ~/Desktop/memories-backup-$(date +%Y%m%d).db
cp -r memory_store ~/Desktop/memory_store_backup_$(date +%Y%m%d)/

# Backup browser extension settings
cp -r ~/Library/Application\ Support/Google/Chrome/Default/Extensions ~/Desktop/chrome-extensions-backup/
```

### 2. Document Current State
```bash
# Save current system stats
python3 src/memory_cli.py stats > ~/Desktop/memory-stats-before-migration.txt

# Check Global Capture build
cd global-capture
swift --version > ~/Desktop/swift-version.txt
./build/GlobalCapture --version 2>&1 >> ~/Desktop/app-version.txt

# List installed Python packages
pip3 list > ~/Desktop/python-packages.txt
```

### 3. Export Environment Configuration
```bash
# Save any custom environment variables
echo "# Memory System Environment" > ~/Desktop/memory-env.txt
env | grep -E "(MEMORY|OPENAI|ANTHROPIC)" >> ~/Desktop/memory-env.txt
```

## 🆕 Fresh Install on M4 MacBook

### Phase 1: System Prerequisites

```bash
# 1. Install Xcode Command Line Tools (for Swift/Git)
xcode-select --install

# 2. Install Homebrew (if not via Migration Assistant)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 3. Install Python 3.11+ (for Apple Silicon optimization)
brew install python@3.11

# 4. Install Node.js (for browser extension)
brew install node

# 5. Install useful tools
brew install ripgrep jq wget
```

### Phase 2: Clone Repository

```bash
# Create project structure
mkdir -p ~/Projects/AgentWorkspace/agentforge/backend
cd ~/Projects/AgentWorkspace/agentforge/backend

# Clone the repository (if in git)
# OR copy from Time Machine backup:
cp -r /Volumes/[TimeMachine]/[Latest]/Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system .

# If copying from backup archive:
tar -xzf ~/Desktop/universal-memory-backup-*.tar.gz -C universal-memory-system/
```

### Phase 3: Python Environment Setup

```bash
cd ~/Projects/AgentWorkspace/agentforge/backend/universal-memory-system

# Create virtual environment (recommended for M4)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip3 install --upgrade pip
pip3 install -r requirements.txt

# For M4 optimization, ensure numpy uses Apple Silicon
pip3 install --upgrade --force-reinstall numpy

# Install optional ML dependencies for Apple Silicon
pip3 install tensorflow-macos tensorflow-metal  # Optional for better embeddings
```

### Phase 4: Global Capture App Setup

```bash
cd global-capture

# Clean any Intel builds
rm -rf build/
rm -f GlobalCapture

# Build for Apple Silicon
./build.sh

# CRITICAL: First launch will fail - this is expected!
./build/GlobalCapture

# Grant Accessibility permissions:
# 1. Open System Settings > Privacy & Security > Accessibility
# 2. Click + and add GlobalCapture from universal-memory-system/global-capture/build/
# 3. Toggle ON

# Apply permission fix (our special sauce)
./force-enable-debug.sh

# Install to Applications
./build/install.sh

# Test hotkey
# Press ⌘⇧M - should see menu appear
```

### Phase 5: Database Migration

```bash
# CRITICAL - Restore your memories!
cd ~/Projects/AgentWorkspace/agentforge/backend/universal-memory-system

# Copy database from backup
cp ~/Desktop/memories-backup-*.db memories.db
cp -r ~/Desktop/memory_store_backup_*/* memory_store/

# Verify database integrity
python3 << EOF
import sqlite3
conn = sqlite3.connect('memories.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM memories")
print(f"Total memories: {cursor.fetchone()[0]}")
cursor.execute("PRAGMA integrity_check")
print(f"Integrity: {cursor.fetchone()[0]}")
conn.close()
EOF

# Test memory retrieval
python3 src/memory_cli_simple.py stats
python3 src/memory_cli_simple.py list --limit 5
```

### Phase 6: Start Services

```bash
# Terminal 1: Start Memory API
cd ~/Projects/AgentWorkspace/agentforge/backend/universal-memory-system
python3 src/api_service.py --port 8091

# Terminal 2: Verify API health
curl http://localhost:8091/api/health
curl http://localhost:8091/api/stats

# Test memory search
curl "http://localhost:8091/api/search?q=swift+permissions"
```

### Phase 7: Browser Extension

```bash
cd browser-extension

# Install dependencies
npm install

# Build for Chrome
npm run build:chrome

# Install in Chrome:
# 1. Open chrome://extensions/
# 2. Enable Developer Mode
# 3. Click "Load unpacked"
# 4. Select universal-memory-system/browser-extension/dist/chrome

# Test AI Context Copy feature
# Should include AGENT.md path and fallback content
```

### Phase 8: CLI Tools Setup

```bash
# Test both CLI versions
cd ~/Projects/AgentWorkspace/agentforge/backend/universal-memory-system

# Simple CLI (no dependencies)
python3 src/memory_cli_simple.py stats

# Full CLI (if dependencies installed)
python3 src/memory_cli.py stats

# Create alias for quick access
echo 'alias mem="python3 ~/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/src/memory_cli_simple.py"' >> ~/.zshrc
source ~/.zshrc

# Test alias
mem list --limit 3
```

## ✅ Post-Migration Verification

### System Health Checks

```bash
# 1. Memory System Core
curl http://localhost:8091/api/health | jq .

# 2. Global Capture
# - Press ⌘⇧M anywhere
# - Menu should show "✅ Accessibility: Granted"
# - Test "Capture Selection" with some text selected

# 3. Database Integrity
python3 src/memory_cli_simple.py stats
# Should show same counts as pre-migration

# 4. Search Functionality
python3 src/memory_cli_simple.py search "test query"
# Should return relevant results

# 5. Add New Memory (ultimate test)
python3 src/memory_cli_simple.py add "Successfully migrated to M4 MacBook!" \
  --tags migration,m4,success --importance 10
```

### Component Status Checklist

- [ ] Memory API running on port 8091
- [ ] Database migrated with all memories intact
- [ ] Global Capture app installed and hotkey working
- [ ] Accessibility permissions granted and verified
- [ ] Browser extension installed and AI Context Copy working
- [ ] CLI tools (both simple and full) functional
- [ ] AGENT.md and CLAUDE.md symlink present
- [ ] Python dependencies installed for Apple Silicon
- [ ] Swift build optimized for M4

## 🔧 M4-Specific Optimizations

### Apple Silicon Python Performance
```bash
# Ensure using ARM64 Python
python3 -c "import platform; print(platform.machine())"  # Should show 'arm64'

# Install Apple Silicon optimized packages
pip3 install --upgrade --force-reinstall numpy scipy scikit-learn

# If using embeddings, install Metal-optimized ML
pip3 install tensorflow-macos tensorflow-metal
```

### Global Capture for Apple Silicon
```bash
cd global-capture

# Add M4 optimization flags to build.sh
# Edit build.sh and add:
# swiftc -O -target arm64-apple-macos12.0 ...
```

### Memory Performance Tuning
```python
# Add to src/memory_service.py for M4 optimization
import os
os.environ['OMP_NUM_THREADS'] = '8'  # M4 has 8 performance cores
```

## 🚨 Troubleshooting

### Issue: Global Capture Menu Grayed Out
```bash
cd ~/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/global-capture
./force-enable-debug.sh
# Restart the app
```

### Issue: Python Packages Won't Install
```bash
# Use Rosetta if needed (not recommended)
arch -x86_64 pip3 install [package]

# Better: Find Apple Silicon alternative
pip3 install --no-binary :all: [package]
```

### Issue: Memory Search Slow
```bash
# Rebuild search index
python3 << EOF
from memory_service import get_memory_service
service = get_memory_service()
service.rebuild_index()  # If method exists
EOF
```

### Issue: Browser Extension Not Connecting
```bash
# Check CORS settings in api_service.py
# Ensure localhost is allowed
```

## 📊 Migration Success Metrics

After migration, verify these metrics match your pre-migration state:

1. **Total memory count** matches
2. **All projects** are present
3. **Tag list** is complete
4. **Search returns** expected results
5. **Global Capture** captures new content
6. **Browser extension** copies AI context correctly
7. **Performance** is same or better (M4 should be faster!)

## 🎯 Quick Migration Path (If Time Machine Works Perfectly)

1. Use Migration Assistant with Time Machine
2. Run these commands to verify:
```bash
cd ~/Projects/AgentWorkspace/agentforge/backend/universal-memory-system
python3 src/api_service.py --port 8091  # Start API
python3 src/memory_cli_simple.py stats  # Check memories
cd global-capture && ./force-enable-debug.sh  # Fix permissions
```
3. Re-grant Accessibility permissions in System Settings
4. Test ⌘⇧M hotkey

## 💡 Pro Tips

1. **Keep both machines running** during migration for comparison
2. **Test incrementally** - don't wait until everything is moved
3. **Document any issues** as memories for future reference
4. **M4 is faster** - you might notice improved search speed
5. **Use Universal Control** to operate both Macs during migration

## Final Validation

Once everything is working:
```bash
# Create a victory memory!
mem add "Successfully migrated Universal Memory System to M4 MacBook! All components working perfectly." \
  --tags m4,migration,success,encyclopedia-galactica \
  --importance 10 \
  --project universal-memory-system
```

---

*Good luck with your M4 migration! The Encyclopedia Galactica awaits its new, faster home! 🚀*