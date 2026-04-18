# MCP Tools Quick Setup Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Install Dependencies
```bash
cd /usr/local/share/universal-memory-system
venv/bin/pip install aiohttp crewai openai
```

### Step 2: Set Environment Variables
```bash
# Add to ~/.zshrc or ~/.bash_profile
export GITHUB_TOKEN="your_github_token"    # Get from: https://github.com/settings/tokens
export OPENAI_API_KEY="your_openai_key"    # Get from: https://platform.openai.com/api-keys
```

### Step 3: Test Installation
```bash
# Test MCP bridges
venv/bin/python -c "
import asyncio
from src.mcp_tools_bridge import MCPToolsBridge
bridge = MCPToolsBridge()
result = asyncio.run(bridge.test_connections())
print('✅ MCP Tools Ready!' if result['status'] == 'ready' else '⚠️ Some tools need configuration')
"
```

## 📋 Verification Checklist

Run this command to check your setup:
```bash
venv/bin/python -c "
import os
import subprocess
import json

print('🔍 MCP Setup Verification')
print('=' * 40)

# Check Python
print(f'✓ Python: {subprocess.run([\"python3\", \"--version\"], capture_output=True, text=True).stdout.strip()}')

# Check environment variables
github = '✓' if os.getenv('GITHUB_TOKEN') else '✗'
openai = '✓' if os.getenv('OPENAI_API_KEY') else '✗'
print(f'{github} GitHub Token: {\"Set\" if github == \"✓\" else \"Not set\"}')
print(f'{openai} OpenAI API Key: {\"Set\" if openai == \"✓\" else \"Not set\"}')

# Check Git
git = subprocess.run(['git', '--version'], capture_output=True, text=True)
print(f'✓ Git: {git.stdout.strip()}' if git.returncode == 0 else '✗ Git not found')

# Check Claude config
import pathlib
config_path = pathlib.Path.home() / 'Library/Application Support/Claude/claude_desktop_config.json'
if config_path.exists():
    print(f'✓ Claude Desktop Config: Found')
else:
    print(f'✗ Claude Desktop Config: Not found')

print('=' * 40)
"
```

## 🎯 Usage Examples

### Process Articles Automatically
```bash
# Run article analysis with MCP actions
venv/bin/python src/mcp_article_integration.py
```

### Test Individual Tools
```bash
# Test GitHub integration
venv/bin/python -c "
import asyncio
from src.mcp_tools_bridge import MCPToolsBridge
bridge = MCPToolsBridge()
result = asyncio.run(bridge.execute_tool('github_list_repos', {'user': 'cerion'}))
print(f'Found {result.get(\"count\", 0)} repositories')
"
```

## 🔧 Troubleshooting

### Issue: "GitHub token not set"
```bash
# Solution: Create a GitHub Personal Access Token
# 1. Go to: https://github.com/settings/tokens
# 2. Click "Generate new token (classic)"
# 3. Select scopes: repo, read:user
# 4. Copy token and add to ~/.zshrc:
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "OpenAI API key not found"
```bash
# Solution: Get OpenAI API Key
# 1. Go to: https://platform.openai.com/api-keys
# 2. Create new secret key
# 3. Copy key and add to ~/.zshrc:
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "UMS API not running"
```bash
# Solution: Start UMS API service
cd /usr/local/share/universal-memory-system
venv/bin/python src/api_service.py &
```

### Issue: "Module not found"
```bash
# Solution: Reinstall dependencies
cd /usr/local/share/universal-memory-system
venv/bin/pip install --upgrade aiohttp crewai openai
```

## 📦 What's Included

### Core Components
- **MCP Tools Bridge** - Native Python implementation of MCP tools
- **Article Analysis Crew** - AI agents for content analysis  
- **MCP Article Integration** - Automated article-to-action workflow
- **Claude Desktop Config** - Pre-configured MCP servers

### Available Tools
- **GitHub**: Create issues, list repos, analyze code
- **Git**: Status, diff, commit, branch management
- **Filesystem**: Read, write, list files
- **Memory**: Store and recall information
- **Browser**: Screenshot and scrape (requires Playwright)

## 🚦 Status Check

Run this to see current system status:
```bash
venv/bin/python src/mcp_tools_bridge.py
```

Expected output:
```
🔧 MCP Tools Bridge Test
========================================

📦 Testing GitHub tools...
  Repos found: [number]

🔀 Testing Git tools...
  Git status: success

📁 Testing Filesystem tools...
  Files found: [number]

🧠 Testing Memory tools...
  Memory stats: success

✅ MCP Tools Bridge operational!
```

## 📚 Next Steps

1. **Test Article Processing**
   ```bash
   venv/bin/python src/article_crew.py
   ```

2. **Run Full Integration**
   ```bash
   venv/bin/python src/mcp_article_integration.py
   ```

3. **Read Full Documentation**
   ```bash
   cat docs/MCP_COMPLETE_GUIDE.md
   ```

## 💡 Tips

- Set `GITHUB_TOKEN` for full GitHub functionality
- Set `OPENAI_API_KEY` for AI-powered analysis
- Keep UMS API running for memory operations
- Check logs in `/var/log/` for debugging

## 🆘 Need Help?

1. Check full guide: `docs/MCP_COMPLETE_GUIDE.md`
2. View example workflows: `MCP_WORKFLOWS.md`
3. Test connections: `venv/bin/python -m src.mcp_tools_bridge`

---
*Setup completed in under 5 minutes! The system is now ready to automatically process articles and execute actions.*