# MCP Tools Complete Implementation Guide

## Overview
This guide provides comprehensive documentation for the MCP (Model Context Protocol) tools integration with the Universal Memory System. The system enables automated actions based on article analysis, creating a fully autonomous workflow from reading articles to implementing changes.

## System Architecture

### Components
1. **MCP Tools Bridge** (`src/mcp_tools_bridge.py`)
   - Native Python implementation
   - Supports GitHub, Git, Filesystem, Browser, and Memory operations
   - No external MCP server dependencies

2. **Article Analysis Crew** (`src/article_crew.py`)
   - Multi-agent system for article validation
   - Extracts actionable items
   - Determines implementation priority

3. **MCP Article Integration** (`src/mcp_article_integration.py`)
   - Combines article analysis with MCP actions
   - Automates workflow execution
   - Tracks and reports on actions taken

4. **Claude Desktop Integration** (`claude_desktop_config.json`)
   - Configures MCP servers for Claude Desktop
   - Enables direct tool access from Claude

## Installation & Setup

### Prerequisites
```bash
# Python 3.9+ required
python3 --version

# Install required packages
cd /usr/local/share/universal-memory-system
venv/bin/pip install aiohttp crewai openai
```

### Environment Variables
```bash
# Required for full functionality
export GITHUB_TOKEN="your_github_token"  # For GitHub operations
export OPENAI_API_KEY="your_api_key"     # For AI analysis

# Optional
export UMS_API_URL="http://localhost:8091"  # Default UMS API endpoint
```

### MCP Tools Configuration

#### 1. Install MCP servers (for Claude Desktop)
```bash
# Install Node.js MCP servers globally
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-memory
npm install -g @modelcontextprotocol/server-puppeteer
```

#### 2. Configure Claude Desktop
The configuration is already set in:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Current configuration includes:
- **filesystem**: Access to ~/Projects directory
- **git**: AgentForge repository access
- **memory**: Ephemeral memory storage
- **puppeteer**: Browser automation
- **ums-galactica**: Custom UMS integration

## Available MCP Tools

### GitHub Tools
```python
# List repositories
await bridge.execute_tool("github_list_repos", {"user": "username"})

# Create issue
await bridge.execute_tool("github_create_issue", {
    "repo": "owner/repo",
    "title": "Issue title",
    "body": "Issue description"
})

# Get issues
await bridge.execute_tool("github_get_issues", {
    "repo": "owner/repo",
    "state": "open"  # or "closed", "all"
})

# Analyze repository
await bridge.execute_tool("github_analyze_repo", {"repo": "owner/repo"})
```

### Git Tools
```python
# Get status
await bridge.execute_tool("git_status", {"repo_path": "/path/to/repo"})

# Get diff
await bridge.execute_tool("git_diff", {
    "repo_path": "/path/to/repo",
    "cached": False  # True for staged changes
})

# Get branches
await bridge.execute_tool("git_branch", {"repo_path": "/path/to/repo"})

# Get log
await bridge.execute_tool("git_log", {
    "repo_path": "/path/to/repo",
    "limit": 10
})

# Commit changes
await bridge.execute_tool("git_commit", {
    "repo_path": "/path/to/repo",
    "message": "Commit message",
    "files": ["file1.py", "file2.py"]
})
```

### Filesystem Tools
```python
# Read file
await bridge.execute_tool("filesystem_read", {"path": "/path/to/file"})

# Write file
await bridge.execute_tool("filesystem_write", {
    "path": "/path/to/file",
    "content": "File content"
})

# List directory
await bridge.execute_tool("filesystem_list", {"path": "/path/to/dir"})
```

### Memory Tools
```python
# Store memory
await bridge.execute_tool("memory_store", {
    "content": "Information to remember",
    "tags": ["tag1", "tag2"],
    "category": "article"
})

# Recall memory
await bridge.execute_tool("memory_recall", {
    "query": "search query",
    "limit": 5
})

# Get statistics
await bridge.execute_tool("memory_stats", {})
```

## Workflow Examples

### 1. Automated Article Processing
```python
from src.mcp_article_integration import MCPArticleIntegration

# Process recent articles
integration = MCPArticleIntegration()
results = await integration.process_recent_articles(limit=5)

# Results include:
# - Article analysis verdict
# - Extracted action items
# - MCP actions taken
# - GitHub issues created
# - Code updates prepared
```

### 2. Article-Driven Development
```python
# Article: "Implement OAuth2 in Python Flask"
# System automatically:
# 1. Validates article relevance
# 2. Extracts implementation steps
# 3. Creates GitHub issue with requirements
# 4. Prepares code scaffolding
# 5. Updates project documentation
```

### 3. Knowledge-to-Action Pipeline
```python
# Read article → Analyze content → Extract actions → Execute tools
article = {
    "title": "Best Practices for API Design",
    "content": "...",
    "tags": ["api", "backend", "actionable"]
}

# Automatic workflow:
crew_analysis = await crew.process_article(article)
if crew_analysis["verdict"] == "IMPLEMENT_NOW":
    mcp_actions = await integration.execute_mcp_actions(article, crew_analysis)
```

## Testing & Validation

### Test MCP Connections
```bash
# Test all tool connections
cd /usr/local/share/universal-memory-system
venv/bin/python -c "
import asyncio
from src.mcp_tools_bridge import MCPToolsBridge
bridge = MCPToolsBridge()
result = asyncio.run(bridge.test_connections())
import json
print(json.dumps(result, indent=2))
"
```

### Test Article Crew
```bash
# Process recent articles with crew
venv/bin/python src/article_crew.py
```

