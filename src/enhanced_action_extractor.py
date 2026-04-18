#!/usr/bin/env python3
"""
Enhanced Action Extractor with Context-Aware Implementation Planning
Generates specific, implementable actions based on YOUR actual projects and codebase
"""

import json
import requests
import os
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

class EnhancedActionExtractor:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.api_base = "http://localhost:8091"
        
        # YOUR specific projects and their file structures
        self.projects = {
            "AgentForge": {
                "path": "/Users/cerion/Projects/AgentWorkspace/agentforge",
                "key_files": [
                    "backend/app/main.py",
                    "backend/app/core/agent_manager.py",
                    "backend/app/core/schema_designer.py",
                    "backend/app/core/app_builder.py",
                    "backend/app/api/dialogue_routes.py"
                ],
                "tech_stack": ["FastAPI", "React", "SQLAlchemy", "WebSocket"],
                "current_features": ["dialogue system", "schema designer", "progressive builder", "web crawler"]
            },
            "UMS": {
                "path": "/usr/local/share/universal-memory-system",
                "key_files": [
                    "src/api_service.py",
                    "src/article_triage.py",
                    "src/smart_article_validator.py",
                    "src/article_action_extractor.py",
                    "browser-extension/content-scripts/capture-interface.js",
                    "global-capture/main.swift"
                ],
                "tech_stack": ["FastAPI", "SQLite", "Swift", "JavaScript", "Browser Extension"],
                "current_features": ["memory storage", "article triage", "global capture", "browser extension"]
            },
            "Claude Integration": {
                "path": "/usr/local/share/universal-memory-system/galactica-agent",
                "key_files": [
                    "mcp_server.py",
                    "GALACTICA_CLAUDE.md"
                ],
                "tech_stack": ["MCP", "Claude Code", "Python"],
                "current_features": ["MCP tools", "persistent memory", "subagents"]
            }
        }
        
        # Your current goals and interests
        self.user_context = {
            "goals": [
                "Build AI agents that improve productivity",
                "Create seamless capture and retrieval systems",
                "Integrate Claude Code with memory systems",
                "Develop proactive AI assistants",
                "Automate knowledge management"
            ],
            "preferred_patterns": [
                "FastAPI endpoints for new features",
                "React components with TypeScript",
                "Swift for macOS native features",
                "Python scripts for automation",
                "Claude Code subagents for specialized tasks"
            ],
            "avoid": [
                "Complex ML models requiring training",
                "Services requiring paid APIs",
                "Technologies not in current stack",
                "Generic tutorials without specific application"
            ]
        }
    
    def extract_contextual_actions(self, article_content: str, article_metadata: Dict) -> Dict:
        """
        Extract actions that specifically relate to YOUR projects and can be implemented
        in YOUR codebase with YOUR tech stack
        """
        
        # Build context prompt with your specific information
        prompt = f"""
        You are analyzing an article for SPECIFIC implementation opportunities in these EXISTING projects:
        
        PROJECT CONTEXT:
        {json.dumps(self.projects, indent=2)}
        
        USER GOALS:
        {json.dumps(self.user_context['goals'], indent=2)}
        
        ARTICLE CONTENT:
        {article_content[:4000]}
        
        CRITICAL INSTRUCTIONS:
        1. ONLY suggest actions that modify EXISTING files listed above
        2. ONLY use technologies already in the tech stack
        3. Connect every action to a SPECIFIC project and file
        4. Provide EXACT file paths and function names
        5. Skip generic advice - only concrete modifications
        
        For each action, you MUST specify:
        - Which existing file to modify (full path)
        - What function/class to add or modify
        - How it integrates with existing code
        - Why it improves the current system
        
        RETURN JSON:
        {{
            "article_relevance_to_projects": {{
                "AgentForge": "How this relates to AgentForge",
                "UMS": "How this relates to UMS",
                "Claude_Integration": "How this relates to Claude integration"
            }},
            "specific_implementation_actions": [
                {{
                    "action_title": "Add [specific feature] to [specific file]",
                    "target_project": "AgentForge|UMS|Claude Integration",
                    "target_file": "/exact/path/to/file.py",
                    "modification_type": "add_function|modify_function|add_class|add_endpoint",
                    "specific_changes": {{
                        "function_name": "exact_function_name",
                        "location": "After line X or in class Y",
                        "code_snippet": "def new_function():\\n    # Actual code",
                        "integration_points": ["connects to X", "called by Y"]
                    }},
                    "improvement_rationale": "This improves [specific aspect] by [specific benefit]",
                    "estimated_complexity": "simple|moderate|complex",
                    "estimated_hours": 1-8,
                    "dependencies": ["what needs to exist first"],
                    "testing_approach": "How to test this change"
                }}
            ],
            "pattern_applications": [
                {{
                    "pattern_name": "Multi-agent coordination from CrewAI",
                    "apply_to": "AgentForge agent_manager.py",
                    "specific_implementation": "Add crew coordination to existing DialogueAgent class"
                }}
            ],
            "skip_reasons": [
                "Why certain aspects of the article don't apply to your projects"
            ],
            "immediate_win": {{
                "quickest_valuable_change": "The ONE change that would provide immediate value",
                "target_file": "/exact/path/to/file",
                "time_to_implement": "X hours",
                "expected_benefit": "Specific improvement you'll see"
            }}
        }}
        """
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                actions = json.loads(result.get('response', '{}'))
                
                # Validate and enhance the actions
                actions = self.validate_and_enhance_actions(actions, article_content)
                
                return actions
                
        except Exception as e:
            print(f"Error extracting contextual actions: {e}")
            return self.fallback_contextual_extraction(article_content)
    
    def validate_and_enhance_actions(self, actions: Dict, content: str) -> Dict:
        """
        Validate that suggested actions actually make sense for your projects
        """
        
        validated_actions = []
        
        for action in actions.get('specific_implementation_actions', []):
            # Check if target file actually exists
            target_file = action.get('target_file', '')
            if target_file and os.path.exists(target_file):
                action['file_exists'] = True
                
                # Add current file info
                if target_file.endswith('.py'):
                    try:
                        with open(target_file, 'r') as f:
                            lines = f.readlines()
                            action['current_file_lines'] = len(lines)
                            
                            # Find good insertion points
                            for i, line in enumerate(lines):
                                if 'class ' in line:
                                    action['suggested_insertion_line'] = i + 1
                                    break
                    except:
                        pass
                
                validated_actions.append(action)
            elif action.get('modification_type') == 'add_endpoint':
                # For new endpoints, we don't need existing file
                action['is_new_endpoint'] = True
                validated_actions.append(action)
        
        actions['specific_implementation_actions'] = validated_actions
        actions['validation_complete'] = True
        actions['validated_count'] = len(validated_actions)
        
        return actions
    
    def generate_implementation_ticket(self, action: Dict) -> str:
        """
        Generate a detailed implementation ticket for a specific action
        """
        
        ticket = f"""
# Implementation Ticket: {action['action_title']}

## Target
- **Project**: {action['target_project']}
- **File**: `{action['target_file']}`
- **Type**: {action['modification_type']}

## Specific Changes
"""
        
        if action.get('specific_changes'):
            changes = action['specific_changes']
            
            if changes.get('function_name'):
                ticket += f"- **Function**: `{changes['function_name']}`\n"
            
            if changes.get('location'):
                ticket += f"- **Location**: {changes['location']}\n"
            
            if changes.get('code_snippet'):
                ticket += f"\n### Code to Add:\n```python\n{changes['code_snippet']}\n```\n"
            
            if changes.get('integration_points'):
                ticket += f"\n### Integration Points:\n"
                for point in changes['integration_points']:
                    ticket += f"- {point}\n"
        
        ticket += f"""

## Rationale
{action.get('improvement_rationale', 'Improvement to system')}

## Implementation Details
- **Complexity**: {action.get('estimated_complexity', 'moderate')}
- **Estimated Time**: {action.get('estimated_hours', 2)} hours
- **File Exists**: {action.get('file_exists', False)}
"""
        
        if action.get('current_file_lines'):
            ticket += f"- **Current File Size**: {action['current_file_lines']} lines\n"
            
        if action.get('suggested_insertion_line'):
            ticket += f"- **Suggested Insert Point**: Line {action['suggested_insertion_line']}\n"
        
        if action.get('dependencies'):
            ticket += f"\n## Dependencies\n"
            for dep in action['dependencies']:
                ticket += f"- {dep}\n"
        
        if action.get('testing_approach'):
            ticket += f"\n## Testing Approach\n{action['testing_approach']}\n"
        
        ticket += f"""

## Commands to Start
```bash
# Open the target file
code {action.get('target_file', 'FILE_NOT_SPECIFIED')}

# Navigate to project
cd {self.get_project_path(action.get('target_project', ''))}

# Run tests after implementation
python -m pytest tests/
```

---
*Generated from article analysis at {datetime.now().isoformat()}*
"""
        
        return ticket
    
    def get_project_path(self, project_name: str) -> str:
        """Get the path for a project"""
        
        for name, info in self.projects.items():
            if project_name in name:
                return info['path']
        return "/path/to/project"
    
    def create_implementation_todos(self, actions: Dict, article_id: str) -> List[str]:
        """
        Create detailed TODOs with implementation tickets
        """
        
        todos_created = []
        
        # First, create the immediate win if it exists
        if actions.get('immediate_win'):
            win = actions['immediate_win']
            
            todo = {
                'title': f"🎯 QUICK WIN: {win['quickest_valuable_change']}",
                'file': win['target_file'],
                'time': win['time_to_implement'],
                'benefit': win['expected_benefit'],
                'priority': 10,
                'source_article': article_id
            }
            
            # Store in memory system
            self.store_enhanced_todo(todo)
            todos_created.append(todo['title'])
        
        # Then create specific implementation actions
        for action in actions.get('specific_implementation_actions', []):
            # Generate implementation ticket
            ticket = self.generate_implementation_ticket(action)
            
            # Save ticket to file
            ticket_file = f"/tmp/ticket_{article_id}_{len(todos_created)}.md"
            with open(ticket_file, 'w') as f:
                f.write(ticket)
            
            todo = {
                'title': action['action_title'],
                'project': action['target_project'],
                'file': action['target_file'],
                'complexity': action.get('estimated_complexity'),
                'hours': action.get('estimated_hours'),
                'ticket_file': ticket_file,
                'priority': 7,
                'source_article': article_id
            }
            
            self.store_enhanced_todo(todo)
            todos_created.append(action['action_title'])
            
            print(f"✅ Created TODO: {action['action_title']}")
            print(f"   📝 Ticket: {ticket_file}")
        
        return todos_created
    
    def store_enhanced_todo(self, todo: Dict):
        """Store enhanced TODO with implementation details"""
        
        try:
            response = requests.post(
                f"{self.api_base}/api/memory/store",
                json={
                    'content': json.dumps(todo, indent=2),
                    'category': 'todo',
                    'tags': [
                        'implementation-todo',
                        'auto-extracted',
                        'has-ticket',
                        todo.get('project', 'unknown').lower()
                    ],
                    'importance': todo.get('priority', 5),
                    'metadata': {
                        'todo_type': 'contextual_implementation',
                        'has_ticket': bool(todo.get('ticket_file')),
                        'target_file': todo.get('file'),
                        'estimated_hours': todo.get('hours', 0)
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"Error storing TODO: {e}")
    
    def fallback_contextual_extraction(self, content: str) -> Dict:
        """Fallback extraction based on keyword matching"""
        
        # Look for keywords that match your projects
        agentforge_keywords = ['agent', 'dialogue', 'schema', 'builder']
        ums_keywords = ['memory', 'capture', 'article', 'triage']
        claude_keywords = ['claude', 'mcp', 'subagent']
        
        content_lower = content.lower()
        
        relevance = {
            "AgentForge": "Not directly relevant",
            "UMS": "Not directly relevant", 
            "Claude_Integration": "Not directly relevant"
        }
        
        # Check relevance
        if any(kw in content_lower for kw in agentforge_keywords):
            relevance["AgentForge"] = "Contains agent-related concepts"
        if any(kw in content_lower for kw in ums_keywords):
            relevance["UMS"] = "Contains memory/capture concepts"
        if any(kw in content_lower for kw in claude_keywords):
            relevance["Claude_Integration"] = "Contains Claude/MCP concepts"
        
        return {
            "article_relevance_to_projects": relevance,
            "specific_implementation_actions": [],
            "pattern_applications": [],
            "skip_reasons": ["Could not extract specific implementations"],
            "validation_complete": False,
            "is_fallback": True
        }

async def analyze_article_with_context(article_id: str):
    """
    Analyze article with full context of user's projects
    """
    
    extractor = EnhancedActionExtractor()
    
    # Get article from memory
    response = requests.get(f"http://localhost:8091/api/memory/search?id={article_id}")
    
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            article = results[0]
            
            print(f"\n📄 Analyzing article with YOUR project context...")
            print(f"   ID: {article_id}")
            print(f"\n🔍 Checking relevance to your projects...")
            
            # Extract contextual actions
            actions = extractor.extract_contextual_actions(
                article.get('content', ''),
                article.get('metadata', {})
            )
            
            # Display relevance
            relevance = actions.get('article_relevance_to_projects', {})
            print(f"\n📊 Project Relevance:")
            for project, rel in relevance.items():
                print(f"   {project}: {rel}")
            
            # Display specific actions
            specific_actions = actions.get('specific_implementation_actions', [])
            if specific_actions:
                print(f"\n🎯 Specific Implementation Actions Found: {len(specific_actions)}")
                
                for i, action in enumerate(specific_actions, 1):
                    print(f"\n   {i}. {action['action_title']}")
                    print(f"      Target: {action['target_file']}")
                    print(f"      Complexity: {action.get('estimated_complexity')}")
                    print(f"      Time: {action.get('estimated_hours')} hours")
                
                # Create implementation TODOs
                todos = extractor.create_implementation_todos(actions, article_id)
                
                print(f"\n✅ Created {len(todos)} implementation TODOs with tickets")
                
                # Show immediate win
                if actions.get('immediate_win'):
                    win = actions['immediate_win']
                    print(f"\n⚡ IMMEDIATE WIN:")
                    print(f"   {win['quickest_valuable_change']}")
                    print(f"   Time: {win['time_to_implement']}")
                    print(f"   Benefit: {win['expected_benefit']}")
            else:
                print(f"\n📚 No specific implementations found for your projects")
                
                if actions.get('skip_reasons'):
                    print(f"\n❌ Skip Reasons:")
                    for reason in actions['skip_reasons']:
                        print(f"   - {reason}")

if __name__ == "__main__":
    import asyncio
    import sys
    
    if len(sys.argv) > 1:
        article_id = sys.argv[1]
    else:
        # Get most recent article
        response = requests.get("http://localhost:8091/api/memory/search?category=article&limit=1")
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                article_id = results[0]['id']
            else:
                print("No articles found")
                sys.exit(1)
    
    asyncio.run(analyze_article_with_context(article_id))