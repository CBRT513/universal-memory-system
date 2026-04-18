# MCP-Enhanced Workflows

## Overview
MCP tools integration enables your system to take direct actions based on article analysis, creating a fully automated workflow from reading articles to implementing changes.

## Available MCP Tools

### 1. GitHub Tools
- `github_list_repos` - List repositories
- `github_create_issue` - Create issues from action items
- `github_get_issues` - Check existing issues
- `github_analyze_repo` - Analyze repository structure

### 2. Git Tools
- `git_status` - Check working directory status
- `git_diff` - Review changes
- `git_branch` - Manage branches
- `git_log` - View commit history
- `git_commit` - Create commits

### 3. Filesystem Tools
- `filesystem_read` - Read files
- `filesystem_write` - Write files
- `filesystem_list` - List directory contents
- `filesystem_search` - Search for patterns

### 4. Browser Tools
- `browser_screenshot` - Capture webpage screenshots
- `browser_scrape` - Extract webpage content
- `browser_test` - Run browser tests

### 5. Memory Tools
- `memory_store` - Store in UMS
- `memory_recall` - Retrieve from UMS
- `memory_stats` - Get statistics

## Workflow Examples

### Workflow 1: Article → GitHub Issue
**Trigger**: Article about new feature or bug
**Process**:
1. Article captured and classified as "action-required"
2. Article Analysis Crew extracts action items
3. MCP creates GitHub issue in relevant project
4. Notification sent with issue URL

**Command**:
```bash
# Analyze recent articles and create issues
venv/bin/python src/mcp_article_integration.py
```

### Workflow 2: Article → Implementation Plan
**Trigger**: Article about implementation technique
**Process**:
1. Article analyzed for actionable patterns
2. MCP searches codebase for related files
3. Creates implementation plan document
4. Stores plan in project directory
5. Updates project CLAUDE.md with new approach

**Example**:
```python
# Article about CrewAI patterns
# System automatically:
# 1. Identifies AgentForge as target project
# 2. Creates IMPLEMENTATION_PLAN_CrewAI.md
# 3. Lists files to modify
# 4. Generates code snippets
```

### Workflow 3: Article → Documentation
**Trigger**: Article about best practices
**Process**:
1. Article analyzed for key concepts
2. MCP creates documentation file
3. Stores in UMS memory for future reference
4. Updates project README if needed

### Workflow 4: Multi-Project Updates
**Trigger**: Article about security update
**Process**:
1. Article identifies security issue
2. MCP searches all projects for vulnerability
3. Creates issues in affected repositories
4. Generates patch files for each project
5. Sends consolidated notification

## Quick Test Commands

### Test MCP Tools Bridge
```bash
cd /usr/local/share/universal-memory-system
venv/bin/python src/mcp_tools_bridge.py
```

### Process Articles with MCP
```bash
cd /usr/local/share/universal-memory-system
venv/bin/python src/mcp_article_integration.py
```

### Manual Tool Execution
```python
import asyncio
from mcp_tools_bridge import MCPToolsBridge

async def test():
    bridge = MCPToolsBridge()
    
    # Create GitHub issue
    result = await bridge.execute_tool("github_create_issue", {
        "repo": "cerion/project",
        "title": "Test Issue",
        "body": "Testing MCP integration"
    })
    print(result)

asyncio.run(test())
```

## Integration Points

### 1. Article Analysis Crew
- Located: `/usr/local/share/universal-memory-system/src/article_crew.py`
- Enhancement: Crew agents can now use MCP tools
- Example: Validator finds bug → Extractor creates action → MCP creates issue

### 2. AgentForge Multi-Agent System
- Located: `/Users/cerion/Projects/AgentWorkspace/agentforge/backend/app/core/agent_crew.py`
- Enhancement: Agents can use MCP tools for code generation
- Example: DialogueBuilder crew uses filesystem tools to scaffold apps

### 3. Claude Code Subagent Routing
- Located: `/usr/local/share/universal-memory-system/galactica-agent/mcp_server.py`
- Enhancement: Subagents can delegate to MCP tools
- Example: frontend-specialist uses browser tools for testing

## Configuration

### Environment Variables
```bash
# GitHub access
export GITHUB_TOKEN="your_github_token"

# Project paths
export PROJECTS_BASE="$HOME/Projects"

# UMS API
export UMS_API_URL="http://localhost:8091"
```

### Project Context
Edit `/usr/local/share/universal-memory-system/src/mcp_article_integration.py` to add your projects:

```python
"projects": [
    {
        "name": "YourProject",
        "path": "/path/to/project",
        "repo": "username/repo",
        "description": "Project description"
    }
]
```

## Automation Examples

### Auto-Issue Creation
```bash
# Run every hour to process new articles
while true; do
    venv/bin/python src/mcp_article_integration.py
    sleep 3600
done
```

### Git Status Monitor
```bash
# Check all projects for uncommitted changes
for project in AgentForge Machine_Maintenance_App; do
    echo "Checking $project..."
    venv/bin/python -c "
import asyncio
from mcp_tools_bridge import MCPToolsBridge

async def check():
    bridge = MCPToolsBridge()
    result = await bridge.execute_tool('git_status', {
        'repo_path': '/Users/cerion/Projects/$project'
    })
    print(result)

asyncio.run(check())
"
done
```

## Benefits

1. **Automatic Action Taking**: Articles don't just inform, they trigger actions
2. **Cross-Project Coordination**: Single article can update multiple projects
3. **Memory Integration**: All actions stored in UMS for future reference
4. **GitHub Integration**: Direct issue creation from article insights
5. **Code Generation**: Articles can trigger actual code updates
6. **Documentation**: Automatic documentation from article learnings

## Next Steps

1. **Add more MCP tools**: Slack, Discord, email integrations
2. **Enhance decision logic**: ML-based action classification
3. **Add review step**: Human approval before critical actions
4. **Create dashboards**: Visualize article → action pipeline
5. **Add metrics**: Track action success rates

## Troubleshooting

### MCP Tools Not Working
```bash
# Check if aiohttp is installed
venv/bin/pip list | grep aiohttp

# Reinstall if needed
venv/bin/pip install aiohttp
```

### GitHub Integration Issues
```bash
# Test GitHub CLI
gh auth status

# Set GitHub token
export GITHUB_TOKEN="your_token"
```

### Memory Integration Issues
```bash
# Check UMS API
curl http://localhost:8091/api/stats

# Restart UMS if needed
sudo launchctl unload /Library/LaunchDaemons/com.ums.api.plist
sudo launchctl load /Library/LaunchDaemons/com.ums.api.plist
```

---

## Summary

The MCP tools integration transforms your article analysis system from passive observation to active implementation. Articles now directly create issues, generate code, update documentation, and coordinate across projects - all automatically based on AI analysis and your configured rules.