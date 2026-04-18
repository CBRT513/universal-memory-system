#!/usr/bin/env python3
"""
Claude Code SubAgent CLI - Command-line interface for managing subagents
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

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.subagent_manager import SubAgentManager

def simple_table(headers, rows, max_width=60):
    """Simple table formatter without external dependencies"""
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Limit description column width
    if len(col_widths) > 2:
        col_widths[-1] = min(col_widths[-1], max_width)
    
    # Print header
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))
    
    # Print rows
    for row in rows:
        formatted_row = []
        for i, (cell, width) in enumerate(zip(row, col_widths)):
            cell_str = str(cell)
            if i == len(row) - 1 and len(cell_str) > width:
                cell_str = cell_str[:width-3] + "..."
            formatted_row.append(cell_str.ljust(width))
        print(" | ".join(formatted_row))

class SubAgentCLI:
    """CLI for managing Claude Code SubAgents"""
    
    def __init__(self):
        self.manager = SubAgentManager()
    
    def list_agents(self, format: str = "table"):
        """List all available subagents"""
        agents = self.manager.list_templates()
        
        if format == "json":
            data = [
                {
                    "name": agent.name,
                    "description": agent.description,
                    "model": agent.model
                }
                for agent in agents
            ]
            print(json.dumps(data, indent=2))
        else:
            headers = ["Name", "Model", "Description"]
            rows = [
                [agent.name, agent.model, agent.description[:60] + "..." if len(agent.description) > 60 else agent.description]
                for agent in agents
            ]
            simple_table(headers, rows)
    
    def show_agent(self, name: str):
        """Show details of a specific agent"""
        agent = self.manager.get_template(name)
        if not agent:
            print(f"Error: Agent '{name}' not found")
            return 1
        
        print(f"Name: {agent.name}")
        print(f"Model: {agent.model}")
        print(f"Description: {agent.description}")
        print("\nInstructions:")
        print("-" * 50)
        print(agent.instructions)
        return 0
    
    def create_agent(self, name: str, output: Optional[str] = None):
        """Create a subagent file"""
        try:
            output_path = Path(output) if output else None
            created_path = self.manager.create_subagent_file(name, output_path)
            print(f"Successfully created subagent file: {created_path}")
            return 0
        except ValueError as e:
            print(f"Error: {e}")
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1
    
    def create_all(self):
        """Create all subagent files"""
        created = self.manager.create_all_subagents()
        print(f"\nSuccessfully created {len(created)} subagent files")
        print(f"Files saved to: {self.manager.output_dir}")
        return 0
    
    def recommend(self, task_type: str):
        """Recommend a model for a task type"""
        recommended = self.manager.recommend_model(task_type)
        model_info = self.manager.get_model_info(recommended)
        
        print(f"Recommended model for '{task_type}': {recommended}")
        if model_info:
            print(f"Model: {model_info.get('name', 'Unknown')}")
            print(f"Description: {model_info.get('description', 'No description')}")
            print(f"Max tokens: {model_info.get('max_tokens', 'Unknown')}")
        return 0
    
    def execute(self, agent_name: str, task: str, no_memory: bool = False):
        """Execute a subagent with a task"""
        print(f"Executing {agent_name} with task: {task}")
        print("-" * 50)
        
        result = self.manager.execute_subagent(
            agent_name, 
            task, 
            integrate_memory=not no_memory
        )
        
        print(result)
        return 0
    
    def create_custom(self, name: str, description: str, instructions_file: str, model: str = "sonnet"):
        """Create a custom subagent"""
        try:
            # Read instructions from file
            with open(instructions_file, 'r') as f:
                instructions = f.read()
            
            path = self.manager.create_custom_subagent(name, description, instructions, model)
            print(f"Successfully created custom subagent: {path}")
            return 0
        except FileNotFoundError:
            print(f"Error: Instructions file '{instructions_file}' not found")
            return 1
        except Exception as e:
            print(f"Error creating custom subagent: {e}")
            return 1
    
    def models(self):
        """List available models"""
        models = self.manager.models_config.get('models', {})
        
        headers = ["Model", "Name", "Max Tokens", "Recommended For"]
        rows = []
        
        for key, info in models.items():
            recommended = ", ".join(info.get('recommended_for', [])[:3])
            if len(info.get('recommended_for', [])) > 3:
                recommended += "..."
            
            rows.append([
                key,
                info.get('name', 'Unknown'),
                info.get('max_tokens', 'N/A'),
                recommended
            ])
        
        simple_table(headers, rows)
        return 0

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code SubAgent Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available subagents
  %(prog)s list
  
  # Show details of a specific subagent
  %(prog)s show frontend-developer
  
  # Create a subagent file
  %(prog)s create frontend-developer
  
  # Create all subagent files
  %(prog)s create-all
  
  # Get model recommendation for a task
  %(prog)s recommend backend
  
  # Execute a subagent (requires Claude Code CLI)
  %(prog)s execute python-developer "Create a FastAPI application"
  
  # List available models
  %(prog)s models
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all available subagents')
    list_parser.add_argument('--format', choices=['table', 'json'], default='table',
                            help='Output format')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show details of a specific subagent')
    show_parser.add_argument('name', help='Name of the subagent')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a subagent file')
    create_parser.add_argument('name', help='Name of the subagent')
    create_parser.add_argument('-o', '--output', help='Output file path')
    
    # Create all command
    subparsers.add_parser('create-all', help='Create all subagent files')
    
    # Recommend command
    recommend_parser = subparsers.add_parser('recommend', help='Recommend a model for a task')
    recommend_parser.add_argument('task_type', help='Type of task (e.g., backend, frontend, api)')
    
    # Execute command
    execute_parser = subparsers.add_parser('execute', help='Execute a subagent with a task')
    execute_parser.add_argument('agent', help='Name of the subagent')
    execute_parser.add_argument('task', help='Task to execute')
    execute_parser.add_argument('--no-memory', action='store_true',
                               help='Do not store results in memory system')
    
    # Create custom command
    custom_parser = subparsers.add_parser('create-custom', help='Create a custom subagent')
    custom_parser.add_argument('name', help='Name of the subagent')
    custom_parser.add_argument('description', help='Description of the subagent')
    custom_parser.add_argument('instructions_file', help='Path to instructions file')
    custom_parser.add_argument('--model', default='sonnet', help='Model to use')
    
    # Models command
    subparsers.add_parser('models', help='List available models')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = SubAgentCLI()
    
    if args.command == 'list':
        cli.list_agents(args.format)
    elif args.command == 'show':
        return cli.show_agent(args.name)
    elif args.command == 'create':
        return cli.create_agent(args.name, args.output)
    elif args.command == 'create-all':
        return cli.create_all()
    elif args.command == 'recommend':
        return cli.recommend(args.task_type)
    elif args.command == 'execute':
        return cli.execute(args.agent, args.task, args.no_memory)
    elif args.command == 'create-custom':
        return cli.create_custom(args.name, args.description, 
                                args.instructions_file, args.model)
    elif args.command == 'models':
        return cli.models()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())