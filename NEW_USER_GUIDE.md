# 🧠 Universal Memory System (UMS)
## Your AI-Powered External Brain for Everything You Read, Write, and Learn

---

## What Is This?

The **Universal Memory System (UMS)** is like having a photographic memory for your digital life. It automatically captures, organizes, and makes searchable everything you work with on your Mac - from code snippets to articles, terminal commands to web content.

Think of it as:
- 🔮 **A search engine for your personal knowledge** - Find that command you used 3 months ago
- 📚 **An automatic knowledge base** - Never lose track of important information
- 🤖 **AI-powered content understanding** - Automatically categorizes and scores content by importance
- ⏰ **A time machine for your work** - Remember exactly what you were working on and when

## What Will It Do For You?

### 🎯 **Never Lose Information Again**
- Automatically captures text you copy or select
- Stores terminal commands and their outputs
- Saves code snippets with context about when/where you used them
- Archives articles and documentation you read

### 🔍 **Instant Knowledge Retrieval**
- Search across ALL your captured memories with one query
- Find that Stack Overflow solution you saw months ago
- Retrieve that perfect code example you once wrote
- Access commands you ran in terminal last year

### 📊 **Intelligent Organization**
- AI automatically categorizes content (articles, code, notes, solutions)
- Scores content by "actionability" - what needs your attention
- Tags memories with relevant topics and technologies
- Links related information together

### 🚀 **Boost Your Productivity**
- Stop wasting time searching through browser history
- Never lose track of useful commands or configurations
- Build a personal knowledge base that grows with you
- Learn from your past solutions and decisions

---

## How to Install (5 Minutes)

### Prerequisites
- macOS (10.15 or later)
- Python 3 installed
- Admin access to your Mac

### Installation Steps

1. **Download the UMS Package**
   ```bash
   # Your admin will provide you with the installation package
   # It will be a .tar.gz file containing all necessary files
   ```

2. **Extract and Install**
   ```bash
   # Extract the package
   tar -xzf universal-memory-system.tar.gz
   
   # Navigate to the directory
   cd universal-memory-system
   
   # Run the clean installation script
   ./install_clean_ums.sh
   ```

3. **Grant Permissions**
   - When prompted, grant Accessibility permissions for Global Capture
   - Go to: System Preferences → Security & Privacy → Privacy → Accessibility
   - Add and check "UniversalMemoryCapture"

4. **Start UMS**
   ```bash
   ~/start_ums.sh
   ```
   
   The dashboard will automatically open in your browser!

---

## How to Use It

### 🔥 **Quick Start - Three Ways to Capture**

#### 1. Global Capture Hotkey (⌘⇧M)
- Select any text in any application
- Press `⌘⇧M` (Command+Shift+M)
- A capture window appears - add tags and importance
- Click "Save" - it's now in your memory system forever!

#### 2. Automatic Clipboard Monitoring (Optional)
- Anything you copy (⌘C) can be automatically captured
- Enable in Global Capture menu bar settings
- Great for passive knowledge collection

#### 3. Browser Extension
- Capture entire web pages or selected content
- Automatically extracts article text and metadata
- Perfect for research and documentation

### 📊 **The Dashboard - Your Memory Command Center**

Open http://localhost:8091/dashboard to access:

#### Universal Search
- **Search everything** you've ever captured
- **Sort by**: Relevance, Date, or Importance
- **See metadata**: Source app, date captured, tags, importance score

#### Action Plans
- View articles and content marked as "actionable"
- See what needs implementation or follow-up
- Track your learning progress

#### Memory Management
- Add memories manually
- Edit tags and importance
- Export your knowledge base

### 🎯 **Power User Tips**

#### Smart Searching
```
# Search for specific project memories
project:myapp database

# Search by date range
python async "last week"

# Search by importance
docker compose importance:high
```

#### Tagging Strategy
- Use project names as tags
- Add technology tags (python, react, docker)
- Tag by action needed (todo, reference, learning)

#### Memory Types
- **Articles**: Long-form content automatically analyzed by AI
- **Code Snippets**: Programming examples and solutions
- **Commands**: Terminal commands and configurations
- **Notes**: Quick thoughts and ideas
- **Solutions**: Fixes and workarounds you've discovered

---

## Real-World Use Cases

### 👨‍💻 **For Developers**
- Capture error messages and their solutions
- Store useful code snippets from Stack Overflow
- Remember complex terminal commands
- Track configuration changes across projects
- Build a personal library of coding patterns