### Test End-to-End Integration
```bash
# Run complete MCP article workflow
venv/bin/python src/mcp_article_integration.py
```

## Troubleshooting

### Common Issues

#### 1. GitHub Token Not Set
```bash
# Error: github_status: "no_token"
# Solution:
export GITHUB_TOKEN="your_github_personal_access_token"
```

#### 2. UMS API Not Running
```bash
# Error: memory_status: "not_running"
# Solution: Start UMS API service
cd /usr/local/share/universal-memory-system
venv/bin/python src/api_service.py
```

#### 3. OpenAI API Key Missing
```bash
# Error: OpenAI API key not found
# Solution:
export OPENAI_API_KEY="your_openai_api_key"
```

#### 4. MCP Servers Not Installed
```bash
# Error: MCP server not found
# Solution: Install MCP servers
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-git
# ... install other servers
```

### Debug Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual tools
bridge = MCPToolsBridge()
result = await bridge.execute_tool("tool_name", {"param": "value"})
print(f"Result: {result}")
```

## Integration Points

### 1. UMS API Service
- Endpoint: `http://localhost:8091`
- Provides article storage and retrieval
- Manages notification system
- Tracks TODOs and action items

### 2. Article Analysis Crew
- Uses CrewAI framework
- Three specialized agents:
  - Validator: Checks article relevance
  - Extractor: Identifies action items
  - Analyzer: Determines implementation priority

### 3. Notification System
- Desktop notifications for actionable content
- Priority-based alerting
- Integration with system notification center

## Advanced Usage

### Custom Tool Creation
```python
class CustomMCPBridge(MCPToolsBridge):
    async def handle_custom_tool(self, tool: str, params: Dict) -> Dict:
        """Add custom tool handlers"""
        if tool == "custom_analyze":
            # Custom implementation
            return {"status": "success", "result": "..."}
```

### Workflow Automation
```python
# Create automated pipeline
async def automated_pipeline():
    # 1. Monitor for new articles
    articles = await fetch_new_articles()
    
    # 2. Process with crew
    for article in articles:
        analysis = await crew.process_article(article)
        
        # 3. Execute MCP actions
        if analysis["verdict"] == "IMPLEMENT_NOW":
            await execute_mcp_workflow(article, analysis)
        
        # 4. Track results
        await store_execution_results(results)
```

### Batch Processing
```python
# Process multiple articles efficiently
async def batch_process(articles: List[Dict]):
    tasks = []
    for article in articles:
        task = asyncio.create_task(
            integration.process_article_with_mcp(article)
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

## Performance Considerations

### Optimization Tips
1. **Batch API calls**: Group GitHub/Git operations
2. **Cache results**: Store frequently accessed data
3. **Async operations**: Use asyncio for parallel processing
4. **Rate limiting**: Respect API rate limits
5. **Connection pooling**: Reuse HTTP connections

### Resource Management
```python
# Proper cleanup
async with MCPArticleIntegration() as integration:
    results = await integration.process_recent_articles()
    # Resources automatically cleaned up
```

## Security Best Practices

### Token Management
- Store tokens in environment variables
- Never commit tokens to version control
- Use read-only tokens when possible
- Rotate tokens regularly

### File System Access
- Validate all file paths
- Use sandboxed directories
- Implement access controls
- Log all file operations

### API Security
- Use HTTPS for all external calls
- Validate SSL certificates
- Implement request timeouts
- Handle errors gracefully

## Monitoring & Logging

### Enable Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/mcp_integration.log'),
        logging.StreamHandler()
    ]
)
```

### Track Metrics
```python
# Monitor tool usage
bridge = MCPToolsBridge()
# After operations
print(f"Tool usage: {bridge.tool_usage}")
```

## Future Enhancements

### Planned Features
1. **WebSocket support**: Real-time article monitoring
2. **Plugin system**: Extensible tool architecture
3. **ML-powered routing**: Smart action selection
4. **Distributed execution**: Multi-node processing
5. **Advanced caching**: Intelligent result caching

### Integration Roadmap
- [ ] Slack integration for notifications
- [ ] JIRA integration for issue tracking
- [ ] CI/CD pipeline integration
- [ ] Cloud storage support (S3, GCS)
- [ ] Database backends (PostgreSQL, MongoDB)

## Support & Resources

### Documentation
- MCP Protocol: https://modelcontextprotocol.io
- CrewAI: https://github.com/joaomdmoura/crewai
- UMS Documentation: `/usr/local/share/universal-memory-system/README.md`

### Debugging
```bash
# Check system status
venv/bin/python -c "
from src.mcp_tools_bridge import MCPToolsBridge
import asyncio
bridge = MCPToolsBridge()
asyncio.run(bridge.test_connections())
"

# View logs
tail -f /var/log/ums_api.log
tail -f /var/log/mcp_integration.log
```

### Community
- Report issues: GitHub Issues
- Discussions: GitHub Discussions
- Updates: Follow project releases

## Conclusion

The MCP Tools integration provides a powerful bridge between knowledge acquisition (articles) and action execution (development tasks). By combining AI-powered analysis with automated tool execution, the system creates a seamless workflow from learning to implementation.

Key benefits:
- **Automated workflows**: Articles trigger appropriate actions
- **Intelligent routing**: AI determines best actions
- **Tool integration**: GitHub, Git, filesystem access
- **Extensible architecture**: Easy to add new tools
- **Production ready**: Error handling and logging

The system is designed to grow with your needs, supporting everything from simple automations to complex multi-step workflows.