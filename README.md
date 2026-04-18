# Universal AI Memory System

🧠 **Never lose context again!** A complete, production-ready system for maintaining persistent memory across all your AI interactions and projects.

## Overview

The Universal AI Memory System is designed for **non-programmers** who want reliable, local AI memory without complexity. It provides:

- **Local-only storage** - Your data never leaves your machine
- **Works with any AI** - ChatGPT, Claude, Bard, local models
- **Multiple interfaces** - CLI, web GUI, browser integration
- **Zero maintenance** - Automated setup, self-healing, backups
- **Anti-regression protection** - Prevents losing working solutions

## Quick Start

### 1. Automatic Installation

```bash
# Clone or download the system
cd universal-memory-system

# Run automated setup (handles everything)
python setup.py
```

The setup will:
- ✅ Create Python environment with all dependencies
- ✅ Configure memory storage and vector search  
- ✅ Install global `memory` CLI command
- ✅ Setup web librarian GUI
- ✅ Create browser bookmarklet
- ✅ Configure auto-start services
- ✅ Run comprehensive verification tests

### 2. Start Using

```bash
# Store your first memory
memory remember "Use React.memo for expensive components" --tags react,performance --importance 8

# Search your memories  
memory search "React optimization"

# Get context for AI chat (copies to clipboard)
memory context --relevant-to "React performance issues" --copy

# Open web interface
open http://localhost:8092
```

## Core Features

### 🧠 Intelligent Memory Storage

- **Smart categorization** - Automatically categorizes as solution, pattern, decision, etc.
- **Auto-tagging** - Extracts relevant technical tags from content
- **Importance scoring** - Estimates significance based on content analysis
- **Deduplication** - Prevents storing the same insight twice
- **Project detection** - Auto-detects current project from git/directory

### 🔍 Advanced Search

- **Semantic search** - Find memories by meaning, not just keywords
- **Vector similarity** - Uses AI embeddings for intelligent matching  
- **Full-text search** - Traditional keyword search as fallback
- **Filtered search** - By project, category, tags, importance
- **Cross-project search** - Find related solutions from other projects

### 🎯 Context Generation

- **AI-ready context** - Generates perfect prompts for ChatGPT, Claude, etc.
- **Token-aware** - Respects AI platform limits (4K, 8K, 32K tokens)
- **Protection-aware** - Highlights working systems to prevent changes
- **Progressive disclosure** - Summary first, details on demand
- **Cross-project insights** - Includes relevant solutions from other work

### 🛡️ Anti-Regression Protection

```bash
# Mark working systems as protected
memory remember "JWT authentication working perfectly for 6 months" --status working --protection critical

# Context generation will show:
# "PROTECTED WORKING SYSTEMS (do not modify):
# ✅ JWT authentication working perfectly for 6 months"
```

## Usage Examples

### Daily Development Workflow

```bash
# Morning: Get context for current work
memory context --project myapp --copy
# Paste into ChatGPT: "Here's context from my previous work: [context]"

# During development: Store solutions
memory remember "Fixed CORS by adding credentials: true to server config" --tags cors,server

# End of day: Store decisions  
memory remember "Decided to use PostgreSQL over MongoDB for better SQL support" --category decision --protection high

# Before changing working systems: Check what's protected
memory search --status working --project myapp
```

### AI Platform Integration

**ChatGPT:**
```bash
memory ai-context --question "How to optimize database queries?" --ai chatgpt --copy
# Generates: "I'm working on a project with relevant context: [memories]... Current question: How to optimize database queries?"
```

**Claude:**
```bash
memory ai-context --question "React performance issues" --ai claude --copy
# Generates: "I have relevant experience from previous work: [memories]... Please help with: React performance issues"
```

**Browser Integration:**
1. Start memory service: `./scripts/start-services.sh`
2. Open browser integration: `open static/browser_integration.html`  
3. Drag bookmarklet to bookmark bar
4. Use on any AI website to capture insights

### Team Collaboration

