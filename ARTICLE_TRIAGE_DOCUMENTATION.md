# 📚 Article Triage System - Complete Documentation

## System Overview

The Article Triage System is an intelligent content analysis and classification system integrated into the Universal AI Memory System. It automatically detects, analyzes, and categorizes articles using local Ollama models, providing actionable insights without any API costs.

## Table of Contents
1. [Architecture](#architecture)
2. [Installation & Setup](#installation--setup)
3. [Core Components](#core-components)
4. [API Documentation](#api-documentation)
5. [CLI Commands](#cli-commands)
6. [Usage Examples](#usage-examples)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Implementation Details](#implementation-details)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ARTICLE TRIAGE SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Content Input Sources:                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ ⌘⇧M     │ │   API   │ │   CLI   │ │ Browser │          │
│  │ Hotkey  │ │  POST   │ │Commands │ │   Ext   │          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │
│       │           │           │           │                 │
│       └───────────┴───────────┴───────────┘                 │
│                       │                                      │
│                       ▼                                      │
│              ┌─────────────────┐                            │
│              │ Content Router  │                            │
│              │ (Auto-detection)│                            │
│              └────────┬────────┘                            │
│                       │                                      │
│         ┌─────────────┴─────────────┐                       │
│         ▼                           ▼                       │
│  ┌──────────────┐           ┌──────────────┐              │
│  │   Article    │           │ Code/Note    │              │
│  │   Detected   │           │   Detected   │              │
│  └──────┬───────┘           └──────┬───────┘              │
│         │                           │                       │
│         ▼                           ▼                       │
│  ┌──────────────┐           ┌──────────────┐              │
│  │Ollama Triage │           │Regular Store │              │
│  │  (Analysis)  │           │  (Bypass)    │              │
│  └──────┬───────┘           └──────┬───────┘              │
│         │                           │                       │
│         ▼                           │                       │
│  ┌──────────────┐                  │                       │
│  │Classification│                  │                       │
│  │ & Scoring    │                  │                       │
│  └──────┬───────┘                  │                       │
│         │                           │                       │
│         └───────────┬───────────────┘                       │
│                     ▼                                       │
│           ┌──────────────────┐                             │
│           │  Memory Storage  │                             │
│           │   + Metadata     │                             │
│           └──────────────────┘                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Installation & Setup

### Prerequisites
1. **Ollama Installation**
   ```bash
   # macOS
   brew install ollama
   
   # Start Ollama service
   ollama serve
   ```

2. **Install Required Models**
   ```bash
   # Lightweight model for fast classification (2GB)
   ollama pull phi3:mini
   
   # Better analysis model (2GB)
   ollama pull llama3.2:3b
   
   # Optional: Alternative models
   ollama pull mistral:7b     # Better quality (4GB)
   ollama pull qwen2.5:3b     # Good for structured output (3GB)
   ```

3. **Python Dependencies**
   ```bash
   cd /Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system
   pip install -r requirements.txt
   ```

### Verification
```bash
# Run test suite
python3 test_article_triage.py

# Check Ollama models
ollama list
```

## Core Components

### 1. ArticleDetector (`article_triage.py`)
Detects whether content is an article, code, note, or snippet.

**Detection Criteria:**
- **Articles**: >500 words, has structure (title, sections), contains article markers
- **Code**: Contains code indicators (```, def, function, class, etc.)
- **Notes**: 100-500 words, informal structure
- **Snippets**: <100 words

**Usage:**
```python
from article_triage import ArticleDetector

detector = ArticleDetector()
content_type = detector.detect_content_type(content, metadata)
# Returns: 'article', 'code', 'note', or 'snippet'
```

### 2. OllamaArticleAnalyzer (`article_triage.py`)
Analyzes articles using local Ollama models.

**Features:**
- Auto-selects best available model
- 24-hour result caching
- Quick mode for real-time analysis
- Fallback analysis if Ollama unavailable

**Analysis Output:**
```json
{
  "title": "Article Title",
  "author": "Author Name",
  "summary": "2-3 sentence summary",
  "key_topics": ["topic1", "topic2"],
  "technologies": ["react", "python"],
  "actionability_score": 8,
  "relevance_score": 7,
  "classification": "implement_now",
  "action_items": ["item1", "item2"],
  "key_insights": ["insight1", "insight2"]
}
```

### 3. ArticleTriageService (`article_triage.py`)
Main service coordinating detection, analysis, and storage.

**Classifications:**
- `implement_now`: High-value, immediately actionable
- `reference`: Valuable for future reference
- `monitor`: Emerging trends to track
- `archive`: Lower priority content

## API Documentation

### Base URL
```
http://localhost:8091
```

### Endpoints

#### 1. Analyze Article (No Storage)
```http
POST /api/article/analyze
Content-Type: application/json

{
  "content": "Article content...",
  "metadata": {},
  "quick_mode": false
}

Response:
{
  "status": "analyzed",
  "analysis": {
    "title": "...",
    "classification": "implement_now",
    "actionability_score": 8,
    ...
  },
  "metadata": {...},
  "recommendations": {...}
}
```

#### 2. Triage and Store Article
```http
POST /api/article/triage
Content-Type: application/json

{
  "content": "Article content...",
  "project": "ai-tools",
  "tags": ["react", "tutorial"],
  "source": "medium",
  "source_url": "https://...",
  "metadata": {}
}

Response:
{
  "status": "triaged_and_stored",
  "memory_id": "abc123",
  "title": "Building React Apps",
  "classification": "implement_now",
  "actionability_score": 9,
  "relevance_score": 8,
  "summary": "...",
  "recommendations": {...}
}
```

#### 3. Get Actionable Articles
```http
GET /api/article/actionable?limit=10

Response:
{
  "articles": [
    {
      "memory_id": "abc123",
      "title": "...",
      "actionability_score": 9,
      "action_items": [...],
      ...
    }
  ],
  "count": 5
}
```

#### 4. Article Statistics
```http
GET /api/article/stats

Response:
{
  "stats": {
    "total_articles": 42,
    "classifications": {
      "implement_now": 10,
      "reference": 20,
      "monitor": 8,
      "archive": 4
    },
    "average_actionability": 6.5,
    "average_relevance": 7.2,
    "top_technologies": [
      ["react", 15],
      ["python", 12]
    ]
  }
}
```

#### 5. Extract Action Items
```http
POST /api/article/extract
Content-Type: application/json

{
  "memory_id": "abc123"
}

Response:
{
  "memory_id": "abc123",
  "title": "...",
  "action_items": [...],
  "technologies": [...],
  "implementation_steps": [...]
}
```

### Auto-Triage in Memory Store

The standard `/api/memory/store` endpoint now includes automatic article detection:

```http
POST /api/memory/store
Content-Type: application/json

{
  "content": "Long article content...",
  "metadata": {
    "auto_triage": true  // Default: true
  }
}

# If article detected, returns:
{
  "id": "xyz789",
  "article_triage": {
    "title": "Detected Article Title",
    "classification": "reference",
    "summary": "...",
    "priority": "medium"
  }
}
```

## CLI Commands

### Article Commands Group

#### Analyze Article
```bash
# From text
memory article analyze "Article content here..."

# From file
memory article analyze --file article.md

# From URL
memory article analyze --url https://example.com/article

# Quick mode
memory article analyze --file article.txt --quick
```

#### Triage and Store
```bash
# Basic triage
memory article triage "Article content..."

# With project and tags
memory article triage --file article.md \
  --project "ai-tools" \
  --tags "react,hooks,tutorial"

# From URL
memory article triage --url https://dev.to/article \
  --project "web-dev"
```

#### List Actionable Articles
```bash
# Default (10 articles)
memory article actionable

# Custom limit
memory article actionable --limit 5
```

#### View Statistics
```bash
memory article stats
```

## Usage Examples

### Example 1: Hotkey Capture with Auto-Triage
1. Browse to an article on Medium
2. Select all text (⌘A)
3. Press ⌘⇧M
4. System automatically:
   - Detects it's an article
   - Runs Ollama analysis
   - Classifies and scores
   - Stores with metadata

### Example 2: CLI Article Processing
```bash
# Download and triage an article
curl -s https://example.com/article.html | \
  memory article triage --project "tutorials"
```

### Example 3: API Integration
```python
import requests

# Analyze without storing
response = requests.post(
    "http://localhost:8091/api/article/analyze",
    json={"content": article_text, "quick_mode": True}
)

if response.json()["status"] == "analyzed":
    analysis = response.json()["analysis"]
    print(f"Classification: {analysis['classification']}")
    print(f"Should implement: {analysis['actionability_score'] >= 8}")
```

### Example 4: Finding Actionable Content
```bash
# Get high-priority articles to implement
memory article actionable --limit 3

# Output:
# ✅ Building a CLI Tool with Python
#    ID: abc123 | Score: 9/10
#    Classification: implement_now
#    Action Items:
#     • Install Click and Rich libraries
#     • Create command structure
#     • Add error handling
```

## Configuration

### Environment Variables
```bash
# Ollama configuration
export OLLAMA_URL="http://localhost:11434"
export OLLAMA_ARTICLE_MODEL="phi3:mini"  # or llama3.2:3b, mistral:7b
export OLLAMA_TIMEOUT=30

# Triage configuration
export ARTICLE_CACHE_HOURS=24
export ARTICLE_MIN_WORDS=500
export ARTICLE_QUICK_MODE=false

# Auto-triage in memory store
export AUTO_TRIAGE_ENABLED=true
export AUTO_TRIAGE_MIN_LENGTH=500
```

### Model Selection
Models are selected in order of preference:
1. Environment variable `OLLAMA_ARTICLE_MODEL`
2. Auto-detection of best available:
   - `llama3.2:3b` (recommended)
   - `phi3:mini` (fastest)
   - `mistral:7b` (best quality)
   - First available model (fallback)

### Disabling Auto-Triage
```python
# Via API
{
  "content": "...",
  "metadata": {"auto_triage": false}
}

# Via CLI
memory store "content" --metadata '{"auto_triage": false}'
```

## Troubleshooting

### Issue: Ollama Not Responding
```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Restart Ollama
killall ollama
ollama serve

# Verify models installed
ollama list
```

### Issue: Articles Misclassified as Notes
**Cause**: Content too short or lacks article structure
**Solution**: 
- Capture complete articles when possible
- Include title and introduction
- Ensure >500 words

### Issue: Slow Analysis
**Cause**: Using large model or cold cache
**Solutions**:
```bash
# Switch to faster model
export OLLAMA_ARTICLE_MODEL="phi3:mini"

# Use quick mode for real-time capture
memory article analyze --quick

# Pre-warm model
ollama run phi3:mini "test"
```

### Issue: High Memory Usage
**Cause**: Multiple large models loaded
**Solution**:
```bash
# Unload unused models
curl -X DELETE http://localhost:11434/api/delete \
  -d '{"name": "mistral:7b"}'
```

## Implementation Details

### Database Schema
```sql
-- Article metadata table
CREATE TABLE article_metadata (
    memory_id TEXT PRIMARY KEY,
    title TEXT,
    author TEXT,
    publication_date INTEGER,
    reading_time INTEGER,
    relevance_score REAL,
    actionability_score REAL,
    classification TEXT,
    key_topics TEXT,          -- JSON array
    technologies TEXT,         -- JSON array
    action_items TEXT,        -- JSON array
    key_insights TEXT,        -- JSON array
    summary TEXT,
    analysis_timestamp INTEGER,
    analysis_method TEXT,
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);

-- Indexes for performance
CREATE INDEX idx_article_classification ON article_metadata(classification);
CREATE INDEX idx_article_actionability ON article_metadata(actionability_score);
CREATE INDEX idx_article_relevance ON article_metadata(relevance_score);
```

### Classification Logic
```python
# Scoring factors for classification
actionability_factors = [
    'step-by-step instructions',
    'code examples',
    'installation commands',
    'implementation guide'
]

relevance_factors = [
    'matches user interests',
    'related to current projects',
    'trending technology',
    'solves known problem'
]

# Classification thresholds
if actionability >= 8 and relevance >= 7:
    classification = "implement_now"
elif relevance >= 8:
    classification = "monitor"
elif actionability >= 6 or relevance >= 6:
    classification = "reference"
else:
    classification = "archive"
```

### Performance Characteristics
- **Detection time**: <10ms
- **Analysis time**: 2-5 seconds (Ollama)
- **Storage time**: <100ms
- **Cache hit**: <5ms
- **Memory overhead**: ~50MB for service
- **Model memory**: 2-8GB depending on model

## Change Log

### Version 1.0.0 (2025-08-13)
- Initial implementation of Article Triage System
- Ollama integration for local analysis
- Auto-detection in memory store endpoint
- CLI commands for article management
- API endpoints for triage operations
- Caching system for performance
- Fallback analysis for offline mode
- Test suite for validation

## Related Documentation
- [Universal AI Memory System README](README.md)
- [API Service Documentation](src/api_service.py)
- [CLI Documentation](src/memory_cli.py)
- [Test Suite](test_article_triage.py)

---

*This documentation is part of the Universal AI Memory System (Encyclopedia Galactica)*