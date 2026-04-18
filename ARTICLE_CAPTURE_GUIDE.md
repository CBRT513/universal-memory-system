# 📰 Article Capture Guide - Global Capture (⌘⇧M)

## Overview
The Global Capture app (`⌘⇧M`) provides a specialized article capture interface that integrates with the Universal Memory System's Article Triage feature. This allows you to capture, classify, and evaluate articles directly from any application on macOS.

## How to Capture Articles

### Step 1: Select Article Text
Select the article content in any application:
- Web browser (Chrome, Safari, Firefox, etc.)
- PDF reader
- Text editor
- Email client
- Any text-selectable application

### Step 2: Press ⌘⇧M
Press `Cmd+Shift+M` to open the capture dialog.

### Step 3: Article Capture Interface
The capture dialog will display with the following elements:

#### 📰 Article Checkbox (Top)
- **Checked by default** for article capture
- When checked: Shows article-specific options
- When unchecked: Shows regular memory capture options

#### Article Type Dropdown (When Article is Checked)
Select the article classification:
- **🚀 Actionable** - Needs implementation (highest priority)
- **📚 Reference** - Keep for documentation
- **🎓 Learning** - Educational content
- **🔍 Research** - Needs further investigation

#### Tags Field
Add comma-separated tags to categorize the article:
- Example: `react, hooks, performance, tutorial`
- Helps with later retrieval and organization

#### Importance Slider (1-10)
Rate the article's importance:
- 1-3: Low priority
- 4-6: Medium priority  
- 7-9: High priority
- 10: Critical/Must implement

#### Text Preview
- Shows the captured article text
- Editable if you need to clean up or add notes
- Scrollable for long articles

### Step 4: Store the Article
Click "Store Memory" to:
1. Send the article to the Article Triage system
2. Get AI analysis of actionability and relevance
3. Extract key action items
4. Store in the memory system with full metadata

## Article Triage Processing

When you capture an article, the system automatically:

### 1. Content Analysis
- Detects if the content is an article
- Analyzes structure and technical content
- Extracts key technologies and concepts

### 2. Classification
Articles are classified into categories:
- **implement_now** - Contains actionable code/solutions
- **reference** - Valuable documentation to keep
- **monitor** - Worth tracking for updates
- **archive** - Store but low priority

### 3. Scoring
- **Actionability Score (0-10)**: How immediately useful
- **Relevance Score (0-10)**: How relevant to your projects

### 4. Action Item Extraction
- Identifies specific implementation steps
- Extracts code patterns
- Lists technologies to research

## Viewing Captured Articles

### Via CLI
```bash
# List all actionable articles
python3 /usr/local/share/universal-memory-system/src/memory_cli.py article actionable

# Get statistics
python3 /usr/local/share/universal-memory-system/src/memory_cli.py article stats

# Search articles
python3 /usr/local/share/universal-memory-system/src/memory_cli.py search "react hooks"
```

### Via API Dashboard
Open http://localhost:8091/dashboard to:
- Browse all captured articles
- Filter by classification
- Sort by actionability score
- View extracted action items

## Troubleshooting

### ⌘⇧M Not Working
1. Check Accessibility permissions:
   - System Settings → Privacy & Security → Accessibility
   - Ensure "Universal Memory Capture" is enabled
2. Restart the app:
   ```bash
   pkill -f 'Universal Memory Capture' && open '/Applications/Universal Memory Capture.app'
   ```

### Article Interface Not Showing
1. The interface should show:
   - Article checkbox at the top
   - Article type dropdown when checked
   - Tags field
   - Importance slider
2. If missing, rebuild the app:
   ```bash
   cd /usr/local/share/universal-memory-system/global-capture
   ./build.sh && cd build && ./install.sh
   ```

### Article Not Being Processed
1. Ensure Memory API is running:
   ```bash
   curl http://localhost:8091/api/health
   ```
2. Check Ollama is installed and running:
   ```bash
   ollama list  # Should show phi3:mini or similar
   ```

## Tips for Effective Article Capture

### 1. Select Complete Content
- Include the full article text
- Don't worry about headers/footers - they'll be filtered

### 2. Use Descriptive Tags
- Add technology tags: `react, typescript, nextjs`
- Add concept tags: `performance, optimization, hooks`
- Add project tags: `my-app, frontend, backend`

### 3. Set Accurate Importance
- Rate based on immediate need
- Higher scores appear first in actionable lists

### 4. Choose Correct Article Type
- **Actionable**: Has code/steps you'll implement
- **Reference**: Documentation you'll refer back to
- **Learning**: Educational, not immediately actionable
- **Research**: Needs more investigation

## Integration with Memory System

Captured articles are:
- Stored in the Universal Memory System
- Searchable via semantic search
- Tagged and categorized automatically
- Available to all AI agents for context
- Linked to related memories

## Keyboard Shortcuts

- **⌘⇧M**: Open capture dialog (global)
- **Tab**: Navigate between fields
- **Enter**: Store memory
- **Esc**: Cancel capture

## Menu Bar Features

Click the 🧠 icon in the menu bar to:
- View recent captures
- Check Memory Service status
- Copy AI context
- Access settings
- Force resync with API

---

*Last Updated: 2025-08-19*
*Part of the Universal AI Memory System (Encyclopedia Galactica)*