```bash
# Share knowledge base
memory export --format markdown --project myapp --output team-knowledge.md

# Onboard new team member
memory export --category decision --format chatgpt > architectural-decisions.txt

# Document patterns for reuse
memory search --category pattern --project myapp --format markdown
```

## Architecture

### Local-First Design

```
~/.ai-memory/                    # All data stored locally
├── memories.db                  # SQLite with FTS search
├── vectors/                     # Vector embeddings for semantic search
│   ├── embeddings.bin          # HNSW index file
│   └── metadata.json           # Index configuration
├── backups/                    # Automated daily backups
├── exports/                    # User-generated exports
├── logs/                       # Service logs
└── config.json                 # System configuration
```

### Component Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Tool      │    │  Web GUI        │    │ Browser Plugin  │
│   (memory cmd)  │    │  (localhost:    │    │ (bookmarklet)   │
│                 │    │   8092)         │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────────┐
                    │      REST API Service       │
                    │     (localhost:8091)        │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │     Memory Engine           │
                    │  • Semantic Search          │
                    │  • Context Generation       │
                    │  • Anti-regression Logic    │
                    └─────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐    ┌───────────▼────────┐    ┌──────────▼─────────┐
│  SQLite DB     │    │   Vector Index     │    │  File System       │
│  • Metadata    │    │   • HNSW Search    │    │  • Exports         │
│  • FTS Search  │    │   • Embeddings     │    │  • Backups         │
│  • Relations   │    │   • Similarity     │    │  • Configuration   │
└────────────────┘    └────────────────────┘    └────────────────────┘
```

### Embedding Providers

The system supports multiple embedding providers with automatic fallback:

1. **Sentence Transformers** (default) - Local, no internet required
2. **Ollama** - Local LLM server with embedding models  
3. **OpenAI** - High quality, requires API key
4. **Cohere** - Alternative cloud provider

## Service Management

### Starting Services

```bash
# Start all services
./scripts/start-services.sh

# Or individually
memory server --start              # Memory API
python src/librarian_gui.py       # Web GUI
```

### Stopping Services

```bash
# Stop all services  
./scripts/stop-services.sh

# Or individually
memory server --stop
pkill -f librarian_gui.py
```

### Status Check

```bash
# Check service status
./scripts/status.sh

# Or via CLI
memory server --status

# Or via web
curl http://localhost:8091/api/health
```

### Auto-Start (macOS)

The system automatically configures macOS launchd for auto-start:

```bash
# Services start automatically on login
# Disable with:
launchctl unload ~/Library/LaunchAgents/com.universalai.memory.plist

# Re-enable with:  
launchctl load ~/Library/LaunchAgents/com.universalai.memory.plist
```

## Configuration

### System Configuration: `~/.ai-memory/config.json`

```json
{
  "storage_path": "/Users/username/.ai-memory",
  "api_port": 8091,
  "gui_port": 8092,
  "embedding_provider": "sentence-transformers",
  "embedding_model": "all-MiniLM-L6-v2",
  "vector_search_enabled": true,
  "auto_backup": true,
  "backup_interval_hours": 24,
  "max_storage_size_gb": 10,
  "log_level": "INFO"
}
```

### Environment Variables

```bash
export MEMORY_HOME="/path/to/universal-memory-system"
export MEMORY_API_URL="http://localhost:8091"
export EMBEDDING_PROVIDER="sentence-transformers"  # or ollama, openai
export OPENAI_API_KEY="sk-..."  # if using OpenAI embeddings
```

### CLI Configuration: `~/.ai-memory/cli_config.json`

```json
{
  "default_importance": 5,
  "max_search_results": 10,
  "auto_copy_context": true,
  "rich_output": true,
  "project_detection": true
}
```

## Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check port usage
lsof -i :8091
lsof -i :8092

# Kill existing processes
pkill -f memory_service
pkill -f librarian_gui

# Restart
./scripts/start-services.sh
```

