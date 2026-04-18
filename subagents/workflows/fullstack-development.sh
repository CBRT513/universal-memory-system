#!/bin/bash
# Workflow: fullstack-development
# Generated: 2025-08-17T03:20:33.078635
# This workflow chains multiple Claude Code SubAgents

set -e  # Exit on error

echo "Starting workflow: fullstack-development"

# Change to subagents directory
cd "/usr/local/share/universal-memory-system/subagents"


echo "Step 1: Running frontend-developer subagent..."
python3 cli/subagent_cli.py execute frontend-developer "${1:-Default task}"

if [ $? -ne 0 ]; then
    echo "Error: frontend-developer subagent failed"
    exit 1
fi

echo "Step 1 completed successfully"

echo "Step 2: Running backend-developer subagent..."
python3 cli/subagent_cli.py execute backend-developer "${1:-Default task}"

if [ $? -ne 0 ]; then
    echo "Error: backend-developer subagent failed"
    exit 1
fi

echo "Step 2 completed successfully"

echo "Step 3: Running api-developer subagent..."
python3 cli/subagent_cli.py execute api-developer "${1:-Default task}"

if [ $? -ne 0 ]; then
    echo "Error: api-developer subagent failed"
    exit 1
fi

echo "Step 3 completed successfully"

echo "Step 4: Running test-automation-engineer subagent..."
python3 cli/subagent_cli.py execute test-automation-engineer "${1:-Default task}"

if [ $? -ne 0 ]; then
    echo "Error: test-automation-engineer subagent failed"
    exit 1
fi

echo "Step 4 completed successfully"

echo "Workflow completed successfully!"
