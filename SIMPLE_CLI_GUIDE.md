# 🖥️ Simple CLI Guide - Universal AI Memory System

## Overview

The Simple CLI (`memory_cli_simple.py`) is a **zero-dependency** command-line interface for the Universal AI Memory System. It works without any external Python packages - no click, rich, or numpy required!

## Why Use Simple CLI?

- **No dependencies** - Works with vanilla Python 3
- **Always works** - No pip install failures
- **Full functionality** - All core features available
- **Clean output** - Simple, readable formatting

## Installation

None required! Just use it:

```bash
cd /Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system
python3 src/memory_cli_simple.py --help
```

## Commands

### Add a Memory

```bash
# Basic
python3 src/memory_cli_simple.py add "Your memory content here"

# With tags and importance
python3 src/memory_cli_simple.py add "Important Python decorator pattern" \
  --tags python,decorators,patterns \
  --importance 8 \
  --project myproject

# With category
python3 src/memory_cli_simple.py add "Fixed the authentication bug" \
  --category solution \
  --tags auth,bugfix \
  --importance 9
```

### Search Memories

```bash
# Basic search
python3 src/memory_cli_simple.py search "React hooks"

# Limit results
python3 src/memory_cli_simple.py search "authentication" --limit 5

# Filter by project
python3 src/memory_cli_simple.py search "database" --project backend
```

### List Recent Memories

```bash
# Default (10 most recent)
python3 src/memory_cli_simple.py list

# Specific number
python3 src/memory_cli_simple.py list --limit 20
```

### Get Statistics

```bash
python3 src/memory_cli_simple.py stats
```

Shows:
- Total memories and projects
- Memory distribution by project
- Category breakdown
- Top tags
- Vector search status

### Ask Questions

```bash
# Get context from memories
python3 src/memory_cli_simple.py ask "What do I know about authentication?"

python3 src/memory_cli_simple.py ask "How did I fix the Swift permission issues?"
```

## Examples

### Daily Workflow

```bash
# Morning: Check what you were working on
python3 src/memory_cli_simple.py list --limit 5

# During work: Store insights
python3 src/memory_cli_simple.py add "useState hook causes re-render on every call without dependencies" \
  --tags react,hooks,performance --importance 7

# Problem solving: Search for similar issues
python3 src/memory_cli_simple.py search "re-render performance"

# End of day: Store solution
python3 src/memory_cli_simple.py add "Fixed re-render issue by memoizing component with React.memo" \
  --category solution --tags react,optimization --importance 9
```

### Quick Memory Capture

```bash
# Alias for quick access (add to ~/.zshrc or ~/.bashrc)
alias mem="python3 /Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/src/memory_cli_simple.py"

# Then use:
mem add "Quick thought about the architecture"
mem search "database optimization"
mem list
mem stats
```

### Integration with Other Tools

```bash
# Pipe output from other commands
echo "Important command: docker run -p 8080:80 nginx" | xargs -I {} mem add "{}" --tags docker,commands

# Save error messages
python3 myapp.py 2>&1 | grep Error | xargs -I {} mem add "Error encountered: {}" --tags errors,debugging

# Capture git commit messages
git log --oneline -1 | xargs -I {} mem add "Commit: {}" --tags git,commits
```

## Output Format

### Add Command
```
✅ Memory stored successfully!
   ID: mem_1754921741999_6267
   Project: myproject
   Tags: python, testing
```

### Search Results
```
📚 Found 3 memories:

1. [backend] Fixed authentication by implementing JWT tokens...
   Tags: auth, jwt, security
   Importance: ⭐⭐⭐⭐⭐⭐⭐⭐
   Created: 2024-01-11 10:30

2. [frontend] React authentication hook using context API...
   Tags: react, auth, hooks
   Importance: ⭐⭐⭐⭐⭐⭐
   Created: 2024-01-10 15:45
```

### Statistics
```
📊 Memory System Statistics

Total Memories: 71
Total Projects: 3
Vector Search: ❌ Disabled

📁 Projects:
   • backend: 35 memories
   • frontend: 25 memories
   • docs: 11 memories

🏷️  Top Tags:
   • python: 15 uses
   • react: 12 uses
   • bugfix: 8 uses
```

## Tips & Tricks

### 1. Quick Capture
Use minimal commands for speed:
```bash
mem add "Quick thought"  # Minimal - uses defaults
```

### 2. Consistent Tagging
Develop a personal tagging system:
- Languages: `python`, `javascript`, `swift`
- Types: `bugfix`, `feature`, `optimization`
- Status: `todo`, `in-progress`, `solved`

### 3. Importance Levels
- 1-3: Minor notes
- 4-6: Useful information
- 7-8: Important patterns
- 9-10: Critical solutions

### 4. Project Organization
Use consistent project names:
```bash
mem add "Memory 1" --project my-app
mem add "Memory 2" --project my-app  # Same project
mem search "database" --project my-app  # Filter by project
```

## Troubleshooting

### No Results Found
- Search is case-insensitive but exact word matching
- Try shorter search terms
- Use `list` to see recent memories

### Performance
- Simple CLI loads all memories into memory
- For 1000+ memories, initial load may take 1-2 seconds
- Subsequent operations are fast

### Unicode/Emoji Issues
- Terminal must support UTF-8
- If emojis don't display, the functionality still works

## Advantages Over Full CLI

| Feature | Simple CLI | Full CLI (click) |
|---------|-----------|------------------|
| Dependencies | None | click, rich, numpy |
| Installation | Nothing | pip install required |
| Speed | Fast | Slightly faster |
| Output | Simple text | Rich formatting |
| Colors | Basic | Full color support |
| Works offline | ✅ Always | ❌ Needs packages |

## Summary

The Simple CLI provides **full memory system access** without any external dependencies. It's perfect for:
- Quick memory capture
- Systems without pip/npm
- Minimal environments
- Scripting and automation
- When other tools break

Just Python 3 and you're ready to build your Encyclopedia Galactica! 🚀