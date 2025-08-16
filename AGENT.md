# Universal AI Memory System

A comprehensive memory system that captures, processes, and retrieves information from multiple sources including global text capture, browser extensions, GitHub integration, and direct API access. This system serves as an "encyclopedia galactica" for AI agents and development tools.

## Project Overview

The Universal AI Memory System consists of:
- **Memory Core API** (`src/`) - FastAPI-based memory storage and retrieval
- **Global Capture macOS App** (`global-capture/`) - System-wide text capture with ⌘⇧M hotkey
- **Browser Extensions** (`browser-extension/`) - Web page content capture
- **GitHub Integration** (`github-integration/`) - Repository and code analysis
- **CLI Interface** (`src/memory_cli.py`) - Command-line memory management
- **Dashboard** - Web-based memory visualization and management

## Build & Commands

### Memory System Core
- Start memory service: `python3 src/api_service.py --port 8091`
- Run CLI interface: `python3 src/memory_cli.py <command>`
- Install dependencies: `pip3 install -r requirements.txt`
- Check system health: `curl http://localhost:8091/api/health`
- View system stats: `python3 src/memory_cli.py stats`
- **Generate AI Context**: `python3 src/ai_context_generator.py --copy` (copies to clipboard)

### Global Capture (macOS)
- Build: `cd global-capture && ./build.sh`
- Install: `cd global-capture/build && ./install.sh`
- Debug permissions: `cd global-capture && ./force-enable-debug.sh`
- Test permissions: `cd global-capture && swift permission-test.swift`
- Quick fix: `cd global-capture && ./quick-fix-test.sh`
- **AI Context Copy**: Click 🤖 "Copy AI Context" in menu bar for ready-to-paste AI messages

### Browser Extensions
- Build Chrome extension: `cd browser-extension && npm run build:chrome`
- Build Firefox extension: `cd browser-extension && npm run build:firefox`
- Development: `cd browser-extension && npm run dev`

### Development Environment
- Memory API: http://localhost:8091
- Dashboard: http://localhost:8091/dashboard
- API Documentation: http://localhost:8091/docs
- Health Check: http://localhost:8091/api/health

## Code Style & Conventions

### Python (Memory Core)
- Use Python 3.8+ with type hints
- FastAPI for API endpoints with automatic OpenAPI generation
- Pydantic for data validation and serialization
- SQLAlchemy for database operations
- pytest for testing
- Black for code formatting
- Follow PEP 8 naming conventions
- Use descriptive function/variable names
- Document API endpoints with proper docstrings

### Swift (Global Capture)
- Use Swift 5+ with explicit type annotations
- Follow Apple's Swift API Design Guidelines
- Use NSStatusItem for menu bar integration
- ApplicationServices framework for accessibility permissions
- Proper memory management with weak references
- Comprehensive error handling and logging
- Use `print()` for debug output with descriptive prefixes

### JavaScript/TypeScript (Browser Extensions)
- ES6+ with TypeScript preferred
- Use consistent naming: camelCase for variables, PascalCase for classes
- Manifest V3 for Chrome extensions
- WebExtensions API for cross-browser compatibility
- Error handling with try-catch blocks
- Use descriptive variable names

### File Management Best Practices

#### Backup File Protocol
- **NEVER create backup files in working directories**: No `*.backup`, `*.bak`, `*.old`, `*.orig` files alongside source code
- **Dedicated Backup Directory**: All backup files MUST be placed in `.backups/` directory at project root
  - Use `.backups/` (with dot prefix) to automatically hide from most tools and IDEs
  - Create directory structure: `.backups/YYYY-MM-DD/` for daily organization
- **Backup Naming Convention**: 
  - Format: `.backups/YYYY-MM-DD/[relative-path]/[filename].[HHMMSS].backup`
  - Example: `.backups/2025-08-14/src/components/DataImportManager.jsx.143022.backup`
  - Preserves directory structure for easy restoration
- **Automatic Cleanup Policy**:
  - Keep maximum 5 versions per file
  - Remove backups older than 7 days
  - Exception: Keep at least 1 backup per file regardless of age
- **Version Control Priority**: 
  - Always prefer Git for version history
  - Use backups ONLY for immediate rollback safety during risky operations
  - Commit to Git before making significant changes
- **Temporary Files**:
  - Use `.tmp/` directory at project root (dot prefix for hiding)
  - Never create temp files in source directories
  - Clean up temp files after each session

