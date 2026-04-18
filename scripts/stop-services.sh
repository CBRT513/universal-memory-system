#!/bin/bash
# Universal AI Memory System - Service Stopper

echo "🛑 Stopping Universal AI Memory System..."

# Stop services using PID files
for service in memory_service gui_service; do
    pid_file="/Users/cerion/.ai-memory/${service}.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service (PID: $pid)..."
            kill "$pid"
            rm "$pid_file"
        else
            echo "$service not running"
            rm -f "$pid_file"
        fi
    fi
done

# Fallback: kill by port
pkill -f "memory_service"
pkill -f "librarian_gui"

echo "✅ Services stopped"
