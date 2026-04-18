#!/bin/bash

# Store Article Triage System Documentation in Memory System
# This script documents the system changes in the memory system itself

echo "📚 Storing Article Triage System documentation in memory..."

# Check if API is running
if ! curl -s http://localhost:8091/api/health > /dev/null 2>&1; then
    echo "⚠️  Starting Memory API service..."
    python3 src/api_service.py --port 8091 &
    sleep 5
fi

# Store main documentation
echo "📝 Storing main article triage documentation..."
curl -X POST http://localhost:8091/api/article/triage \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "content": "$(cat ARTICLE_TRIAGE_DOCUMENTATION.md | jq -Rs .)",
  "project": "universal-memory",
  "tags": ["documentation", "article_triage", "system_architecture", "api", "cli"],
  "source": "documentation",
  "metadata": {
    "component": "article_triage",
    "version": "1.0.0",
    "type": "complete_documentation",
    "created_by": "Claude Code",
    "created_date": "2025-08-13"
  }
}
EOF

echo ""
echo "📝 Storing implementation change log..."
curl -X POST http://localhost:8091/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Article Triage System Implementation - Version 1.0.0\n\nImplemented intelligent article detection and triage system for Universal Memory System.\n\nChanges:\n1. Created article_triage.py with ArticleDetector, OllamaArticleAnalyzer, and ArticleTriageService\n2. Extended api_service.py with 5 new endpoints for article operations\n3. Modified memory store endpoint to auto-detect and triage articles\n4. Added CLI commands: article analyze, triage, actionable, stats\n5. Created article_metadata database table\n6. Integrated Ollama models (phi3:mini, llama3.2:3b) for local analysis\n\nBenefits:\n- Zero API costs (uses local Ollama)\n- Automatic article classification (implement_now, reference, monitor, archive)\n- Actionability and relevance scoring\n- Technology and topic extraction\n- Action item identification\n\nTesting:\n- Created comprehensive test suite (test_article_triage.py)\n- All components tested and verified working",
    "category": "change_log",
    "tags": ["implementation", "article_triage", "v1.0.0", "enhancement"],
    "importance": 9,
    "metadata": {
      "component": "article_triage",
      "files_modified": [
        "src/article_triage.py",
        "src/api_service.py",
        "src/memory_cli.py"
      ],
      "files_created": [
        "src/article_triage.py",
        "test_article_triage.py",
        "ARTICLE_TRIAGE_DOCUMENTATION.md"
      ]
    }
  }'

echo ""
echo "📝 Storing API documentation..."
curl -X POST http://localhost:8091/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Article Triage API Endpoints\n\nNew endpoints added to Universal Memory System:\n\n1. POST /api/article/analyze - Analyze article without storing\n2. POST /api/article/triage - Triage and store with intelligence\n3. GET /api/article/actionable - Get high-priority articles\n4. GET /api/article/stats - Article statistics\n5. POST /api/article/extract - Extract action items from stored article\n\nAuto-triage in /api/memory/store:\n- Automatically detects articles >500 chars\n- Runs Ollama analysis if detected\n- Enhances metadata with insights\n- Can be disabled with metadata.auto_triage=false",
    "category": "api_documentation",
    "tags": ["api", "endpoints", "article_triage"],
    "importance": 8,
    "metadata": {
      "endpoints": [
        "/api/article/analyze",
        "/api/article/triage",
        "/api/article/actionable",
        "/api/article/stats",
        "/api/article/extract"
      ]
    }
  }'

echo ""
echo "📝 Storing CLI documentation..."
curl -X POST http://localhost:8091/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Article CLI Commands\n\nNew commands added to memory CLI:\n\nmemory article analyze [content] - Analyze without storing\n  --file FILE - Read from file\n  --url URL - Fetch from URL\n  --quick - Quick analysis mode\n\nmemory article triage [content] - Triage and store article\n  --file FILE - Read from file\n  --url URL - Fetch from URL\n  --project PROJECT - Assign to project\n  --tags TAGS - Add tags (comma-separated)\n\nmemory article actionable - List high-priority articles\n  --limit N - Number to show\n\nmemory article stats - Show article statistics",
    "category": "cli_documentation",
    "tags": ["cli", "commands", "article_triage"],
    "importance": 7,
    "metadata": {
      "commands": [
        "article analyze",
        "article triage",
        "article actionable",
        "article stats"
      ]
    }
  }'

echo ""
echo "📝 Storing configuration documentation..."
curl -X POST http://localhost:8091/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Article Triage Configuration\n\nEnvironment Variables:\n- OLLAMA_URL: Ollama service URL (default: http://localhost:11434)\n- OLLAMA_ARTICLE_MODEL: Model for analysis (phi3:mini, llama3.2:3b, mistral:7b)\n- OLLAMA_TIMEOUT: Request timeout in seconds (default: 30)\n- ARTICLE_CACHE_HOURS: Cache TTL (default: 24)\n- AUTO_TRIAGE_ENABLED: Enable auto-triage in memory store (default: true)\n- AUTO_TRIAGE_MIN_LENGTH: Minimum content length for auto-triage (default: 500)\n\nRequired Ollama Models:\n- phi3:mini (2GB) - Fast classification\n- llama3.2:3b (2GB) - Better analysis\n- mistral:7b (4GB) - Optional, best quality",
    "category": "configuration",
    "tags": ["config", "environment", "article_triage", "ollama"],
    "importance": 7,
    "metadata": {
      "environment_vars": [
        "OLLAMA_URL",
        "OLLAMA_ARTICLE_MODEL",
        "OLLAMA_TIMEOUT",
        "ARTICLE_CACHE_HOURS",
        "AUTO_TRIAGE_ENABLED",
        "AUTO_TRIAGE_MIN_LENGTH"
      ],
      "required_models": ["phi3:mini", "llama3.2:3b"]
    }
  }'

echo ""
echo "✅ Documentation stored in memory system!"
echo ""
echo "View stored documentation:"
echo "  python3 src/memory_cli.py search --tags documentation,article_triage"
echo ""
echo "View article statistics:"
echo "  python3 src/memory_cli.py article stats"