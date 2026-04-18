#!/bin/bash

echo "Setting up Seamless Workspace Switching..."
echo "=========================================="
echo ""

# Make all scripts executable
chmod +x /usr/local/share/universal-memory-system/switch
chmod +x /usr/local/share/universal-memory-system/ums
chmod +x /usr/local/share/universal-memory-system/workspace_manager.py
chmod +x /usr/local/share/universal-memory-system/workspace_config.py
chmod +x /usr/local/share/universal-memory-system/apply_workspace_patch.py

# Apply patches to make all tools workspace-aware
echo "Making all tools workspace-aware..."
python3 /usr/local/share/universal-memory-system/apply_workspace_patch.py

# Create global aliases
cat >> ~/.zshrc << 'EOF'

# Universal Memory System - Seamless Workspaces
export PATH="/usr/local/share/universal-memory-system:$PATH"

# Quick switch between workspaces
alias work='echo "work" > ~/.ums-current-workspace && export UMS_WORKSPACE=work && echo "💼 Switched to work workspace (port 8092)"'
alias personal='echo "personal" > ~/.ums-current-workspace && export UMS_WORKSPACE=personal && echo "🏠 Switched to personal workspace (port 8091)"'

# All commands work the same, just use different data
alias mem='python3 /usr/local/share/universal-memory-system/src/memory_cli.py'
alias subagent='python3 /usr/local/share/universal-memory-system/subagents/cli/subagent_cli.py'

# Quick status check
workspace() {
    if [ -f ~/.ums-current-workspace ]; then
        current=$(cat ~/.ums-current-workspace)
    else
        current="personal"
    fi
    
    if [ "$current" = "work" ]; then
        echo "💼 Current workspace: work (port 8092)"
    else
        echo "🏠 Current workspace: personal (port 8091)"
    fi
}

# Start the current workspace's API
ums-start() {
    workspace
    python3 /usr/local/share/universal-memory-system/src/api_service.py &
}

# Initialize with personal workspace
if [ ! -f ~/.ums-current-workspace ]; then
    echo "personal" > ~/.ums-current-workspace
fi
EOF

echo ""
echo "✅ Setup Complete!"
echo ""
echo "HOW IT WORKS:"
echo "============="
echo ""
echo "1. SWITCH WORKSPACES (instant, no restart needed):"
echo "   work        # Switch to work workspace"
echo "   personal    # Switch to personal workspace"
echo "   workspace   # Check current workspace"
echo ""
echo "2. ALL COMMANDS STAY THE SAME:"
echo "   mem list                     # Lists from current workspace"
echo "   mem store 'Some note'        # Stores to current workspace"
echo "   subagent list               # Works with current workspace"
echo "   python3 src/memory_cli.py    # Auto-detects workspace"
echo ""
echo "3. DATA IS COMPLETELY SEPARATE:"
echo "   Personal: ~/.ums-personal/memories/personal_memories.db"
echo "   Work: ~/.ums-work/memories/work_memories.db"
echo ""
echo "4. BOTH CAN RUN SIMULTANEOUSLY:"
echo "   Personal API: http://localhost:8091"
echo "   Work API: http://localhost:8092"
echo ""
echo "To activate, run: source ~/.zshrc"
echo "Then just type 'work' or 'personal' to switch!"