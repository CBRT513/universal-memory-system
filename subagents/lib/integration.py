#!/usr/bin/env python3
"""
Integration module for Claude Code SubAgents with Universal Memory System
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests

# Add parent directory to path for memory system imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class MemoryIntegration:
    """Integration with Universal Memory System"""
    
    def __init__(self, api_base: str = "http://localhost:8091"):
        self.api_base = api_base
        self.headers = {"Content-Type": "application/json"}
    
    def store_subagent_pattern(self, agent_name: str, pattern: str, 
                               context: str, tags: List[str] = None) -> bool:
        """Store a successful pattern from a subagent"""
        try:
            memory_content = f"""
SubAgent Pattern: {agent_name}
Pattern: {pattern}
Context: {context}
Timestamp: {datetime.now().isoformat()}
Source: Claude Code SubAgent System
"""
            
            payload = {
                "content": memory_content,
                "category": "subagent_pattern",
                "tags": tags or [f"subagent-{agent_name}", "pattern", "automation"],
                "importance": 8,
                "metadata": {
                    "agent_name": agent_name,
                    "pattern_type": "solution",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            response = requests.post(
                f"{self.api_base}/api/memory/store",
                json=payload,
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error storing pattern: {e}")
            return False
    
    def retrieve_relevant_context(self, agent_name: str, task: str, 
                                 limit: int = 5) -> List[Dict]:
        """Retrieve relevant context for a subagent task"""
        try:
            params = {
                "q": f"{agent_name} {task}",
                "limit": limit
            }
            
            response = requests.get(
                f"{self.api_base}/api/memory/search",
                params=params,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            
            return []
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    def log_subagent_execution(self, agent_name: str, task: str, 
                              result: str, success: bool = True):
        """Log subagent execution in memory system"""
        try:
            status = "successful" if success else "failed"
            
            memory_content = f"""
SubAgent Execution Log
Agent: {agent_name}
Task: {task}
Status: {status}
Result Summary: {result[:500]}...
Timestamp: {datetime.now().isoformat()}
"""
            
            payload = {
                "content": memory_content,
                "category": "subagent_log",
                "tags": [f"subagent-{agent_name}", "execution", status],
                "importance": 6 if success else 8,
                "metadata": {
                    "agent_name": agent_name,
                    "task": task,
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            response = requests.post(
                f"{self.api_base}/api/memory/store",
                json=payload,
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error logging execution: {e}")
            return False

class WorkflowIntegration:
    """Integration with existing development workflows"""
    
    def __init__(self):
        self.memory = MemoryIntegration()
        self.subagents_dir = Path(__file__).parent.parent
    
    def create_workflow_script(self, workflow_name: str, agents: List[str]) -> Path:
        """Create a workflow script that chains multiple subagents"""
        script_path = self.subagents_dir / "workflows" / f"{workflow_name}.sh"
        script_path.parent.mkdir(exist_ok=True)
        
        script_content = f"""#!/bin/bash
# Workflow: {workflow_name}
# Generated: {datetime.now().isoformat()}
# This workflow chains multiple Claude Code SubAgents

set -e  # Exit on error

echo "Starting workflow: {workflow_name}"

# Change to subagents directory
cd "{self.subagents_dir}"

"""
        
        for i, agent in enumerate(agents, 1):
            script_content += f"""
echo "Step {i}: Running {agent} subagent..."
python3 cli/subagent_cli.py execute {agent} "${{1:-Default task}}"

if [ $? -ne 0 ]; then
    echo "Error: {agent} subagent failed"
    exit 1
fi

echo "Step {i} completed successfully"
"""
        
        script_content += """
