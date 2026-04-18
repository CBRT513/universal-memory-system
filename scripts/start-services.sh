#!/bin/bash
# Universal AI Memory System - Service Starter

echo "🧠 Starting Universal AI Memory System..."

# Check if already running
if curl -s http://localhost:8091/api/health > /dev/null 2>&1; then
    echo "⚠️  Memory service already running on port 8091"
else
    echo "🚀 Starting Memory Service..."
    cd "/Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/src"
    "/Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/venv/bin/python" -m uvicorn memory_service:app --host 127.0.0.1 --port 8091 > "/Users/cerion/.ai-memory/logs/memory_service.log" 2>&1 &
    echo $! > "/Users/cerion/.ai-memory/memory_service.pid"
    sleep 2
fi

if curl -s http://localhost:8092/ > /dev/null 2>&1; then
    echo "⚠️  GUI service already running on port 8092"
else
    echo "🎨 Starting Librarian GUI..."
    cd "/Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/src"
    "/Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/venv/bin/python" librarian_gui.py --host 127.0.0.1 --port 8092 > "/Users/cerion/.ai-memory/logs/gui_service.log" 2>&1 &
    echo $! > "/Users/cerion/.ai-memory/gui_service.pid"
    sleep 2
fi

echo "✅ Services started!"
echo "📊 Memory API: http://localhost:8091/docs"
echo "🎨 Librarian GUI: http://localhost:8092/"
echo "🌐 Browser Integration: file:///Users/cerion/.ai-memory/browser/integration.html"
