#!/bin/bash
# Universal AI Memory System - Status Check

echo "🔍 Universal AI Memory System Status"
echo "=================================="

# Check Memory Service
if curl -s http://localhost:8091/api/health > /dev/null 2>&1; then
    echo "✅ Memory Service: Running (http://localhost:8091)"
else
    echo "❌ Memory Service: Not running"
fi

# Check GUI Service
if curl -s http://localhost:8092/ > /dev/null 2>&1; then
    echo "✅ Librarian GUI: Running (http://localhost:8092)"
else
    echo "❌ Librarian GUI: Not running"
fi

# Check CLI
if command -v memory > /dev/null 2>&1; then
    echo "✅ CLI Command: Available"
else
    echo "❌ CLI Command: Not found (restart shell or source config)"
fi

# Check storage
if [ -d "/Users/cerion/.ai-memory" ]; then
    echo "✅ Storage Directory: /Users/cerion/.ai-memory"
    echo "   $(du -sh "/Users/cerion/.ai-memory" | cut -f1) used"
else
    echo "❌ Storage Directory: Not found"
fi
