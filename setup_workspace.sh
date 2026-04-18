#!/bin/bash

# Universal Memory System - Workspace Setup
# Creates separate workspaces for personal and work accounts

echo "Universal Memory System - Workspace Configuration"
echo "=================================================="
echo ""

# Detect current user
CURRENT_USER=$(whoami)
UMS_BASE="/usr/local/share/universal-memory-system"

# Function to create workspace
create_workspace() {
    local PROFILE=$1
    local PORT=$2
    local DB_NAME=$3
    
    echo "Setting up $PROFILE workspace..."
    
    # Create profile-specific directories
    PROFILE_DIR="$HOME/.ums-$PROFILE"
    mkdir -p "$PROFILE_DIR"
    mkdir -p "$PROFILE_DIR/memories"
    mkdir -p "$PROFILE_DIR/logs"
    mkdir -p "$PROFILE_DIR/config"
    mkdir -p "$PROFILE_DIR/subagent-outputs"
    
    # Create profile-specific config
    cat > "$PROFILE_DIR/config/settings.json" << EOF
{
    "profile": "$PROFILE",
    "user": "$CURRENT_USER",
    "api_port": $PORT,
    "database": "$PROFILE_DIR/memories/$DB_NAME",
    "log_dir": "$PROFILE_DIR/logs",
    "subagent_output": "$PROFILE_DIR/subagent-outputs",
    "memory_namespace": "${PROFILE}_memories",
    "tags_prefix": "${PROFILE}",
    "created": "$(date -Iseconds)"
}
EOF
    
    # Create start script for this profile
    cat > "$PROFILE_DIR/start.sh" << 'EOF'
#!/bin/bash
PROFILE_DIR="$(dirname "$0")"
CONFIG="$PROFILE_DIR/config/settings.json"
PORT=$(python3 -c "import json; print(json.load(open('$CONFIG'))['api_port'])")
DB=$(python3 -c "import json; print(json.load(open('$CONFIG'))['database'])")

echo "Starting Universal Memory System - $(basename $PROFILE_DIR | sed 's/.ums-//')"
echo "API Port: $PORT"
echo "Database: $DB"

export UMS_PROFILE="$(basename $PROFILE_DIR | sed 's/.ums-//')"
export UMS_CONFIG="$CONFIG"
export MEMORY_DB_PATH="$DB"
export MEMORY_API_PORT=$PORT

python3 /usr/local/share/universal-memory-system/src/api_service.py --port $PORT
EOF
    
    chmod +x "$PROFILE_DIR/start.sh"
    
    # Create memory CLI wrapper
    cat > "$PROFILE_DIR/memory.sh" << 'EOF'
#!/bin/bash
PROFILE_DIR="$(dirname "$0")"
CONFIG="$PROFILE_DIR/config/settings.json"
export UMS_PROFILE="$(basename $PROFILE_DIR | sed 's/.ums-//')"
export UMS_CONFIG="$CONFIG"
export MEMORY_DB_PATH=$(python3 -c "import json; print(json.load(open('$CONFIG'))['database'])")
export MEMORY_API_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG'))['api_port'])")

python3 /usr/local/share/universal-memory-system/src/memory_cli.py "$@"
EOF
    
    chmod +x "$PROFILE_DIR/memory.sh"
    
    echo "✓ Created $PROFILE workspace at: $PROFILE_DIR"
    echo "  - API Port: $PORT"
    echo "  - Database: $PROFILE_DIR/memories/$DB_NAME"
    echo ""
}

# Create both workspaces
create_workspace "personal" 8091 "personal_memories.db"
create_workspace "work" 8092 "work_memories.db"

# Create convenience aliases script
cat > "$HOME/.ums_aliases" << 'EOF'
# Universal Memory System Aliases
alias ums-personal="$HOME/.ums-personal/start.sh"
alias ums-work="$HOME/.ums-work/start.sh"
alias mem-personal="$HOME/.ums-personal/memory.sh"
alias mem-work="$HOME/.ums-work/memory.sh"

# Quick capture functions
capture-personal() {
    echo "$*" | $HOME/.ums-personal/memory.sh store --category "quick_capture" --tags "personal"
}

capture-work() {
    echo "$*" | $HOME/.ums-work/memory.sh store --category "quick_capture" --tags "work"
}

# Show which workspace is active
ums-status() {
    echo "Universal Memory System Status:"
    if lsof -i:8091 > /dev/null 2>&1; then
        echo "  ✓ Personal workspace running on port 8091"
    else
        echo "  ✗ Personal workspace not running"
    fi
    
    if lsof -i:8092 > /dev/null 2>&1; then
        echo "  ✓ Work workspace running on port 8092"
    else
        echo "  ✗ Work workspace not running"
    fi
}
EOF

echo "Setup Complete!"
echo "=============="
echo ""
echo "Two separate workspaces have been created:"
echo ""
echo "1. PERSONAL WORKSPACE (~/.ums-personal/)"
echo "   - Start server: ums-personal"
echo "   - CLI access: mem-personal <command>"
echo "   - API port: 8091"
echo "   - Quick capture: capture-personal \"your note here\""
echo ""
echo "2. WORK WORKSPACE (~/.ums-work/)"
echo "   - Start server: ums-work"
echo "   - CLI access: mem-work <command>"
echo "   - API port: 8092"
echo "   - Quick capture: capture-work \"your note here\""
echo ""
echo "To enable aliases, add this to your shell profile:"
echo "  source ~/.ums_aliases"
echo ""
echo "Then you can use:"
echo "  ums-status       # Check which workspaces are running"
echo "  ums-personal     # Start personal workspace"
echo "  ums-work         # Start work workspace"
echo "  mem-personal list  # List personal memories"
echo "  mem-work list      # List work memories"