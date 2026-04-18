# Universal AI Memory System - Complete Quick Start Guide

## 🚀 One-Command Setup

Get your complete Universal AI Memory System running in under 5 minutes:

```bash
# 1. Start the core memory service
cd src && python3 api_service.py --host 0.0.0.0 --port 8091 &

# 2. Start the web interface
cd web-interface && python3 -m http.server 8092 &

# 3. Install browser extension (Chrome/Edge)
# Load unpacked extension from: browser-extension/

# 4. Build and install Global Capture (macOS)
cd global-capture && ./build.sh && cd build && ./install.sh
```

## 🎯 Core System Components

### 1. Memory API Service (localhost:8091)
**What it does**: Core memory storage, search, and AI integration
**Status check**: `curl localhost:8091/api/health`
**Features**:
- ✅ Vector similarity search with HNSW
- ✅ SQLite FTS5 full-text search  
- ✅ Smart categorization and tagging
- ✅ Cross-project context generation
- ✅ GitHub repository integration
- ✅ Natural language processing
- ✅ Export/import capabilities
- ✅ Anti-regression protection

### 2. Web Dashboard (localhost:8092)
**What it does**: Web-based GUI for memory management and search
**Access**: Open `http://localhost:8092` in your browser
**Features**:
- 🔍 Advanced search interface
- 📊 Memory statistics and analytics
- 🏷️ Tag and category management
- 📈 Usage trends and insights
- ⚙️ System configuration
- 📤 Export and backup tools

### 3. Browser Extension (AI Platform Integration)
**What it does**: Captures insights from ChatGPT, Claude, Perplexity, etc.
**Install**: Load unpacked extension from `browser-extension/`
**Features**:
- 🤖 Auto-detects AI responses on major platforms
- 🎯 One-click capture with smart categorization
- 📝 Quick notes and context tagging
- 🔄 Real-time sync with memory system
- ⚡ Popup interface for instant access

### 4. Global Capture Service (macOS System-Wide)
**What it does**: Captures from any macOS application
**Install**: Run `global-capture/build.sh` then `build/install.sh`
**Features**:
- ⌨️ Global hotkey (⌘⇧M) for instant capture
- 📋 Smart clipboard monitoring
- 🖼️ OCR screenshot text extraction
- 🧠 Context-aware project detection
- 📱 Menu bar interface and controls

### 5. Command Line Interface
**What it does**: Terminal-based memory management
**Usage**: `python3 src/memory_cli.py [command]`
**Features**:
- 💬 Natural language queries
- 📚 GitHub repository integration
- 🔧 System maintenance and cleanup
- 📊 Statistics and health monitoring
- 🔄 Backup and restore operations

## 🎮 Usage Examples

### Quick Memory Storage
```bash
# CLI method
echo "JWT tokens expire after 1 hour in production" | python3 src/memory_cli.py store --category security

# API method  
curl -X POST localhost:8091/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{"content": "Use React.memo for expensive component renders", "category": "optimization"}'
```

### Smart Search
```bash
# Natural language CLI
python3 src/memory_cli.py "How do I optimize React components?"

# Web dashboard
# Open http://localhost:8092 and search naturally

# API search
curl "localhost:8091/api/memory/search?q=JWT+tokens&include_semantic=true"
```

### Global Capture Workflow
1. **Select text anywhere in macOS** (Xcode, Terminal, browser, etc.)
2. **Press ⌘⇧M** (Cmd+Shift+M)
3. **Text automatically captured** with full context
4. **Smart categorization** based on app and content
5. **Instant availability** in all interfaces

### Browser Extension Workflow  
1. **Visit ChatGPT, Claude, or Perplexity**
2. **AI response appears** with auto-detection
3. **Click capture button** or use selection capture
4. **Content intelligently categorized** and tagged
5. **Synced to your memory system** immediately

## 🔧 Configuration & Customization

### Memory Service Configuration
Edit `src/memory_service.py` for:
- **Embedding provider**: Ollama, Sentence Transformers, OpenAI
- **Vector dimensions**: Adjust for your embedding model
- **Database path**: Change storage location
- **Search parameters**: Tune relevance thresholds

### Web Interface Customization  
Edit `web-interface/index.html` for:
- **UI themes and styling**
- **Search result formatting**
- **Statistics display options**
- **Dashboard layout preferences**

### Global Capture Settings
Menu bar → Settings for:
- **Hotkey configuration** (currently ⌘⇧M)  
- **Clipboard monitoring** toggle
- **Content filtering** sensitivity
- **Excluded applications** list
- **OCR enablement** for screenshots

### Browser Extension Settings
Extension popup → Settings for:
- **Auto-detection** preferences
- **Platform-specific** capture rules
- **Notification** settings
- **Smart tagging** configuration

## 🔒 Security & Privacy