**Memory command not found:**
```bash
# Check PATH
echo $PATH | grep .local/bin

# If missing, add to shell config:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Vector search not working:**
```bash
# Check embedding provider
memory doctor

# Install additional dependencies
pip install sentence-transformers hnswlib

# Or use Ollama
brew install ollama
ollama pull nomic-embed-text
export EMBEDDING_PROVIDER=ollama
```

**Browser bookmarklet fails:**
```bash
# Ensure services are running
curl http://localhost:8091/api/health

# Check browser console for errors
# Common issue: CORS - already configured for localhost
```

### Diagnostics

```bash
# Run comprehensive diagnostics
memory doctor

# Check system statistics  
memory stats

# View service logs
tail -f ~/.ai-memory/logs/memory_service.log
tail -f ~/.ai-memory/logs/gui_service.log
```

### Performance Issues

```bash
# Clean up old memories
memory cleanup --old --days 180 --dry-run
memory cleanup --duplicates --unused --access-threshold 0

# Create backup before cleanup
memory backup

# Optimize database
sqlite3 ~/.ai-memory/memories.db "VACUUM; REINDEX;"
```

### Data Recovery

```bash
# List available backups
ls ~/.ai-memory/backups/

# Restore from backup
cp ~/.ai-memory/backups/memory_backup_20240101_120000.db ~/.ai-memory/memories.db

# Export all data as JSON
memory export --format json --output full-backup.json

# Re-import data (if needed)
# Currently requires manual SQL import
```

## API Reference

### Core Endpoints

```bash
# Health check
GET /api/health

# Store memory
POST /api/memory/store
{
  "content": "Solution text",
  "tags": ["tag1", "tag2"],
  "importance": 8,
  "status": "working",
  "protection_level": "high"
}

# Search memories
GET /api/memory/search?q=query&project=myapp&limit=10
POST /api/memory/search
{
  "query": "search term",
  "project": "myapp",
  "category": "solution",
  "limit": 10
}

# Generate context
POST /api/memory/context
{
  "relevant_to": "database optimization",
  "project": "myapp",
  "max_tokens": 4000
}

# Get statistics
GET /api/memory/stats

# Export data
GET /api/memory/export?format=markdown&project=myapp
```

### AI Integration Helpers

```bash
# Generate AI prompt with context
GET /ai/prompt?question=How%20to%20optimize%20React&ai_platform=chatgpt

# Find related memories
POST /api/memory/relate
{
  "content": "React performance optimization",
  "limit": 10,
  "cross_project": true
}
```

## Security & Privacy

### Local-First Architecture

- **No cloud dependencies** - Everything runs locally
- **No telemetry** - No data collection or reporting  
- **No network access required** - Works completely offline
- **User data control** - You own all your data
- **Open source** - Transparent, auditable code

### Data Protection

- **Local storage only** - Data never transmitted externally
- **Configurable retention** - Auto-delete old memories
- **Secure deletion** - Proper cleanup of sensitive data
- **Access control** - Only accessible via localhost
- **Backup encryption** - Optional encrypted backups

### Best Practices

```bash
# Regular backups
memory backup --destination ~/secure-backups/

# Clean up sensitive data
memory search "password\|secret\|key" --format json
# Review and delete manually if needed

# Limit memory retention
memory cleanup --old --days 365

# Monitor storage usage
memory stats | grep storage
```

## Advanced Usage

### Custom Workflows

**Git Integration:**
```bash
# Auto-remember commit messages
echo 'memory remember "$(git log -1 --pretty=%B)" --category decision --project $(basename $(pwd)) --tags git,commit' > .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

**IDE Integration (VS Code):**
```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Remember Solution",
      "type": "shell",
      "command": "memory",
      "args": ["remember", "${input:solution}", "--project", "${workspaceFolderBasename}"]
    }
  ]
}
```

**Automated Context Generation:**
```bash
# Create alias for quick context
alias aicontext='memory context --relevant-to "$1" --copy && echo "Context copied! Paste into AI chat."'

# Usage: aicontext "database optimization"
```