#### Why This Matters
- **Build Tool Compatibility**: Prevents Vite, Webpack, Next.js, etc. from processing backup files
- **IDE Performance**: Stops IDEs from indexing backup files
- **Clean Git Status**: Backup directories can be gitignored with single rule
- **Universal Application**: Works across all languages, frameworks, and build systems
- **Easy Recovery**: Organized structure makes finding backups simple

#### Implementation Example
```bash
# Creating a backup (DO THIS)
mkdir -p .backups/$(date +%Y-%m-%d)/src/components/
cp src/components/Component.jsx .backups/$(date +%Y-%m-%d)/src/components/Component.jsx.$(date +%H%M%S).backup

# Creating a backup (DON'T DO THIS)
cp src/components/Component.jsx src/components/Component.jsx.backup  # ❌ WRONG
cp src/components/Component.jsx Component.jsx.old                      # ❌ WRONG
```

#### Gitignore Rule
Add to `.gitignore`:
```
.backups/
.tmp/
```

## Memory System Architecture

### Core Components
```
┌─────────────────────────────────────────────────────────────┐
│                    UNIVERSAL MEMORY SYSTEM                  │
├─────────────────────────────────────────────────────────────┤
│  Global Capture ──┐    Browser Ext ──┐    GitHub API ──┐   │
│       (⌘⇧M)       │        (JS)      │     (Python)    │   │
│                   ▼                  ▼                 ▼   │
│              ┌─────────────────────────────────────────────┐│
│              │         Memory Core API (FastAPI)          ││
│              │  • Storage & Retrieval                     ││
│              │  • Semantic Search                         ││
│              │  • Tag Management                          ││
│              │  • Importance Scoring                      ││
│              └─────────────────────────────────────────────┘│
│                              │                             │
│                              ▼                             │
│              ┌─────────────────────────────────────────────┐│
│              │      CLI Interface & Dashboard              ││
│              │  • Query memories                          ││
│              │  • System statistics                       ││
│              │  • Memory management                       ││
│              └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Capture**: Text/content captured via multiple sources
2. **Processing**: Content analyzed, tagged, and importance scored
3. **Storage**: Memories stored with metadata and embeddings
4. **Retrieval**: Semantic search and filtering capabilities
5. **Integration**: AI agents query memories for context

## Memory Usage & Integration

### For AI Coding Agents
```python
# Query project-specific memories
memories = query_memory("How do I build the Global Capture app?")

# Get context for current task
context = get_memories_by_tags(["build", "swift", "global-capture"])

# Store agent learnings
store_memory("Fixed permission detection issue in Global Capture", 
            tags=["fix", "permissions", "swift"], importance=8)
```

### Global Capture Integration
- **⌘⇧M hotkey** captures selected text from any macOS application
- **Automatic context detection** includes app name and timestamp
- **Rich capture dialog** with editable tags and importance scoring
- **Menu bar integration** with live status indicators
- **Clipboard monitoring** (optional) for passive content capture

### API Endpoints for Agents
- `GET /api/memories` - Retrieve all memories with filtering
- `POST /api/memories` - Store new memory
- `GET /api/search?q={query}` - Semantic search
- `GET /api/stats` - System statistics
- `GET /api/tags` - Available tags
- `GET /api/health` - System health check

## Testing Guidelines

### Memory Core Testing
- Unit tests: `pytest src/tests/`
- API tests: `pytest src/tests/test_api.py`
- Integration tests: Test full capture-to-retrieval flow
- Mock external dependencies (AI services, databases)
- Test error conditions and edge cases

### Global Capture Testing
- Permission detection: `swift global-capture/permission-test.swift`
- Hotkey registration: Manual testing with ⌘⇧M
- Menu functionality: Test all menu items
- Memory integration: Verify captures reach memory system

### ⚠️ CRITICAL: Global Capture Keyboard Handling
**NEVER use NSEvent monitors for global hotkeys!** This causes severe keyboard interference.

#### The Problem (Discovered 2025-08-14)
Using `NSEvent.addGlobalMonitorForEvents(matching: .keyDown)` intercepts ALL keyboard events system-wide, causing:
- Colored focus rings appearing randomly
- Keyboard input interference
- Focus stealing from applications
- Performance degradation

#### The Solution
Always use Carbon's HotKey API:
```swift
// ✅ CORRECT - Only responds to specific hotkey
RegisterEventHotKey(keyCode, modifiers, hotkeyID, target, 0, &hotkeyRef)

