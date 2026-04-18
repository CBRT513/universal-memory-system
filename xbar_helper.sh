#!/bin/bash
# UMS xbar helper script - handles commands from menu bar

UMS_DIR="/usr/local/share/universal-memory-system"
VENV_PYTHON="$UMS_DIR/venv/bin/python"
MEMORY_CLI="$UMS_DIR/memory_cli.sh"

case "$1" in
    "process-articles")
        cd "$UMS_DIR"
        "$VENV_PYTHON" src/mcp_article_integration.py
        ;;
    "run-crew")
        cd "$UMS_DIR"
        "$VENV_PYTHON" src/article_crew.py
        ;;
    "test-mcp")
        cd "$UMS_DIR"
        "$VENV_PYTHON" -c "import asyncio; from src.mcp_tools_bridge import MCPToolsBridge; bridge = MCPToolsBridge(); result = asyncio.run(bridge.test_connections()); import json; print(json.dumps(result, indent=2))"
        ;;
    "github-ops")
        cd "$UMS_DIR"
        "$VENV_PYTHON" src/mcp_tools_bridge.py
        ;;
    "capture-clipboard")
        pbpaste | "$MEMORY_CLI" store --category article --tags "to-review,from-clipboard"
        osascript -e 'display notification "Article captured from clipboard" with title "UMS"'
        ;;
    "ai-context")
        cd "$UMS_DIR"
        "$VENV_PYTHON" src/ai_context_generator.py | pbcopy
        osascript -e 'display notification "AI context copied to clipboard" with title "UMS"'
        ;;
    "memory-stats")
        "$MEMORY_CLI" stats
        ;;
    "start-ums")
        cd "$UMS_DIR"
        ./scripts/start-services.sh
        ;;
    "stop-ums")
        cd "$UMS_DIR"
        ./scripts/stop-services.sh
        ;;
    *)
        echo "Unknown command: $1"
        exit 1
        ;;
esac