echo "Workflow completed successfully!"
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        script_path.chmod(0o755)
        
        print(f"Created workflow script: {script_path}")
        return script_path
    
    def create_vscode_tasks(self) -> Path:
        """Create VS Code tasks.json for subagent integration"""
        vscode_dir = Path(".vscode")
        vscode_dir.mkdir(exist_ok=True)
        
        tasks_path = vscode_dir / "tasks.json"
        
        tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "SubAgent: Frontend Developer",
                    "type": "shell",
                    "command": "python3",
                    "args": [
                        "${workspaceFolder}/subagents/cli/subagent_cli.py",
                        "execute",
                        "frontend-developer",
                        "${input:frontendTask}"
                    ],
                    "group": "build",
                    "presentation": {
                        "reveal": "always",
                        "panel": "new"
                    }
                },
                {
                    "label": "SubAgent: Backend Developer",
                    "type": "shell",
                    "command": "python3",
                    "args": [
                        "${workspaceFolder}/subagents/cli/subagent_cli.py",
                        "execute",
                        "backend-developer",
                        "${input:backendTask}"
                    ],
                    "group": "build",
                    "presentation": {
                        "reveal": "always",
                        "panel": "new"
                    }
                },
                {
                    "label": "SubAgent: Code Review",
                    "type": "shell",
                    "command": "python3",
                    "args": [
                        "${workspaceFolder}/subagents/cli/subagent_cli.py",
                        "execute",
                        "code-reviewer",
                        "Review the current changes"
                    ],
                    "group": "test",
                    "presentation": {
                        "reveal": "always",
                        "panel": "new"
                    }
                },
                {
                    "label": "SubAgent: List All",
                    "type": "shell",
                    "command": "python3",
                    "args": [
                        "${workspaceFolder}/subagents/cli/subagent_cli.py",
                        "list"
                    ],
                    "group": "none",
                    "presentation": {
                        "reveal": "always",
                        "panel": "new"
                    }
                }
            ],
            "inputs": [
                {
                    "id": "frontendTask",
                    "type": "promptString",
                    "description": "Enter the frontend development task"
                },
                {
                    "id": "backendTask",
                    "type": "promptString",
                    "description": "Enter the backend development task"
                }
            ]
        }
        
        with open(tasks_path, 'w') as f:
            json.dump(tasks, f, indent=2)
        
        print(f"Created VS Code tasks: {tasks_path}")
        return tasks_path
    
    def create_git_hooks(self) -> Path:
        """Create git hooks for automatic code review"""
        hooks_dir = Path(".git/hooks")
        if not hooks_dir.exists():
            hooks_dir = Path("hooks")  # Fallback for testing
            hooks_dir.mkdir(exist_ok=True)
        
        pre_commit_path = hooks_dir / "pre-commit"
        
        hook_content = """#!/bin/bash
# Pre-commit hook for Claude Code SubAgent code review

echo "Running automated code review..."

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py|js|ts|jsx|tsx)$')

if [ -z "$STAGED_FILES" ]; then
    echo "No code files to review"
    exit 0
fi

# Run code review subagent
python3 subagents/cli/subagent_cli.py execute code-reviewer "Review staged files: $STAGED_FILES"

# Check if review passed
if [ $? -ne 0 ]; then
    echo "Code review failed. Please address the issues before committing."
    exit 1
fi

echo "Code review passed!"
exit 0
"""
        
        with open(pre_commit_path, 'w') as f:
            f.write(hook_content)
        
        # Make hook executable
        pre_commit_path.chmod(0o755)
        
        print(f"Created git hook: {pre_commit_path}")
        return pre_commit_path
    
    def create_makefile(self) -> Path:
        """Create Makefile for common subagent tasks"""
        makefile_path = self.subagents_dir / "Makefile"
        
        makefile_content = """# Claude Code SubAgents Makefile

.PHONY: help list create-all test-frontend test-backend review clean

help:
\t@echo "Claude Code SubAgents - Available commands:"
\t@echo "  make list          - List all available subagents"
\t@echo "  make create-all    - Create all subagent files"
\t@echo "  make test-frontend - Test frontend developer subagent"
\t@echo "  make test-backend  - Test backend developer subagent"
\t@echo "  make review        - Run code review subagent"
\t@echo "  make clean         - Clean generated files"

list:
\tpython3 cli/subagent_cli.py list

create-all:
\tpython3 cli/subagent_cli.py create-all

test-frontend:
\tpython3 cli/subagent_cli.py execute frontend-developer "Create a simple React component"

test-backend:
\tpython3 cli/subagent_cli.py execute backend-developer "Create a REST API endpoint"

review:
\tpython3 cli/subagent_cli.py execute code-reviewer "Review recent changes"

clean:
\trm -rf output/*.md
\t@echo "Cleaned generated files"

# Workflow targets
workflow-fullstack:
\t@echo "Running full-stack development workflow..."
\tpython3 cli/subagent_cli.py execute frontend-developer "Create frontend components"
\tpython3 cli/subagent_cli.py execute backend-developer "Create API endpoints"
\tpython3 cli/subagent_cli.py execute api-developer "Document API"
\tpython3 cli/subagent_cli.py execute test-automation-engineer "Create tests"

workflow-deploy:
\t@echo "Running deployment workflow..."
\tpython3 cli/subagent_cli.py execute security-engineer "Security audit"
\tpython3 cli/subagent_cli.py execute performance-engineer "Performance optimization"
\tpython3 cli/subagent_cli.py execute devops-engineer "Deploy to production"
"""
        
        with open(makefile_path, 'w') as f:
            f.write(makefile_content)
        
        print(f"Created Makefile: {makefile_path}")
        return makefile_path

if __name__ == "__main__":
    # Test integrations
    print("Setting up workflow integrations...")
    
    workflow = WorkflowIntegration()
    
    # Create sample workflow
    workflow.create_workflow_script(
        "fullstack-development",
        ["frontend-developer", "backend-developer", "api-developer", "test-automation-engineer"]
    )
    
    # Create VS Code tasks
    workflow.create_vscode_tasks()
    
    # Create git hooks
    workflow.create_git_hooks()
    
    # Create Makefile
    workflow.create_makefile()
    
    print("\nIntegration setup complete!")