// ❌ WRONG - Intercepts ALL keyboard events
NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { ... }
```

See `global-capture/CRITICAL_DO_NOT_USE_EVENT_MONITORS.md` for full details.

### Browser Extension Testing
- Test across Chrome, Firefox, Safari
- Verify content extraction accuracy
- Test popup interface functionality
- Check memory system integration

## Security Considerations

### Sensitive Data Handling
- **Never store passwords, API keys, or secrets** in memories
- **Filter sensitive content** before storage (credit cards, SSNs, etc.)
- **Local storage only** - no external data transmission without consent
- **Accessibility permissions** properly requested and validated

### macOS Security
- **Proper entitlements** in Info.plist for system access
- **Accessibility permission validation** with user guidance
- **Sandbox compliance** for App Store distribution
- **Code signing** for trusted execution

### API Security
- **Input validation** on all endpoints
- **Rate limiting** to prevent abuse
- **CORS configuration** for browser extension access
- **Local network only** (localhost:8091)

## Configuration & Environment

### Environment Variables
```bash
# Memory System Configuration
export MEMORY_API_PORT=8091
export MEMORY_DB_PATH="./memories.db"
export MEMORY_ENABLE_DEBUG=true

# AI Integration
export OPENAI_API_KEY="your-key-here"  # Optional: for enhanced search
export ANTHROPIC_API_KEY="your-key-here"  # Optional: for content analysis
```

### System Configuration

#### Sudo Timeout Configuration
For development environments where frequent sudo commands are needed, you can extend the sudo password timeout to reduce authentication prompts:

```bash
# Extend sudo timeout to 60 minutes for specific user
echo "Defaults:username timestamp_timeout=60" | sudo tee /etc/sudoers.d/username-timeout
sudo chmod 440 /etc/sudoers.d/username-timeout

# Verify configuration
sudo visudo -c