### Scaling for Teams

```bash
# Export team knowledge
memory export --format markdown --output team-wiki.md

# Share decisions across team
memory search --category decision --format chatgpt > team-decisions.txt

# Create project templates
memory search --category pattern --project template --format markdown
```

### Integration with External Tools

**Obsidian Vault:**
```bash
# Export as markdown files for Obsidian
memory export --format markdown --project myapp --output ~/ObsidianVault/AI-Memories/myapp.md
```

**Notion Database:**
```bash
# Export as JSON for import to Notion
memory export --format json | jq '.[] | {Title: .content, Tags: (.tags | join(", ")), Importance: .importance}'
```

## Development

### Project Structure

```
universal-memory-system/
├── setup.py                    # Automated installation script
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── src/                        # Core system code
│   ├── memory_service.py       # Core memory engine
│   ├── memory_cli.py           # Command-line interface  
│   ├── librarian_gui.py        # Web GUI service
│   └── api_service.py          # REST API service
├── static/                     # Browser integration files
│   ├── browser_capture.js      # Bookmarklet code
│   └── browser_integration.html # Setup instructions
├── templates/                  # HTML templates
│   └── librarian.html          # Web GUI template
├── scripts/                    # Service management (generated)
│   ├── start-services.sh       # Start all services
│   ├── stop-services.sh        # Stop all services
│   └── status.sh               # Check service status
└── tests/                      # Test files (if added)
```

### Testing

```bash
# Manual testing
memory remember "Test memory" --tags test
memory search "test"
memory context --relevant-to "testing"
memory doctor

# API testing
curl -X POST http://localhost:8091/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{"content":"Test via API","tags":["api","test"]}'

# Browser testing
open static/browser_integration.html
# Click "Test Bookmarklet" button
```

## FAQ

**Q: Does this work offline?**
A: Yes! With sentence-transformers (default), everything works offline. Only Ollama model downloads or OpenAI API calls require internet.

**Q: How much storage does it use?**
A: ~1KB per memory + ~4KB per embedding. 10,000 memories ≈ 50MB total.

**Q: Can I use my own AI models?**  
A: Yes! Install Ollama and use any embedding model. The system auto-detects available providers.

**Q: Is my data secure?**
A: Completely. Everything runs locally, no cloud services, no telemetry, no network access required.

**Q: Can I share memories with my team?**
A: Export/import via JSON or markdown. Shared storage support planned for future versions.

**Q: What if I have problems?**
A: Run `memory doctor` for diagnostics. Check logs in `~/.ai-memory/logs/`. The system is designed to be self-healing.

## Changelog

### v1.0.1 - Critical Bug Fixes
- 🔧 **Fixed vector search synchronization**: Memories stored via web interface are now immediately searchable
- 🔧 **Fixed statistics display**: "Show me system statistics" now correctly displays system stats instead of help text
- 🔧 **Fixed SQLite Row access**: Resolved AttributeError in search result processing
- 🔧 **Improved hybrid search**: Better fallback from vector to FTS search when needed
- ✅ **Enhanced pattern matching**: Statistics requests now have higher priority in librarian agent

### v1.0.0 - Initial Release
- ✅ Core memory storage with SQLite + vector search
- ✅ Command-line interface with rich output  
- ✅ Web-based librarian GUI with chat interface
- ✅ Browser bookmarklet for all AI platforms
- ✅ Automated setup for Mac mini deployment
- ✅ Anti-regression protection for working systems  
- ✅ Service management with auto-start
- ✅ Comprehensive documentation and troubleshooting

### Planned Features
- [ ] Team collaboration features
- [ ] Mobile app for iOS/Android  
- [ ] Advanced analytics and insights
- [ ] Plugin system for extensibility
- [ ] Cloud sync option (encrypted)
- [ ] Voice capture integration

---

🧠 **Universal AI Memory System** - Your AI conversations, never forgotten.