### 📚 **For Researchers**
- Capture important passages from articles
- Store references with automatic source tracking
- Build topic-specific knowledge bases
- Track evolving understanding of subjects

### 🎨 **For Designers**
- Capture design inspiration and references
- Store color schemes and typography choices
- Remember client feedback and requirements
- Track design decisions and rationale

### 📈 **For Product Managers**
- Capture user feedback and feature requests
- Store competitive analysis findings
- Track product decisions and their context
- Build a knowledge base of industry insights

---

## Daily Workflow Integration

### Morning Routine
1. Start UMS: `~/start_ums.sh`
2. Dashboard opens automatically
3. Check Action Plans for today's priorities

### During Work
- Press ⌘⇧M whenever you find something useful
- Let clipboard monitoring capture your research
- Search the dashboard when you need to recall something

### End of Day
- Review what was captured today
- Tag important items for future reference
- Export weekly backup (optional)

---

## Troubleshooting

### System Not Starting?
```bash
# Check if already running
ps aux | grep api_service

# Check logs
tail -f ~/.ai-memory/ums.log

# Restart fresh
~/stop_ums.sh
~/start_ums.sh
```

### Global Capture Not Working?
1. Check Accessibility permissions
2. Restart the capture app from menu bar
3. Run: `~/start_ums.sh` again

### Search Not Finding Results?
- Check if Ollama is installed for semantic search
- Verify memories are being stored: Check dashboard stats
- Try simpler search terms

---

## Privacy & Security

### 🔒 **Your Data Stays Local**
- All memories stored locally on YOUR Mac
- No cloud services or external servers
- Complete control over your data
- Export anytime, delete anytime

### 🛡️ **Security Features**
- Memories are indexed locally
- Optional encryption for sensitive data
- No telemetry or usage tracking
- Open source and auditable

---

## Complete Uninstallation

### 🗑️ **Need to Remove UMS?**

We understand that not every tool is right for everyone. If you need to uninstall UMS for any reason, we've made it completely reversible.

### **One-Command Uninstall**
```bash
~/uninstall_ums.sh
```

### **What the Uninstaller Does:**

#### ✅ **Complete Removal**
- Stops all running UMS processes
- Removes Global Capture app and permissions
- Deletes all configuration files
- Cleans up system directories
- Removes launch agents and autostart items
- Clears accessibility permissions
- Removes all temporary files and caches

#### 💾 **Automatic Backup**
Before removing anything, the uninstaller:
- Creates a complete backup on your Desktop
- Exports your memories to readable text format
- Preserves your database for potential recovery
- Saves all configuration files

#### 📁 **Backup Location**
`~/Desktop/UMS_FINAL_BACKUP_[timestamp]/`
- `memories.db` - Your complete database (can be restored)
- `exported_memories.txt` - Human-readable memory list
- Configuration files for reference

### **After Uninstallation**
- Your Mac is returned to its pre-UMS state
- No background processes remain
- No system modifications persist
- Your backup remains on Desktop (delete when ready)

### **Reinstalling Later**
If you change your mind:
1. Use the original installation package
2. Optionally restore your old database from backup

---

## Getting Help

### Resources
- **Dashboard**: http://localhost:8091/dashboard
- **API Documentation**: http://localhost:8091/docs
- **Logs**: `~/.ai-memory/ums.log`

### Quick Commands
```bash
# Start UMS
~/start_ums.sh

# Stop UMS
~/stop_ums.sh

# Check health
curl http://localhost:8091/api/health

# View recent memories
curl http://localhost:8091/api/memory/search?q=recent&limit=5
```

---

## Tips for Success

### 🎯 **First Week Goals**
1. Capture at least 10 memories per day
2. Try all three capture methods
3. Search for something you captured yesterday
4. Set up your tagging system
5. Export your first backup

### 📈 **Building Your Knowledge Base**
- Be liberal with capturing - you can always filter later
- Tag consistently for better organization
- Review and rate importance weekly
- Use the Action Plans dashboard for follow-ups

### 💡 **Advanced Features to Explore**
- Article triage system for long-form content
- Relevance scoring for search results
- Project-based memory filtering
- Custom importance scoring

---

## Welcome to Your New Superpower! 🚀

The Universal Memory System is your personal AI assistant that never forgets. It learns from everything you do, helping you become more productive and knowledgeable over time.

**Start capturing memories today, and in a month, you'll wonder how you ever lived without it!**

---

*Questions? Issues? Your administrator can help, or check the dashboard for built-in help and documentation.*