# Example for multiple users
echo "Defaults:cerion timestamp_timeout=60" | sudo tee /etc/sudoers.d/cerion-timeout
echo "Defaults:Equillabs timestamp_timeout=60" | sudo tee /etc/sudoers.d/equillabs-timeout
sudo chmod 440 /etc/sudoers.d/*-timeout
```

**Note**: The default sudo timeout is 5 minutes. Setting it to 60 minutes is useful for development but should be used cautiously in production environments.

### Global Capture Configuration
- **Hotkey**: ⌘⇧M (Cmd+Shift+M) - customizable
- **Memory API Base**: http://localhost:8091
- **Clipboard Monitoring**: Disabled by default
- **Auto-tagging**: Enabled with context detection

## AI Agent Integration Patterns

### Context-Aware Development
```python
# Before making code changes
context = memory_system.get_context(
    current_file="global-capture/main.swift",
    task="fix permission detection",
    max_memories=10
)

# After successful changes
memory_system.store_learning(
    content="Permission detection fixed by forcing status to true",
    context={"file": "main.swift", "line": 170},
    tags=["fix", "permissions", "swift"],
    importance=9
)
```

### Knowledge Persistence
- **Code patterns**: Store successful implementation patterns
- **Bug fixes**: Document solutions for future reference
- **Architecture decisions**: Capture design rationale
- **Learning outcomes**: Store insights from debugging sessions

## Migration & Compatibility

### From Legacy Systems
- Import from existing knowledge bases
- Migrate bookmark collections
- Convert notes and documentation
- Preserve tags and categorization

### Tool Compatibility
- **Claude Code**: Full integration via this AGENT.md
- **Cursor**: Access via API endpoints
- **GitHub Copilot**: Context injection through memories
- **Replit**: Memory system as knowledge base
- **Any AI Tool**: RESTful API for universal access

## Performance & Scaling

### Memory System Performance
- **Semantic search**: Sub-100ms response times
- **Storage**: SQLite for <100k memories, PostgreSQL for larger
- **Indexing**: Vector embeddings for semantic similarity
- **Caching**: In-memory cache for frequent queries

### Global Capture Performance
- **Hotkey latency**: <50ms response time
- **Memory integration**: Async storage to prevent UI blocking
- **Resource usage**: Minimal CPU/memory footprint
- **Battery impact**: Optimized for MacBook usage

## Troubleshooting

### Common Issues

#### Global Capture
- **Menu items grayed out**: Run `global-capture/force-enable-debug.sh`
- **Hotkey not working**: Check Accessibility permissions in System Preferences
- **Memory not storing**: Verify Memory API is running on port 8091

#### Memory System
- **API not responding**: Check `python3 src/api_service.py --port 8091`
- **Search not working**: Verify database permissions and disk space
- **Slow queries**: Check memory database size and indexing

#### Browser Extension
- **Not capturing**: Check extension permissions and API connection
- **Content missing**: Verify content extraction rules
- **Authentication**: Ensure memory API allows CORS requests

## Development Workflow

### Adding New Features
1. **Design**: Document in AGENT.md and memory system
2. **Implement**: Follow code style guidelines
3. **Test**: Unit tests + integration tests
4. **Document**: Update relevant documentation
5. **Deploy**: Build and test across all components

### Memory-Enhanced Development
1. **Query existing knowledge** before implementing
2. **Store solutions and patterns** during development
3. **Document decisions and rationale** in memories
4. **Build knowledge base** for future AI agents

## Documentation Standards

### Mandatory Documentation Requirement
**CRITICAL**: All changes, enhancements, and modifications to the Universal AI Memory System MUST be properly documented and stored within the system itself. This is non-negotiable.

### Self-Documenting System Protocol
The Universal Memory System (Encyclopedia Galactica) must document its own evolution. Every AI agent working on this system must:

1. **Capture System Changes**: Use the memory system to document all modifications
2. **Maintain Documentation Categories**: Store documentation in structured categories
3. **Follow Documentation Templates**: Use standardized formats for consistency
4. **Link Related Content**: Connect new documentation to existing memories

### Documentation Categories
All system documentation must be categorized as:
- `system_architecture` - Core system design and patterns
- `api_documentation` - Endpoint specifications and usage
- `cli_documentation` - Command reference and examples
- `configuration` - Setup procedures and environment requirements
- `change_log` - Historical record of all modifications
- `troubleshooting` - Known issues and solutions
- `article_triage` - Article analysis and classification system

### AI Agent Responsibilities
When working on this system, AI agents must:

1. **Document Before Implementation**: Create documentation memories before making changes
2. **Update Existing Documentation**: Modify relevant existing memories when changes affect them
3. **Provide Complete Context**: Include why, how, and what for all changes
4. **Include Usage Examples**: Provide concrete examples of new functionality
5. **Test Documentation**: Verify documentation accuracy before completion

### Documentation Commands
Use these commands to properly document changes:

```bash
# Document a system change
python3 src/memory_cli.py store \
  "Description of change and implementation details" \
  --category "system_change" \
  --tags "enhancement,api,v1.0.0" \
  --importance 8

# Document with article triage (for longer documentation)
python3 src/memory_cli.py article triage \
  --file DOCUMENTATION.md \
  --project "universal-memory" \
  --tags "documentation,system"

# Create linked documentation via API
curl -X POST http://localhost:8091/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "API endpoint documentation...",
    "category": "api_documentation",
    "tags": ["api", "endpoints", "article_triage"],
    "metadata": {
      "component": "article_triage",
      "version": "1.0.0",
      "related_files": ["article_triage.py", "api_service.py"]
    }
  }'
```

### Documentation Quality Requirements
All documentation must include:
- **Context**: Why the change was needed
- **Implementation**: Technical details and approach
- **Usage**: How to use the new functionality
- **Examples**: Concrete usage examples
- **Dependencies**: Requirements and prerequisites
- **Testing**: Verification procedures
- **Rollback**: How to revert if needed

### Compliance Verification
Before completing any work:
1. Verify all changes are documented in the memory system
2. Ensure documentation follows the required template
3. Confirm all related documentation is updated
4. Test documentation accuracy with actual usage

**Incomplete documentation = Incomplete implementation**

### Article Triage System Documentation
The Article Triage System added on 2025-08-13 includes:
- **Complete documentation**: `ARTICLE_TRIAGE_DOCUMENTATION.md`
- **Implementation files**: `src/article_triage.py`
- **API enhancements**: Extended `src/api_service.py`
- **CLI commands**: Extended `src/memory_cli.py`
- **Test suite**: `test_article_triage.py`
- **Partial article handling**: `partial_article_enhancement.md`

This system automatically detects, analyzes, and classifies articles using local Ollama models, providing intelligent triage without API costs.

---

*This Universal AI Memory System serves as a comprehensive knowledge base for AI agents, enabling them to understand project structure, access historical context, and contribute to the evolving encyclopedia galactica of development knowledge.*