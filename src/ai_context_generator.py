#!/usr/bin/env python3
"""
AI Context Generator - Generate standardized AI context messages
Part of Universal AI Memory System
"""


# Workspace configuration - automatically detect personal vs work
import sys
from pathlib import Path
sys.path.insert(0, '/usr/local/share/universal-memory-system')
try:
    from workspace_config import config
    # This automatically sets up the right database and port
    import os
    os.environ['MEMORY_API_PORT'] = str(config.api_port)
    os.environ['MEMORY_DB_PATH'] = config.database_path
except ImportError:
    pass  # Fallback to defaults if workspace config not available

import requests
import json
from datetime import datetime
import argparse
import pyperclip
import sys

class AIContextGenerator:
    def __init__(self, api_base="http://localhost:8091"):
        self.api_base = api_base
        
    def generate_context_message(self, task_description=None, include_memories=5):
        """Generate a comprehensive AI context message"""
        
        # Get system stats
        stats = self.get_stats()
        
        # Get recent memories
        recent_memories = self.get_recent_memories(limit=include_memories)
        
        # Get current working directory context
        import os
        current_dir = os.getcwd()
        project_name = os.path.basename(current_dir)
        
        # Get absolute path to AGENT.md
        import os
        agent_md_path = os.path.abspath("AGENT.md")
        project_root = os.path.dirname(agent_md_path)
        
        message = f"""I'm working on the Universal AI Memory System project. Please read the AGENT.md file to understand the system architecture and development patterns.

## Project Files & Context
• **AGENT.md Location**: `{agent_md_path}`
• **Project Root**: `{project_root}`
• **Current Directory**: `{current_dir}`
• **If you cannot access files**: This is a Universal AI Memory System (Encyclopedia Galactica for AI development) with components: Global Capture (macOS app), Memory API (FastAPI), Browser Extension, CLI tools, and GitHub integration.

## Project Context
• **System**: Universal AI Memory System (Encyclopedia Galactica for AI development)
• **Components**: Global Capture (macOS), Memory API, Browser Extension, CLI, GitHub Integration
• **Project**: {project_name}
• **Memory Stats**: {stats.get('total_memories', 0)} memories, {stats.get('sources', {}).get('global-capture', 0)} from Global Capture
• **API Status**: {'✅ Connected' if self.check_health() else '❌ Disconnected'}

## Quick Reference Commands
• **Build Global Capture**: `cd global-capture && ./build.sh && cd build && ./install.sh`
• **Start Memory API**: `python3 src/api_service.py --port 8091`
• **CLI Interface**: `python3 src/memory_cli.py <command>`
• **Health Check**: `curl http://localhost:8091/api/health`
• **AI Context**: `python3 src/ai_context_generator.py --copy`

## Recent Relevant Memories
{self.format_memories(recent_memories)}

## Architecture Summary (if AGENT.md not accessible)
This is a comprehensive memory system with:
- **Global Capture**: macOS app with ⌘⇧M hotkey for system-wide text capture
- **Memory API**: FastAPI service (localhost:8091) for storage/retrieval
- **Browser Extension**: Chrome/Firefox extension for web content capture
- **CLI Tools**: Command-line interface for memory management
- **GitHub Integration**: Repository analysis and code pattern extraction
- **AGENT.md Integration**: Universal format for AI tool compatibility

## Development Context
• **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• **API Base**: {self.api_base}
• **Available Tools**: Global Capture (⌘⇧M), Browser Extension, CLI, API

{f"Now I need help with: {task_description}" if task_description else "Now I need help with: [DESCRIBE YOUR TASK HERE]"}

Please read the AGENT.md file at the path above for complete context, or use the architecture summary if file access is unavailable."""
        
        return message
    
    def get_stats(self):
        """Get memory system statistics"""
        try:
            response = requests.get(f"{self.api_base}/api/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        return {}
    
    def get_recent_memories(self, limit=5):
        """Get recent memories from the system"""
        try:
            response = requests.get(f"{self.api_base}/api/search", 
                                  params={'limit': limit, 'sort': 'recent'}, 
                                  timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
        except requests.RequestException:
            pass
        return []
    
    def check_health(self):
        """Check if memory API is healthy"""
        try:
            response = requests.get(f"{self.api_base}/api/health", timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def format_memories(self, memories):
        """Format memories for display in context"""
        if not memories:
            return "• No recent memories found (check Memory API connection)"
        
        formatted = []
        for memory in memories:
            content = memory.get('content', 'No content')[:100]
            tags = ', '.join(memory.get('tags', []))
            source = memory.get('source', 'unknown')
            formatted.append(f"• {content}... [Source: {source}, Tags: {tags}]")
        
        return '\n'.join(formatted)

def main():
    parser = argparse.ArgumentParser(description='Generate AI context message for Universal Memory System')
    parser.add_argument('--task', '-t', help='Describe the task you need help with')
    parser.add_argument('--memories', '-m', type=int, default=5, help='Number of recent memories to include (default: 5)')
    parser.add_argument('--copy', '-c', action='store_true', help='Copy to clipboard')
    parser.add_argument('--api-base', default='http://localhost:8091', help='Memory API base URL')
    parser.add_argument('--output', '-o', help='Save to file instead of printing')
    
    args = parser.parse_args()
    
    generator = AIContextGenerator(api_base=args.api_base)
    
    print("🤖 Generating AI Context Message...")
    
    # Generate context message
    context_message = generator.generate_context_message(
        task_description=args.task,
        include_memories=args.memories
    )
    
    # Output handling
    if args.output:
        with open(args.output, 'w') as f:
            f.write(context_message)
        print(f"✅ AI context saved to {args.output}")
    elif args.copy:
        try:
            pyperclip.copy(context_message)
            print("✅ AI context copied to clipboard!")
            print("\n📋 Ready to paste into any AI chat")
        except Exception as e:
            print(f"❌ Failed to copy to clipboard: {e}")
            print("\n" + "="*50)
            print(context_message)
    else:
        print("\n" + "="*50)
        print(context_message)
        print("="*50)

if __name__ == "__main__":
    main()