# Claude Code SubAgents System

A comprehensive collection of 17 specialized Claude Code SubAgents integrated with the Universal Memory System. These subagents automate specific coding tasks, from frontend development to DevOps, with built-in memory persistence and workflow integration.

## 🚀 Quick Start

```bash
# List all available subagents
python3 subagents/cli/subagent_cli.py list

# Create all subagent files
python3 subagents/cli/subagent_cli.py create-all

# Execute a subagent
python3 subagents/cli/subagent_cli.py execute frontend-developer "Build a React dashboard"
```

## 📦 Available SubAgents

### Development SubAgents
1. **frontend-developer** - React, Vue, modern UI development
2. **backend-developer** - Server-side logic, APIs, databases
3. **api-developer** - RESTful and GraphQL API design
4. **mobile-developer** - React Native, Flutter, iOS/Android
5. **python-developer** - Python-specific development patterns
6. **javascript-developer** - Modern JavaScript ES2024+
7. **typescript-developer** - Type-safe TypeScript development

### Infrastructure & Operations
8. **devops-engineer** - CI/CD, containerization, automation
9. **database-architect** - Database design and optimization
10. **cloud-architect** - AWS, Azure, GCP architecture
11. **security-engineer** - Security audits and best practices
12. **performance-engineer** - Performance optimization

### Quality & Testing
13. **test-automation-engineer** - Comprehensive test suites
14. **code-reviewer** - Code quality and best practices

### Data & ML
15. **data-engineer** - Data pipelines and ETL
16. **ml-engineer** - Machine learning systems

### Documentation
17. **documentation-writer** - Technical documentation

## 🎯 Usage Examples

### Basic Usage

```bash
# Show details of a specific subagent
python3 subagents/cli/subagent_cli.py show frontend-developer

# Get model recommendation for a task
python3 subagents/cli/subagent_cli.py recommend backend

# List available models
python3 subagents/cli/subagent_cli.py models
```

### Creating Custom SubAgents

```bash
# Create a custom subagent from instructions file
python3 subagents/cli/subagent_cli.py create-custom \
  my-agent \
  "Custom agent for specific task" \
  instructions.txt \
  --model sonnet
```

### Workflow Examples

#### Full-Stack Development Workflow
```bash
# Chain multiple subagents for full-stack development
make workflow-fullstack
```

This runs:
1. Frontend Developer - Create UI components
2. Backend Developer - Build API endpoints
3. API Developer - Document the API
4. Test Engineer - Create test suites

#### Deployment Workflow
```bash
# Prepare for production deployment
make workflow-deploy
```

This runs:
1. Security Engineer - Security audit
2. Performance Engineer - Optimization
3. DevOps Engineer - Deploy to production

## 🔧 Configuration

### Model Configuration (`configs/models.json`)

```json
{
  "models": {
    "sonnet": {
      "name": "claude-3-5-sonnet-latest",
      "description": "Best for complex coding tasks",
      "max_tokens": 8192,
      "temperature": 0.2
    }
  }
}
```

### Performance Settings (`configs/performance.json`)

```json
{
  "performance": {
    "parallel_execution": {
      "enabled": true,
      "max_concurrent_agents": 5
    },
    "caching": {
      "enabled": true,
      "ttl_seconds": 3600
    }
  }
}
```

## 🔗 Integration

### VS Code Integration

Tasks are automatically configured in `.vscode/tasks.json`:

1. Open Command Palette (`Cmd+Shift+P`)
2. Run "Tasks: Run Task"
3. Select a SubAgent task

### Git Hooks

Pre-commit hook automatically runs code review:

```bash
# Install git hook
cp subagents/hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

### Makefile Commands

```bash
make list          # List all subagents
make create-all    # Create all subagent files
make test-frontend # Test frontend subagent
make test-backend  # Test backend subagent
make review        # Run code review
```

## 💾 Memory System Integration

All subagent executions are automatically stored in the Universal Memory System:

- **Pattern Storage**: Successful solutions are saved for future reference
- **Context Retrieval**: Relevant past solutions are retrieved automatically
- **Execution Logging**: All executions are logged with results

### Accessing Stored Patterns

```bash
# Search for frontend patterns
python3 src/memory_cli.py search "subagent-frontend-developer pattern"

# View all subagent executions
python3 src/memory_cli.py search "subagent_log"
```

## 🏗️ Architecture

```
subagents/
├── templates/          # 17 SubAgent templates
│   ├── frontend-developer.yaml
│   ├── backend-developer.yaml
│   └── ...
├── configs/           # Configuration files
│   ├── models.json
│   └── performance.json
├── lib/              # Core libraries
│   ├── subagent_manager.py
│   └── integration.py
├── cli/              # CLI interface
│   └── subagent_cli.py
├── output/           # Generated subagent files
└── workflows/        # Workflow scripts
```

## 🚦 Best Practices

### 1. Choose the Right SubAgent
- Use specialized agents for specific tasks
- Chain multiple agents for complex workflows
- Let the system recommend models based on task type

### 2. Leverage Memory Integration
- Past solutions are automatically retrieved
- Successful patterns are stored for reuse
- Review execution logs to improve prompts

### 3. Optimize Performance
- Enable caching for repeated tasks
- Use parallel execution for independent tasks
- Monitor resource usage with performance config

### 4. Create Custom Workflows
- Combine subagents for your specific needs
- Use Makefile targets for common workflows
- Integrate with CI/CD pipelines

## 🔍 Troubleshooting

### Claude Code CLI Not Found
```bash
# Ensure Claude Code is installed
brew install claude-code  # macOS
# or
npm install -g claude-code  # via npm
```

### Memory System Connection Issues
```bash
# Check if memory API is running
curl http://localhost:8091/api/health

# Start memory API if needed
python3 src/api_service.py --port 8091
```

### Permission Errors
```bash
# Make CLI executable
chmod +x subagents/cli/subagent_cli.py

# Fix Python path issues
export PYTHONPATH=$PYTHONPATH:/usr/local/share/universal-memory-system
```

## 📚 Advanced Usage

### Batch Processing
```python
from subagents.lib.subagent_manager import SubAgentManager

manager = SubAgentManager()

# Process multiple tasks
tasks = [
    ("frontend-developer", "Create login form"),
    ("backend-developer", "Create auth endpoint"),
    ("test-automation-engineer", "Write tests")
]

for agent, task in tasks:
    result = manager.execute_subagent(agent, task)
    print(f"{agent}: {result}")
```

### Custom Integration
```python
from subagents.lib.integration import MemoryIntegration

memory = MemoryIntegration()

# Store custom pattern
memory.store_subagent_pattern(
    agent_name="frontend-developer",
    pattern="React Hook for API calls",
    context="Authentication flow",
    tags=["react", "hooks", "auth"]
)

# Retrieve relevant context
context = memory.retrieve_relevant_context(
    agent_name="frontend-developer",
    task="Build user dashboard",
    limit=5
)
```

## 🤝 Contributing

To add new subagent templates:

1. Create a YAML template in `subagents/templates/`
2. Follow the existing format with frontmatter and instructions
3. Update model recommendations in `configs/models.json`
4. Test the new subagent with the CLI

## 📄 License

Part of the Universal Memory System. See main project license.

## 🔗 Related Documentation

- [Universal Memory System](../README.md)
- [Memory CLI Guide](../SIMPLE_CLI_GUIDE.md)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)

---

*Built with the Universal Memory System - Your AI's Encyclopedia Galactica*