### Local-First Architecture
- **All data stays on your machine**
- **No cloud dependencies** (except optional OpenAI embeddings)
- **Local SQLite database** with FTS5 search
- **Local vector index** with HNSW
- **Local web server** (no external access)

### Smart Content Filtering
- **Automatic detection** of passwords, API keys, tokens
- **Configurable sensitivity** levels
- **Manual exclusion** patterns
- **App-specific filtering** rules

### Permission Requirements
- **macOS Global Capture**: Accessibility access for text selection
- **Browser Extension**: Active tab access for AI platform integration
- **No network permissions** beyond localhost communication

## 📊 System Monitoring

### Health Checks
```bash
# Memory service status
curl localhost:8091/api/health

# Web interface status  
curl localhost:8092

# Global Capture status (macOS)
ps aux | grep "Universal Memory Capture"

# Database statistics
python3 src/memory_cli.py stats
```

### Performance Monitoring
```bash
# Memory usage
python3 src/memory_cli.py "Show me system statistics"

# Recent captures
python3 src/memory_cli.py "What have I captured recently?"

# Storage usage
du -sh ~/.universal_memory/

# Vector index health
python3 src/memory_cli.py "Check vector index status"
```

## 🔄 Backup & Restore

### Automatic Backups
```bash
# Manual backup
python3 src/memory_cli.py backup ~/memory-backup-$(date +%Y%m%d).db

# Scheduled backup (add to crontab)
0 2 * * * cd /path/to/universal-memory-system && python3 src/memory_cli.py backup
```

### Restore Process
```bash
# Restore from backup
python3 src/memory_cli.py restore ~/memory-backup-20240810.db

# Verify restoration
python3 src/memory_cli.py stats
```

## 🧠 Advanced Features

### GitHub Integration
```bash
# Initialize repository analysis
python3 src/memory_cli.py github init

# Sync repository knowledge
python3 src/memory_cli.py github sync

# Query repository context
python3 src/memory_cli.py "What's the architecture of this project?"
```

### Cross-Project Context
```bash
# Generate context for current work
python3 src/memory_cli.py "Generate context for debugging React performance"

# Cross-project insights
curl -X POST localhost:8091/api/memory/context \
  -H "Content-Type: application/json" \
  -d '{"relevant_to": "database optimization", "include_cross_project": true}'
```

### Natural Language Processing
```bash
# Intent-based queries
python3 src/memory_cli.py "Summarize my memories about API design"
python3 src/memory_cli.py "Show me all solutions for authentication issues"
python3 src/memory_cli.py "What configuration files have I worked with?"
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Memory Service Won't Start
```bash
# Check for port conflicts
lsof -i :8091

# Check Python dependencies
pip3 install -r requirements.txt

# Check database permissions
chmod 644 ~/.universal_memory/memory.db
```

#### Global Capture Not Working
1. **Grant Accessibility permissions**: System Preferences → Security & Privacy → Accessibility
2. **Check for conflicts**: Other global hotkey apps
3. **Verify installation**: Look for brain icon in menu bar
4. **Check logs**: Console app → "Universal Memory Capture"

#### Browser Extension Issues
1. **Reload extension**: Chrome → Extensions → Developer mode → Reload
2. **Check permissions**: Extension should have access to AI platform sites
3. **Verify connection**: Extension popup should show "Connected" status
4. **Check console**: F12 → Console for error messages

#### Search Not Finding Results
```bash
# Check database integrity
python3 src/memory_cli.py "Check system health"

# Rebuild vector index
python3 src/memory_cli.py rebuild-index

# Verify FTS5 search
python3 src/memory_cli.py "Test search functionality"
```

## 🔮 Upcoming Features

### In Development
- **Mobile app integration** (iOS shortcuts)
- **Slack/Teams integration** for team knowledge sharing
- **Advanced OCR** with formula and diagram recognition
- **Voice memo capture** with transcription
- **Smart scheduling** (don't capture during presentations)

### Community Requests
- **Custom hotkey configuration**
- **Integration with more AI platforms**
- **Enhanced project detection**
- **Team collaboration features**
- **Enterprise security enhancements**

---

## 🎯 Quick Success Checklist

- [ ] ✅ Memory API service running on localhost:8091
- [ ] ✅ Web dashboard accessible at localhost:8092  
- [ ] ✅ Browser extension loaded and connected
- [ ] ✅ Global Capture installed with brain icon in menu bar
- [ ] ✅ Accessibility permissions granted (macOS)
- [ ] ✅ Test capture: Select text → Press ⌘⇧M → Verify in dashboard
- [ ] ✅ Test browser: Visit ChatGPT → Capture AI response → Check memory
- [ ] ✅ Test search: Use natural language queries in CLI/web
- [ ] ✅ GitHub integration: Run `python3 src/memory_cli.py github init`
- [ ] ✅ Backup configured: Set up automatic database backups

**🧠 Your Universal AI Memory System is now ready! Never lose context again.**