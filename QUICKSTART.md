# Universal AI Memory - Quick Start Guide

🚀 **Get up and running in 5 minutes!**

## 1. Install Everything Automatically

```bash
# Navigate to the system directory
cd universal-memory-system

# Run the automated installer
python setup.py
```

**What this does:**
- ✅ Creates Python environment with all dependencies
- ✅ Configures local storage and vector search
- ✅ Installs global `memory` CLI command  
- ✅ Sets up web GUI and browser integration
- ✅ Configures auto-start services
- ✅ Runs verification tests

**Takes about 2-3 minutes on a typical Mac mini.**

## 2. Start the Services

```bash
# Start memory service and web GUI
./scripts/start-services.sh
```

**You should see:**
```
🧠 Starting Universal AI Memory System...
🚀 Starting Memory Service...
🎨 Starting Librarian GUI...
✅ Services started!
📊 Memory API: http://localhost:8091/docs
🎨 Librarian GUI: http://localhost:8092/
```

## 3. Store Your First Memory

### Via CLI (Recommended)
```bash
# Store a solution you discovered
memory remember "Use React.memo for expensive components that don't change often" --tags react,performance --importance 8

# Store a working system (protected from changes)
memory remember "JWT authentication working perfectly for 6 months" --status working --protection high
```

### Via Web GUI
1. Open http://localhost:8092/
2. Chat with the librarian: "Remember that CSS Grid is better than Flexbox for 2D layouts"
3. The system auto-categorizes and stores it

## 4. Search Your Memories

```bash
# Semantic search (finds by meaning)
memory search "React optimization"

# Filter by project and tags
memory search --project myapp --tags performance

# Quick recall
memory recall "authentication"
```

## 5. Get Context for AI Conversations

```bash
# Generate context for ChatGPT (copies to clipboard)
memory ai-context --question "How to optimize database queries?" --ai chatgpt --copy

# Get general context
memory context --relevant-to "React performance issues" --copy
```

**Then paste into any AI chat!**

## 6. Browser Integration

1. **Open browser integration:** `open static/browser_integration.html`
2. **Drag bookmarklet** to your bookmark bar
3. **Use on any AI website** (ChatGPT, Claude, etc.)
4. **Select interesting text** → Click bookmarklet → Save to memory

## 7. Daily Workflow

### Morning Routine
```bash
# Get context for today's work
memory context --project current-project --copy
# Paste into AI: "Here's context from my previous work: [paste]"
```

### During Development
```bash
# Store solutions as you discover them
memory remember "Fixed CORS by adding credentials: true to server headers" --tags cors,fix

# Store decisions
memory remember "Decided to use PostgreSQL over MongoDB for better relational data" --category decision
```

### Evening Review
```bash
# Check what you learned today
memory search --tags $(date +%Y-%m-%d)

# See system status
memory stats
```

## Common Commands

| Task | Command |
|------|---------|
| Store memory | `memory remember "your insight" --tags tag1,tag2` |
| Search | `memory search "database optimization"` |
| Get AI context | `memory ai-context --question "your question" --copy` |
| View stats | `memory stats` |
| Check health | `memory doctor` |
| Start services | `./scripts/start-services.sh` |
| Stop services | `./scripts/stop-services.sh` |

## Troubleshooting

**Memory command not found:**
```bash
# Restart your shell
source ~/.bashrc  # or ~/.zshrc
```

**Services won't start:**
```bash
# Check what's using the ports
lsof -i :8091
lsof -i :8092

# Kill any conflicts
pkill -f memory_service
pkill -f librarian_gui
```

**Browser bookmarklet fails:**
```bash
# Make sure services are running
curl http://localhost:8091/api/health
```

**Need help:**
```bash
# Run diagnostics
memory doctor

# Check logs
tail -f ~/.ai-memory/logs/memory_service.log
```

## Next Steps

1. **Customize settings:** Edit `~/.ai-memory/config.json`
2. **Explore web GUI:** Visit http://localhost:8092/ for chat interface
3. **Check API docs:** Visit http://localhost:8091/docs for technical details
4. **Read full docs:** See README.md for advanced features

## Key Concepts

- **Memories** = Insights, solutions, decisions you want to remember
- **Context** = Relevant background generated for AI conversations  
- **Protection** = Mark working systems to prevent regression
- **Projects** = Auto-detected from git repositories or directories
- **Semantic search** = Find by meaning, not just keywords

---

🧠 **You're now ready to never lose AI context again!**

Start storing memories and watch how much more effective your AI conversations become.