#!/usr/bin/env python3
"""
Universal AI Memory System - Command Line Interface
Production-ready CLI with rich output and shell completion
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

import os
import sys
import json
import time
import subprocess
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
    from rich.syntax import Syntax
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Warning: Rich not available. Using basic output.")

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

# Import our memory service
from memory_service import get_memory_service, UniversalMemoryService

# Import GitHub integration
try:
    from github_integration import GitHubClient, GitHubKnowledgeSynthesizer
    HAS_GITHUB_INTEGRATION = True
except ImportError:
    HAS_GITHUB_INTEGRATION = False
    print("Warning: GitHub integration not available.")

# Configuration
console = Console() if HAS_RICH else None
SERVICE_PORT = 8091
SERVICE_HOST = "localhost"

class MemoryCLI:
    """Main CLI class with service management"""
    
    def __init__(self):
        self.service = None
        self.service_process = None
        self.config_path = Path.home() / ".ai-memory" / "cli_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load CLI configuration"""
        default_config = {
            "default_importance": 5,
            "max_search_results": 10,
            "auto_copy_context": True,
            "rich_output": HAS_RICH,
            "service_auto_start": True,
            "project_detection": True
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return {**default_config, **config}
            except:
                pass
        
        # Save default config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _save_config(self):
        """Save CLI configuration"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _get_service(self) -> UniversalMemoryService:
        """Get or create memory service"""
        if self.service is None:
            self.service = get_memory_service()
        return self.service
    
    def _print(self, text: str, style: Optional[str] = None):
        """Print with optional styling"""
        if HAS_RICH and console:
            if style:
                console.print(text, style=style)
            else:
                console.print(text)
        else:
            print(text)
    
    def _print_table(self, data: List[Dict], title: str = "", columns: Optional[List[str]] = None):
        """Print data as a table"""
        if not data:
            self._print("No data to display", "yellow")
            return
        
        if HAS_RICH and console:
            # Rich table
            if not columns:
                columns = list(data[0].keys())
            
            table = Table(title=title, show_header=True, header_style="bold magenta")
            for col in columns:
                table.add_column(col.replace('_', ' ').title())
            
            for row in data:
                table.add_row(*[str(row.get(col, '')) for col in columns])
            
            console.print(table)
        else:
            # Plain text table
            if title:
                print(f"\n{title}")
                print("=" * len(title))
            
            if not columns:
                columns = list(data[0].keys())
            
            # Header
            print(" | ".join(col.replace('_', ' ').title() for col in columns))
            print("-" * (sum(len(col) for col in columns) + len(columns) * 3))
            
            # Rows
            for row in data:
                print(" | ".join(str(row.get(col, ''))[:20] for col in columns))
    
    def _print_json(self, data: Any):
        """Print JSON with syntax highlighting"""
        json_str = json.dumps(data, indent=2, default=str)
        
        if HAS_RICH and console:
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            print(json_str)
    
    def _copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard"""
        if HAS_CLIPBOARD:
            try:
                pyperclip.copy(text)
                return True
            except:
                pass
        return False
    
    def _format_memory_for_display(self, memory: Dict[str, Any]) -> Dict[str, str]:
        """Format memory for table display"""
        tags = ', '.join(memory.get('tags', []))
        content = memory['content']
        if len(content) > 80:
            content = content[:77] + "..."
        
        importance = "⭐" * memory.get('importance', 0) if HAS_RICH else f"{memory.get('importance', 0)}/10"
        
        return {
            'project': memory.get('project', '')[:15],
            'content': content,
            'tags': tags[:20],
            'importance': importance,
            'category': memory.get('category', '')[:12],
            'accessed': str(memory.get('access_count', 0))
        }

cli_instance = MemoryCLI()

@click.group()
@click.version_option(version="1.0.0")
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--config', help='Configuration file path')
def cli(verbose, config):
    """Universal AI Memory System - Never lose context again!
    
    This CLI helps you store, search, and retrieve memories from all your AI interactions.
    Perfect for maintaining context across different AI platforms and projects.
    """
    if verbose:
        os.environ['MEMORY_VERBOSE'] = '1'
    
    if config:
        cli_instance.config_path = Path(config)
        cli_instance.config = cli_instance._load_config()

# Core memory operations
@cli.command()
@click.argument('content')
@click.option('--project', '-p', help='Project name (auto-detected if not provided)')
@click.option('--category', '-c', 
              type=click.Choice(['solution', 'pattern', 'decision', 'insight', 'reference']),
              help='Memory category')
@click.option('--tags', '-t', help='Comma-separated tags')
@click.option('--importance', '-i', type=click.IntRange(1, 10), 
              default=None, help='Importance level (1-10)')
@click.option('--status', type=click.Choice(['active', 'working', 'testing', 'failed', 'deprecated']),
              default='active', help='Memory status')
@click.option('--protection', type=click.Choice(['normal', 'high', 'critical']),
              default='normal', help='Protection level')
@click.option('--source', '-s', help='Source (chatgpt, claude, manual, etc.)')
@click.option('--url', help='Source URL')
def remember(content, project, category, tags, importance, status, protection, source, url):
    """Store a memory in the system.
    
    Examples:
      memory remember "Use React.memo for expensive components" --tags react,performance
      memory remember "JWT auth working perfectly - don't change!" --status working --protection high
      memory remember "MongoDB too slow for our queries" --status failed --importance 8
    """
    try:
        service = cli_instance._get_service()
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
        
        # Use config default for importance if not specified
        if importance is None:
            importance = cli_instance.config.get('default_importance', 5)
        
        # Store memory
        result = service.store_memory(
            content=content,
            project=project,
            category=category,
            tags=tag_list,
            importance=importance,
            status=status,
            protection_level=protection,
            source=source,
            source_url=url
        )
        
        if result['status'] == 'duplicate':
            cli_instance._print("⚠️  Duplicate memory detected", "yellow")
            cli_instance._print(f"   Existing ID: {result['id']}")
        else:
            cli_instance._print("✅ Memory stored successfully!", "green")
            cli_instance._print(f"   ID: {result['id']}")
            if result.get('project'):
                cli_instance._print(f"   Project: {result['project']}")
            if result.get('category'):
                cli_instance._print(f"   Category: {result['category']}")
            if result.get('tags'):
                cli_instance._print(f"   Tags: {', '.join(result['tags'])}")
    
    except Exception as e:
        cli_instance._print(f"❌ Error storing memory: {e}", "red")
        sys.exit(1)

@cli.command()
@click.argument('query', required=False)
@click.option('--project', '-p', help='Filter by project (use "current" for auto-detect)')
@click.option('--category', '-c', 
              type=click.Choice(['solution', 'pattern', 'decision', 'insight', 'reference']),
              help='Filter by category')
@click.option('--tags', '-t', help='Filter by tags (comma-separated)')
@click.option('--importance', '-i', type=click.IntRange(1, 10), help='Minimum importance')
@click.option('--limit', '-l', type=int, help='Maximum results')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'markdown', 'plain']),
              default='table', help='Output format')
@click.option('--no-semantic', is_flag=True, help='Disable semantic search')
def search(query, project, category, tags, importance, limit, format, no_semantic):
    """Search memories with smart filters.
    
    Examples:
      memory search "database performance"
      memory search --project myapp --tags optimization
      memory search "authentication" --importance 8 --format markdown
      memory search --category solution --limit 5
    """
    try:
        service = cli_instance._get_service()
        
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
        
        # Use config default for limit if not specified
        if limit is None:
            limit = cli_instance.config.get('max_search_results', 10)
        
        # Search memories
        results = service.search_memories(
            query=query,
            project=project,
            category=category,
            tags=tag_list,
            min_importance=importance or 0,
            limit=limit,
            include_semantic=not no_semantic
        )
        
        if not results:
            cli_instance._print("No memories found matching your criteria", "yellow")
            return
        
        if format == 'table':
            # Format for table display
            table_data = [cli_instance._format_memory_for_display(memory) for memory in results]
            cli_instance._print_table(table_data, f"Search Results ({len(results)} found)")
        
        elif format == 'json':
            cli_instance._print_json(results)
        
        elif format == 'markdown':
            output = f"# Search Results: {query or 'All Memories'}\n\n"
            for i, memory in enumerate(results, 1):
                tags = ', '.join(memory.get('tags', []))
                importance = '⭐' * memory.get('importance', 0)
                
                output += f"## {i}. {memory.get('project', 'General')}\n"
                output += f"**Content**: {memory['content']}\n"
                output += f"**Category**: {memory.get('category', 'N/A')}\n"
                output += f"**Tags**: {tags}\n"
                output += f"**Importance**: {importance}\n"
                if memory.get('similarity_score', 0) > 0:
                    output += f"**Relevance**: {memory['similarity_score']:.3f}\n"
                output += f"**Date**: {datetime.fromtimestamp(memory['timestamp']).strftime('%Y-%m-%d')}\n\n---\n\n"
            
            if HAS_RICH and console:
                md = Markdown(output)
                console.print(md)
            else:
                print(output)
        
        elif format == 'plain':
            for i, memory in enumerate(results, 1):
                print(f"{i}. [{memory.get('project', 'General')}] {memory['content']}")
                print(f"   Tags: {', '.join(memory.get('tags', []))}")
                print(f"   Importance: {memory.get('importance', 0)}/10")
                print()
    
    except Exception as e:
        cli_instance._print(f"❌ Error searching memories: {e}", "red")
        sys.exit(1)

@cli.command()
@click.option('--relevant-to', '-r', help='Generate context relevant to this query')
@click.option('--project', '-p', help='Project context (auto-detect if not provided)')
@click.option('--tokens', '-t', type=int, default=4000, help='Maximum context tokens')
@click.option('--copy', '-c', is_flag=True, help='Copy context to clipboard')
@click.option('--format', '-f', type=click.Choice(['markdown', 'plain']), 
              default='markdown', help='Output format')
@click.option('--no-protection', is_flag=True, help='Disable protection-aware context')
@click.option('--no-cross-project', is_flag=True, help='Disable cross-project insights')
def context(relevant_to, project, tokens, copy, format, no_protection, no_cross_project):
    """Generate intelligent context for AI conversations.
    
    Examples:
      memory context --relevant-to "React performance" --copy
      memory context --project myapp --tokens 2000
      memory context --relevant-to "authentication issues" --format plain
    """
    try:
        service = cli_instance._get_service()
        
        # Generate context
        context_text = service.get_context(
            relevant_to=relevant_to,
            project=project,
            max_tokens=tokens,
            include_cross_project=not no_cross_project,
            protection_aware=not no_protection
        )
        
        if copy and cli_instance.config.get('auto_copy_context', True):
            if cli_instance._copy_to_clipboard(context_text):
                cli_instance._print("✅ Context copied to clipboard!", "green")
            else:
                cli_instance._print("⚠️  Could not copy to clipboard", "yellow")
        
        # Display context
        if HAS_RICH and console and format == 'markdown':
            md = Markdown(context_text)
            panel = Panel(md, title="AI Context", border_style="blue")
            console.print(panel)
        else:
            print(context_text)
    
    except Exception as e:
        cli_instance._print(f"❌ Error generating context: {e}", "red")
        sys.exit(1)

@cli.command(name='ai-context')
@click.option('--question', '-q', help='Your question for the AI')
@click.option('--ai', type=click.Choice(['chatgpt', 'claude', 'generic']), 
              default='generic', help='AI platform')
@click.option('--project', '-p', help='Project context')
@click.option('--copy', '-c', is_flag=True, help='Copy prompt to clipboard')
def ai_context(question, ai, project, copy):
    """Generate complete AI prompt with context.
    
    Examples:
      memory ai-context --question "How to optimize database queries?" --ai chatgpt --copy
      memory ai-context -q "React performance issues" --ai claude
    """
    if not question:
        if HAS_RICH:
            question = Prompt.ask("What's your question for the AI?")
        else:
            question = input("What's your question for the AI? ")
    
    try:
        service = cli_instance._get_service()
        
        # Get context
        context_text = service.get_context(
            relevant_to=question,
            project=project,
            max_tokens=3000
        )
        
        # Format for AI platform
        if ai == 'chatgpt':
            prompt = f"""I'm working on a project and have some relevant context from my previous work:

{context_text}

Current question: {question}"""
        
        elif ai == 'claude':
            prompt = f"""I'm working on a project and have some relevant context from my previous solutions:

{context_text}

Please help me with: {question}"""
        
        else:  # generic
            prompt = f"""Context from my previous work:

{context_text}

Question: {question}"""
        
        if copy:
            if cli_instance._copy_to_clipboard(prompt):
                cli_instance._print("✅ AI prompt copied to clipboard! Paste it into your AI chat.", "green")
            else:
                cli_instance._print("⚠️  Could not copy to clipboard", "yellow")
        else:
            if HAS_RICH and console:
                panel = Panel(prompt, title=f"Prompt for {ai.upper()}", border_style="green")
                console.print(panel)
            else:
                print(f"=== Prompt for {ai.upper()} ===")
                print(prompt)
    
    except Exception as e:
        cli_instance._print(f"❌ Error generating AI prompt: {e}", "red")
        sys.exit(1)

@cli.command()
@click.argument('content')
@click.option('--limit', '-l', type=int, default=10, help='Maximum related memories')
@click.option('--cross-project', is_flag=True, help='Search across all projects')
@click.option('--threshold', type=float, default=0.5, help='Minimum similarity threshold')
def relate(content, limit, cross_project, threshold):
    """Find memories related to given content.
    
    Examples:
      memory relate "React component optimization" --limit 5
      memory relate "database performance" --cross-project
    """
    try:
        service = cli_instance._get_service()
        
        related = service.find_related_memories(
            content=content,
            limit=limit,
            cross_project=cross_project
        )
        
        # Filter by threshold
        related = [r for r in related if r.get('similarity_score', 0) >= threshold]
        
        if not related:
            cli_instance._print("No related memories found", "yellow")
            return
        
        cli_instance._print(f"Found {len(related)} related memories:\n", "bold")
        
        for i, memory in enumerate(related, 1):
            similarity = memory.get('similarity_score', 0)
            tags = ', '.join(memory.get('tags', []))
            
            cli_instance._print(f"{i}. [{memory['project']}] {memory['content'][:100]}...")
            cli_instance._print(f"   Tags: {tags} | Similarity: {similarity:.3f}")
            cli_instance._print("")
    
    except Exception as e:
        cli_instance._print(f"❌ Error finding related memories: {e}", "red")
        sys.exit(1)

# Quick alias for search
@cli.command()
@click.argument('query')
@click.option('--limit', '-l', type=int, default=5, help='Maximum results')
@click.option('--tag', '-t', help='Filter by single tag')
def recall(query, limit, tag):
    """Quick search for memories (alias for search).
    
    Examples:
      memory recall "database optimization"
      memory recall "authentication" --tag security
    """
    try:
        service = cli_instance._get_service()
        
        tag_list = [tag] if tag else None
        
        results = service.search_memories(
            query=query,
            tags=tag_list,
            limit=limit
        )
        
        if not results:
            cli_instance._print("No memories found", "yellow")
            return
        
        for i, memory in enumerate(results, 1):
            cli_instance._print(f"{i}. [{memory.get('project', 'General')}] {memory['content']}")
            if memory.get('tags'):
                cli_instance._print(f"   Tags: {', '.join(memory['tags'])}")
            if memory.get('similarity_score', 0) > 0:
                cli_instance._print(f"   Relevance: {memory['similarity_score']:.3f}")
            cli_instance._print("")
    
    except Exception as e:
        cli_instance._print(f"❌ Error recalling memories: {e}", "red")
        sys.exit(1)

# System management commands
@cli.command()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--project', '-p', help='Statistics for specific project')
def stats(output_json, project):
    """Show memory system statistics.
    
    Examples:
      memory stats
      memory stats --project myapp --json
    """
    try:
        service = cli_instance._get_service()
        statistics = service.get_statistics()
        
        if output_json:
            cli_instance._print_json(statistics)
            return
        
        # Pretty print stats
        overall = statistics['overall']
        
        if HAS_RICH and console:
            panel_content = f"""[bold cyan]Universal AI Memory Statistics[/bold cyan]

📊 Total Memories: {overall['total_memories']}
📁 Total Projects: {overall['total_projects']}
⭐ Average Importance: {overall['avg_importance']}
👁  Total Accesses: {overall['total_accesses']}
🔧 Embedding Provider: {overall['embedding_provider'] or 'None'}
🔍 Vector Search: {'✅ Enabled' if overall['vector_search_enabled'] else '❌ Disabled'}
💾 Storage Path: {overall['storage_path']}"""
            
            panel = Panel(panel_content, border_style="blue")
            console.print(panel)
            
            # Project breakdown
            if statistics.get('projects'):
                table = Table(title="Projects", show_header=True)
                table.add_column("Project", style="cyan")
                table.add_column("Memories", style="yellow")
                table.add_column("Avg Importance", style="green")
                table.add_column("Last Activity", style="magenta")
                
                for proj_name, proj_data in statistics['projects'].items():
                    table.add_row(
                        proj_name,
                        str(proj_data['count']),
                        str(proj_data['avg_importance']),
                        proj_data['last_activity'][:10]  # Date only
                    )
                
                console.print(table)
            
            # Most accessed
            if statistics.get('most_accessed'):
                console.print("\n[bold]Most Accessed Memories:[/bold]")
                for memory in statistics['most_accessed'][:3]:
                    console.print(f"  • [{memory['project']}] {memory['content']} (accessed {memory['access_count']} times)")
        
        else:
            # Plain text output
            print("Universal AI Memory Statistics")
            print("=" * 35)
            print(f"Total Memories: {overall['total_memories']}")
            print(f"Total Projects: {overall['total_projects']}")
            print(f"Average Importance: {overall['avg_importance']}")
            print(f"Total Accesses: {overall['total_accesses']}")
            print(f"Storage Path: {overall['storage_path']}")
            
            if statistics.get('projects'):
                print("\nProjects:")
                for proj_name, proj_data in statistics['projects'].items():
                    print(f"  {proj_name}: {proj_data['count']} memories")
    
    except Exception as e:
        cli_instance._print(f"❌ Error getting statistics: {e}", "red")
        sys.exit(1)

@cli.command()
def projects():
    """List all projects with statistics."""
    try:
        service = cli_instance._get_service()
        project_data = service.get_projects()
        
        projects = project_data['projects']
        current = project_data.get('current_project')
        
        if not projects:
            cli_instance._print("No projects found", "yellow")
            return
        
        if HAS_RICH and console:
            table = Table(title="Projects", show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("Memories", style="yellow")
            table.add_column("Avg Importance", style="green")
            table.add_column("Last Activity", style="magenta")
            table.add_column("Current", style="bold red")
            
            for project in projects:
                is_current = "✓" if project['name'] == current else ""
                last_activity = project['last_activity'][:10]  # Date only
                
                table.add_row(
                    project['name'],
                    str(project['memory_count']),
                    str(project['avg_importance']),
                    last_activity,
                    is_current
                )
            
            console.print(table)
        
        else:
            print("Projects:")
            print("-" * 50)
            for project in projects:
                current_marker = " (current)" if project['name'] == current else ""
                print(f"{project['name']}{current_marker}: {project['memory_count']} memories")
    
    except Exception as e:
        cli_instance._print(f"❌ Error listing projects: {e}", "red")
        sys.exit(1)

@cli.command()
@click.option('--format', '-f', type=click.Choice(['json', 'markdown', 'chatgpt', 'claude']),
              default='markdown', help='Export format')
@click.option('--project', '-p', help='Filter by project')
@click.option('--category', '-c', help='Filter by category')
@click.option('--output', '-o', help='Output file (stdout if not specified)')
@click.option('--limit', '-l', type=int, help='Maximum items to export')
def export(format, project, category, output, limit):
    """Export memories in various formats.
    
    Examples:
      memory export --format json --output backup.json
      memory export --project myapp --format markdown
      memory export --format chatgpt --limit 20 --output context.txt
    """
    try:
        service = cli_instance._get_service()
        
        exported_data = service.export_memories(
            format=format,
            project=project,
            category=category,
            limit=limit
        )
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(exported_data)
            cli_instance._print(f"✅ Exported to {output}", "green")
        else:
            print(exported_data)
    
    except Exception as e:
        cli_instance._print(f"❌ Error exporting memories: {e}", "red")
        sys.exit(1)

@cli.command()
@click.option('--duplicates', is_flag=True, help='Remove duplicate memories')
@click.option('--old', is_flag=True, help='Remove old memories')
@click.option('--days', type=int, default=365, help='Days threshold for old memories')
@click.option('--unused', is_flag=True, help='Remove unused memories')
@click.option('--access-threshold', type=int, default=0, help='Access count threshold')
@click.option('--dry-run', is_flag=True, help='Show what would be removed without removing')
def cleanup(duplicates, old, days, unused, access_threshold, dry_run):
    """Clean up memories based on various criteria.
    
    Examples:
      memory cleanup --duplicates --dry-run
      memory cleanup --old --days 180
      memory cleanup --unused --access-threshold 1
    """
    if not any([duplicates, old, unused]):
        cli_instance._print("Please specify at least one cleanup option", "yellow")
        return
    
    if dry_run:
        cli_instance._print("DRY RUN - No changes will be made", "yellow")
    
    try:
        service = cli_instance._get_service()
        
        if not dry_run:
            if HAS_RICH:
                confirm = Confirm.ask("Are you sure you want to proceed with cleanup?")
            else:
                confirm = input("Are you sure you want to proceed with cleanup? (y/N): ").lower() == 'y'
            
            if not confirm:
                cli_instance._print("Cleanup cancelled", "yellow")
                return
        
        if not dry_run:
            removed = service.cleanup_memories(
                remove_duplicates=duplicates,
                remove_old=old,
                days_threshold=days,
                remove_unused=unused,
                access_threshold=access_threshold
            )
            
            cli_instance._print("Cleanup completed:", "green")
            if duplicates:
                cli_instance._print(f"  Duplicates removed: {removed['duplicates']}")
            if old:
                cli_instance._print(f"  Old memories removed: {removed['old']}")
            if unused:
                cli_instance._print(f"  Unused memories removed: {removed['unused']}")
        else:
            cli_instance._print("Dry run completed - use without --dry-run to perform cleanup", "yellow")
    
    except Exception as e:
        cli_instance._print(f"❌ Error during cleanup: {e}", "red")
        sys.exit(1)

@cli.command()
@click.option('--destination', '-d', help='Backup destination directory')
def backup(destination):
    """Create a backup of the memory database.
    
    Examples:
      memory backup
      memory backup --destination /path/to/backups/
    """
    try:
        service = cli_instance._get_service()
        
        backup_file = service.backup_database(destination)
        cli_instance._print(f"✅ Backup created: {backup_file}", "green")
    
    except Exception as e:
        cli_instance._print(f"❌ Error creating backup: {e}", "red")
        sys.exit(1)

@cli.command()
def doctor():
    """Run comprehensive system diagnostics."""
    try:
        service = cli_instance._get_service()
        health = service.health_check()
        
        if HAS_RICH and console:
            # Status indicator
            if health['status'] == 'healthy':
                status_text = "[green]🟢 Healthy[/green]"
            elif health['status'] == 'degraded':
                status_text = "[yellow]🟡 Degraded[/yellow]"
            else:
                status_text = "[red]🔴 Unhealthy[/red]"
            
            console.print(f"\nSystem Status: {status_text}\n")
            
            # Checks
            console.print("[bold]Component Status:[/bold]")
            for component, status in health['checks'].items():
                if status == 'ok':
                    console.print(f"  ✅ {component.replace('_', ' ').title()}")
                elif status == 'warning':
                    console.print(f"  ⚠️  {component.replace('_', ' ').title()}")
                else:
                    console.print(f"  ❌ {component.replace('_', ' ').title()}")
            
            # Warnings
            if health['warnings']:
                console.print(f"\n[yellow]Warnings:[/yellow]")
                for warning in health['warnings']:
                    console.print(f"  • {warning}")
            
            # Errors
            if health['errors']:
                console.print(f"\n[red]Errors:[/red]")
                for error in health['errors']:
                    console.print(f"  • {error}")
        
        else:
            print(f"System Status: {health['status']}")
            print("\nComponent Status:")
            for component, status in health['checks'].items():
                print(f"  {component}: {status}")
            
            if health['warnings']:
                print("\nWarnings:")
                for warning in health['warnings']:
                    print(f"  - {warning}")
            
            if health['errors']:
                print("\nErrors:")
                for error in health['errors']:
                    print(f"  - {error}")
    
    except Exception as e:
        cli_instance._print(f"❌ Error running diagnostics: {e}", "red")
        sys.exit(1)

# Configuration management
@cli.command()
@click.option('--key', help='Configuration key to get/set')
@click.option('--value', help='Value to set (omit to get current value)')
@click.option('--list', 'list_all', is_flag=True, help='List all configuration options')
def config(key, value, list_all):
    """Manage CLI configuration.
    
    Examples:
      memory config --list
      memory config --key default_importance --value 7
      memory config --key auto_copy_context
    """
    if list_all:
        cli_instance._print("Current Configuration:", "bold")
        for k, v in cli_instance.config.items():
            cli_instance._print(f"  {k}: {v}")
        return
    
    if not key:
        cli_instance._print("Please specify --key or use --list", "yellow")
        return
    
    if value is not None:
        # Set value
        try:
            # Try to parse as JSON for booleans, numbers, etc.
            parsed_value = json.loads(value)
        except:
            # Fall back to string
            parsed_value = value
        
        cli_instance.config[key] = parsed_value
        cli_instance._save_config()
        cli_instance._print(f"✅ Set {key} = {parsed_value}", "green")
    else:
        # Get value
        if key in cli_instance.config:
            cli_instance._print(f"{key}: {cli_instance.config[key]}")
        else:
            cli_instance._print(f"Configuration key '{key}' not found", "yellow")

# Global Capture Commands
@cli.group()
def capture():
    """Global Capture Service management commands."""
    pass

# Article Triage Commands
@cli.group()
def article():
    """Article triage and management commands."""
    pass

@article.command('analyze')
@click.argument('content', required=False)
@click.option('--file', '-f', help='Read article from file')
@click.option('--url', '-u', help='Fetch article from URL')
@click.option('--quick', is_flag=True, help='Use quick analysis mode')
def article_analyze(content, file, url, quick):
    """Analyze an article without storing it.
    
    Examples:
      memory article analyze "Article content here..."
      memory article analyze --file article.txt
      memory article analyze --url https://example.com/article
    """
    try:
        # Get content from various sources
        if file:
            with open(file, 'r') as f:
                content = f.read()
        elif url:
            cli_instance._print(f"Fetching article from {url}...", "yellow")
            # Simple URL fetch (could be enhanced)
            import urllib.request
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
        elif not content:
            cli_instance._print("Please provide content, --file, or --url", "red")
            return
        
        # Import article triage module
        from article_triage import get_triage_service
        triage_service = get_triage_service()
        
        cli_instance._print("Analyzing article...", "yellow")
        
        # Run analysis
        import asyncio
        result = asyncio.run(triage_service.triage_content(
            content=content,
            metadata={'quick_mode': quick}
        ))
        
        if not result.get('is_article'):
            cli_instance._print(f"Content detected as: {result.get('content_type')}", "yellow")
            return
        
        analysis = result['analysis']
        metadata = result['metadata']
        recommendations = result['recommendations']
        
        # Display results
        if HAS_RICH and console:
            # Title
            console.print(f"\n[bold cyan]{analysis.get('title', 'Untitled Article')}[/bold cyan]")
            console.print(f"[dim]By {analysis.get('author', 'Unknown')} | {metadata.get('reading_time_minutes', '?')} min read[/dim]\n")
            
            # Summary
            if analysis.get('summary'):
                console.print(Panel(analysis['summary'], title="Summary", border_style="blue"))
            
            # Scores
            table = Table(show_header=False, box=None)
            table.add_row("Classification:", f"[bold]{analysis.get('classification', 'unknown')}[/bold]")
            table.add_row("Actionability:", f"{analysis.get('actionability_score', 0)}/10")
            table.add_row("Relevance:", f"{analysis.get('relevance_score', 0)}/10")
            table.add_row("Priority:", f"[{recommendations.get('priority', 'normal')}]{recommendations.get('priority', 'normal')}[/{recommendations.get('priority', 'normal')}]")
            console.print(table)
            
            # Key Topics
            if analysis.get('key_topics'):
                console.print("\n[bold]Key Topics:[/bold]")
                for topic in analysis['key_topics']:
                    console.print(f"  • {topic}")
            
            # Technologies
            if analysis.get('technologies'):
                console.print("\n[bold]Technologies:[/bold]")
                console.print(" ".join([f"[cyan]#{tech}[/cyan]" for tech in analysis['technologies']]))
            
            # Action Items
            if analysis.get('action_items'):
                console.print("\n[bold]Action Items:[/bold]")
                for item in analysis['action_items']:
                    console.print(f"  ☐ {item}")
            
            # Recommendations
            if recommendations.get('next_actions'):
                console.print("\n[bold]Recommended Next Steps:[/bold]")
                for action in recommendations['next_actions']:
                    console.print(f"  → {action}")
        
        else:
            # Plain text output
            print(f"\nTitle: {analysis.get('title', 'Untitled')}")
            print(f"Author: {analysis.get('author', 'Unknown')}")
            print(f"Reading Time: {metadata.get('reading_time_minutes', '?')} minutes")
            print(f"\nSummary: {analysis.get('summary', 'N/A')}")
            print(f"\nClassification: {analysis.get('classification')}")
            print(f"Actionability: {analysis.get('actionability_score')}/10")
            print(f"Relevance: {analysis.get('relevance_score')}/10")
            
            if analysis.get('key_topics'):
                print("\nKey Topics:")
                for topic in analysis['key_topics']:
                    print(f"  - {topic}")
            
            if analysis.get('action_items'):
                print("\nAction Items:")
                for item in analysis['action_items']:
                    print(f"  - {item}")
    
    except Exception as e:
        cli_instance._print(f"❌ Error analyzing article: {e}", "red")

@article.command('triage')
@click.argument('content', required=False)
@click.option('--file', '-f', help='Read article from file')
@click.option('--url', '-u', help='Fetch article from URL')
@click.option('--project', '-p', help='Project to assign')
@click.option('--tags', '-t', help='Additional tags (comma-separated)')
def article_triage(content, file, url, project, tags):
    """Triage and store an article with intelligent analysis.
    
    Examples:
      memory article triage "Article content..." --project ai-tools
      memory article triage --file article.md --tags "react,hooks"
    """
    try:
        # Get content
        if file:
            with open(file, 'r') as f:
                content = f.read()
        elif url:
            import urllib.request
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
        elif not content:
            cli_instance._print("Please provide content, --file, or --url", "red")
            return
        
        service = cli_instance._get_service()
        
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
        
        cli_instance._print("Triaging article...", "yellow")
        
        # Use the API's article triage functionality
        from article_triage import get_triage_service
        triage_service = get_triage_service(service.db_path)
        
        import asyncio
        triage_result = asyncio.run(triage_service.triage_content(
            content=content,
            metadata={'source': 'cli', 'source_url': url}
        ))
        
        if not triage_result.get('is_article'):
            # Store as regular memory
            result = service.store_memory(
                content=content,
                project=project,
                category=triage_result.get('content_type', 'note'),
                tags=tag_list
            )
            cli_instance._print(f"✅ Stored as {triage_result.get('content_type')}: {result['id']}", "green")
            return
        
        # Store with article metadata
        analysis = triage_result['analysis']
        recommendations = triage_result['recommendations']
        
        # Combine tags
        all_tags = list(set(
            (tag_list or []) +
            recommendations.get('suggested_tags', []) +
            ['article', analysis.get('classification', 'reference')]
        ))
        
        result = service.store_memory(
            content=content,
            project=project,
            category='article',
            tags=all_tags,
            importance=max(
                analysis.get('actionability_score', 5),
                analysis.get('relevance_score', 5)
            ),
            source='article_cli',
            source_url=url,
            metadata={
                'article_analysis': analysis,
                'recommendations': recommendations
            }
        )
        
        # Store article metadata
        triage_service.store_article_metadata(result['id'], triage_result)
        
        cli_instance._print(f"✅ Article triaged and stored: {result['id']}", "green")
        cli_instance._print(f"   Title: {analysis.get('title', 'Untitled')}", "dim")
        cli_instance._print(f"   Classification: {analysis.get('classification')}", "dim")
        cli_instance._print(f"   Priority: {recommendations.get('priority')}", "dim")
    
    except Exception as e:
        cli_instance._print(f"❌ Error triaging article: {e}", "red")

@article.command('actionable')
@click.option('--limit', '-l', default=10, help='Number of articles to show')
def article_actionable(limit):
    """List actionable articles (implement_now classification).
    
    Example:
      memory article actionable --limit 5
    """
    try:
        from article_triage import get_triage_service
        service = cli_instance._get_service()
        triage_service = get_triage_service(service.db_path)
        
        articles = triage_service.get_actionable_articles(limit)
        
        if not articles:
            cli_instance._print("No actionable articles found", "yellow")
            return
        
        if HAS_RICH and console:
            console.print(f"\n[bold]Top {len(articles)} Actionable Articles:[/bold]\n")
            
            for article in articles:
                # Parse JSON fields
                action_items = article.get('action_items', [])
                if isinstance(action_items, str):
                    import json
                    try:
                        action_items = json.loads(action_items)
                    except:
                        action_items = []
                
                console.print(f"[bold cyan]{article.get('title', 'Untitled')}[/bold cyan]")
                console.print(f"  [dim]ID: {article['memory_id']} | Score: {article.get('actionability_score', 0)}/10[/dim]")
                console.print(f"  Classification: [bold]{article.get('classification', 'unknown')}[/bold]")
                
                if article.get('summary'):
                    console.print(f"  Summary: {article['summary'][:100]}...")
                
                if action_items:
                    console.print("  Action Items:")
                    for item in action_items[:3]:
                        console.print(f"    • {item}")
                
                console.print()
        else:
            print(f"\nTop {len(articles)} Actionable Articles:\n")
            
            for article in articles:
                print(f"Title: {article.get('title', 'Untitled')}")
                print(f"  ID: {article['memory_id']}")
                print(f"  Score: {article.get('actionability_score', 0)}/10")
                print(f"  Classification: {article.get('classification')}")
                print()
    
    except Exception as e:
        cli_instance._print(f"❌ Error getting actionable articles: {e}", "red")

@article.command('stats')
def article_stats():
    """Show article triage statistics.
    
    Example:
      memory article stats
    """
    try:
        from article_triage import get_triage_service
        service = cli_instance._get_service()
        triage_service = get_triage_service(service.db_path)
        
        stats = triage_service.get_article_stats()
        
        if HAS_RICH and console:
            console.print("\n[bold]Article Triage Statistics[/bold]\n")
            
            # Overview
            table = Table(show_header=False, box=None)
            table.add_row("Total Articles:", str(stats['total_articles']))
            table.add_row("Avg Actionability:", f"{stats['average_actionability']}/10")
            table.add_row("Avg Relevance:", f"{stats['average_relevance']}/10")
            table.add_row("Avg Reading Time:", f"{stats['average_reading_time']} min")
            console.print(table)
            
            # Classifications
            if stats.get('classifications'):
                console.print("\n[bold]By Classification:[/bold]")
                for cls, count in stats['classifications'].items():
                    console.print(f"  {cls}: {count}")
            
            # Top Technologies
            if stats.get('top_technologies'):
                console.print("\n[bold]Top Technologies:[/bold]")
                for tech, count in stats['top_technologies'][:10]:
                    console.print(f"  {tech}: {count}")
        
        else:
            print("\nArticle Triage Statistics\n")
            print(f"Total Articles: {stats['total_articles']}")
            print(f"Average Actionability: {stats['average_actionability']}/10")
            print(f"Average Relevance: {stats['average_relevance']}/10")
            print(f"Average Reading Time: {stats['average_reading_time']} minutes")
            
            if stats.get('classifications'):
                print("\nBy Classification:")
                for cls, count in stats['classifications'].items():
                    print(f"  {cls}: {count}")
    
    except Exception as e:
        cli_instance._print(f"❌ Error getting article stats: {e}", "red")

@article.command('plan')
@click.argument('memory_id', required=False)
@click.option('--all', 'generate_all', is_flag=True, help='Generate plans for all implement_now articles')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def article_plan(memory_id, generate_all, output_json):
    """Generate or view action plans for implement_now articles.
    
    Examples:
      memory article plan                    # View all existing plans
      memory article plan --all               # Generate plans for all implement_now articles
      memory article plan mem_12345          # Generate plan for specific article
    """
    try:
        from action_plan_generator import ActionPlanGenerator
        from article_triage import get_triage_service
        import sqlite3
        import json
        
        service = cli_instance._get_service()
        generator = ActionPlanGenerator(service.db_path)
        
        if not memory_id and not generate_all:
            # Show existing plans
            plans = generator.get_pending_action_plans()
            
            if output_json:
                print(json.dumps(plans, indent=2))
                return
            
            if not plans:
                cli_instance._print("No action plans found. Use --all to generate plans for implement_now articles.", "yellow")
                return
            
            cli_instance._print(f"\n📋 Found {len(plans)} action plans:\n", "green")
            for plan in plans:
                formatted = generator.format_action_plan(plan)
                print(formatted)
                print()
            return
        
        if generate_all:
            # Generate plans for all implement_now articles without plans
            with sqlite3.connect(service.db_path) as conn:
                cursor = conn.execute("""
                    SELECT am.memory_id, am.title, am.summary, am.action_items, 
                           am.technologies, am.actionability_score, am.relevance_score
                    FROM article_metadata am
                    LEFT JOIN action_plans ap ON am.memory_id = ap.memory_id
                    WHERE am.classification = 'implement_now' 
                      AND ap.id IS NULL
                    ORDER BY am.actionability_score DESC
                """)
                
                articles = cursor.fetchall()
                
                if not articles:
                    cli_instance._print("All implement_now articles already have action plans.", "green")
                    return
                
                cli_instance._print(f"Generating action plans for {len(articles)} articles...", "cyan")
                
                generated_plans = []
                for article in articles:
                    memory_id = article[0]
                    analysis = {
                        'title': article[1],
                        'summary': article[2],
                        'action_items': json.loads(article[3]) if article[3] else [],
                        'technologies': json.loads(article[4]) if article[4] else [],
                        'actionability_score': article[5],
                        'relevance_score': article[6]
                    }
                    
                    plan = generator.generate_action_plan(memory_id, analysis)
                    generated_plans.append(plan)
                    cli_instance._print(f"✅ Generated plan for: {article[1][:50]}...", "green")
                
                if output_json:
                    print(json.dumps(generated_plans, indent=2))
                else:
                    cli_instance._print(f"\n✨ Generated {len(generated_plans)} action plans!", "green")
                    cli_instance._print("Use 'memory article plan' to view all plans.", "cyan")
                
        elif memory_id:
            # Generate plan for specific article
            with sqlite3.connect(service.db_path) as conn:
                cursor = conn.execute("""
                    SELECT title, summary, action_items, technologies, 
                           actionability_score, relevance_score
                    FROM article_metadata
                    WHERE memory_id = ?
                """, (memory_id,))
                
                article = cursor.fetchone()
                
                if not article:
                    cli_instance._print(f"Article {memory_id} not found or not analyzed.", "red")
                    return
                
                analysis = {
                    'title': article[0],
                    'summary': article[1],
                    'action_items': json.loads(article[2]) if article[2] else [],
                    'technologies': json.loads(article[3]) if article[3] else [],
                    'actionability_score': article[4],
                    'relevance_score': article[5]
                }
                
                plan = generator.generate_action_plan(memory_id, analysis)
                
                if output_json:
                    print(json.dumps(plan, indent=2))
                else:
                    formatted = generator.format_action_plan(plan)
                    print(formatted)
        
    except Exception as e:
        cli_instance._print(f"❌ Error with action plans: {e}", "red")
        import traceback
        traceback.print_exc()

@capture.command('status')
def capture_status():
    """Check Global Capture Service status."""
    try:
        import subprocess
        import platform
        
        if platform.system() != 'Darwin':
            cli_instance._print("❌ Global Capture Service is only available on macOS", "red")
            return
        
        # Check if Global Capture is running
        result = subprocess.run(['pgrep', '-f', 'Universal Memory Capture'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            cli_instance._print("✅ Global Capture Service is running", "green")
            
            # Check menu bar integration
            ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'Universal Memory Capture' in ps_result.stdout:
                cli_instance._print("🧠 Menu bar integration active", "green")
            
            # Check recent captures from global capture
            service = cli_instance._get_service()
            global_memories = service.search_memories(
                query="",
                tags=['global-capture'],
                limit=5
            )
            
            if global_memories:
                cli_instance._print(f"📊 {len(global_memories)} recent global captures found", "cyan")
                
                if HAS_RICH and console:
                    table = Table(title="Recent Global Captures")
                    table.add_column("App", style="cyan")
                    table.add_column("Content", style="white")
                    table.add_column("Method", style="yellow")
                    
                    for memory in global_memories[:3]:
                        metadata = memory.get('metadata', {})
                        app_name = metadata.get('app_name', 'Unknown')
                        capture_method = metadata.get('capture_method', 'unknown')
                        content = memory.get('content', '')[:50] + ('...' if len(memory.get('content', '')) > 50 else '')
                        
                        table.add_row(app_name, content, capture_method)
                    
                    console.print(table)
                else:
                    print("Recent Global Captures:")
                    for i, memory in enumerate(global_memories[:3], 1):
                        metadata = memory.get('metadata', {})
                        app_name = metadata.get('app_name', 'Unknown')
                        content = memory.get('content', '')[:50] + ('...' if len(memory.get('content', '')) > 50 else '')
                        print(f"  {i}. [{app_name}] {content}")
            else:
                cli_instance._print("No global captures found yet", "yellow")
                cli_instance._print("💡 Try pressing ⌘⇧M anywhere in macOS to capture!")
        else:
            cli_instance._print("❌ Global Capture Service is not running", "red")
            cli_instance._print("💡 Install: cd global-capture && ./build.sh && cd build && ./install.sh")
            
            # Check if it's installed but not running
            app_path = "/Applications/Universal Memory Capture.app"
            if Path(app_path).exists():
                cli_instance._print("📱 App installed but not running", "yellow")
                cli_instance._print(f"💡 Launch: open '{app_path}'")
            else:
                cli_instance._print("📱 App not installed", "yellow")
    
    except Exception as e:
        cli_instance._print(f"❌ Error checking capture status: {e}", "red")

@capture.command('test')
@click.option('--content', '-c', default="Test global capture", help='Test content to store')
def capture_test(content):
    """Test global capture functionality."""
    try:
        service = cli_instance._get_service()
        
        # Simulate a global capture
        test_memory = {
            'content': content,
            'category': 'test',
            'tags': ['global-capture', 'test'],
            'importance': 5,
            'source': 'global_capture_test',
            'metadata': {
                'app_name': 'CLI Test',
                'bundle_id': 'com.test.cli',
                'window_title': 'Memory CLI Test',
                'project_context': 'universal-memory-system',
                'capture_method': 'cli_test',
                'timestamp': datetime.now().isoformat(),
                'platform': 'macos_global'
            }
        }
        
        result = service.store_memory(**test_memory)
        
        cli_instance._print("✅ Global capture test successful!", "green")
        cli_instance._print(f"Memory ID: {result['id']}")
        cli_instance._print(f"Content: {content}")
        cli_instance._print("🎯 Test capture can be found with: memory search --tags global-capture")
    
    except Exception as e:
        cli_instance._print(f"❌ Global capture test failed: {e}", "red")

@capture.command('install')
def capture_install():
    """Guide for installing Global Capture Service."""
    cli_instance._print("🧠 Universal AI Memory - Global Capture Installation", "bold")
    cli_instance._print("=" * 60)
    cli_instance._print("")
    cli_instance._print("1. Navigate to the global-capture directory:", "cyan")
    cli_instance._print("   cd global-capture")
    cli_instance._print("")
    cli_instance._print("2. Build the application:", "cyan") 
    cli_instance._print("   ./build.sh")
    cli_instance._print("")
    cli_instance._print("3. Install the service:", "cyan")
    cli_instance._print("   cd build && ./install.sh")
    cli_instance._print("")
    cli_instance._print("4. Grant Accessibility permissions when prompted", "cyan")
    cli_instance._print("")
    cli_instance._print("5. Look for the brain icon 🧠 in your menu bar", "cyan")
    cli_instance._print("")
    cli_instance._print("6. Press ⌘⇧M anywhere in macOS to capture!", "cyan")
    cli_instance._print("")
    cli_instance._print("📖 Full instructions: global-capture/USER_INSTRUCTIONS.md", "yellow")

# Enhanced natural language processing
def handle_natural_language_query(query: str, service) -> str:
    """Process natural language queries with enhanced intent detection"""
    query_lower = query.lower().strip()
    
    # Enhanced intent patterns
    search_patterns = ['show me', 'find', 'search for', 'what', 'how', 'when', 'where', 'list', 'tell me about']
    stats_patterns = ['statistics', 'stats', 'how many', 'count', 'total', 'system status', 'overview', 'dashboard']
    summary_patterns = ['summarize', 'summary', 'overview of', 'recap', 'digest']
    context_patterns = ['generate context', 'context for', 'relevant to', 'help me with', 'background on']
    capture_patterns = ['global capture', 'capture status', 'hotkey', 'menu bar', 'clipboard']
    github_patterns = ['github', 'repository', 'repo', 'git']
    
    # Check for global capture queries
    if any(pattern in query_lower for pattern in capture_patterns):
        return handle_capture_query(query_lower, service)
    
    # Check for GitHub queries
    if any(pattern in query_lower for pattern in github_patterns):
        return handle_github_query(query_lower, service)
    
    # Check for statistics request
    if any(pattern in query_lower for pattern in stats_patterns) or query_lower in ['stats', 'status']:
        stats = service.get_statistics()
        return format_statistics(stats)
    
    # Check for summary request
    if any(pattern in query_lower for pattern in summary_patterns):
        results = service.search_memories(query=query, limit=20, include_semantic=True)
        if results:
            output = [f"📋 Memory Summary for: '{query}'"]
            output.append("=" * 60)
            
            # Group by category
            by_category = {}
            for memory in results:
                cat = memory.get('category', 'unknown')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(memory)
            
            for category, memories in by_category.items():
                output.append(f"\n📂 {category.title()} ({len(memories)} items):")
                for memory in memories[:3]:
                    content = memory.get('content', '')[:80] + ('...' if len(memory.get('content', '')) > 80 else '')
                    output.append(f"   • {content}")
                if len(memories) > 3:
                    output.append(f"   ... and {len(memories) - 3} more")
            
            return "\n".join(output)
        else:
            return f"No memories found to summarize for: '{query}'"
    
    # Check for context generation request
    if any(pattern in query_lower for pattern in context_patterns):
        context = service.get_context(relevant_to=query, max_tokens=3000)
        return f"🧠 Generated Context for: '{query}'\n{'=' * 60}\n\n{context}"
    
    # Default to search
    results = service.search_memories(query=query, limit=10, include_semantic=True)
    return format_memory_table(results)

def handle_capture_query(query: str, service) -> str:
    """Handle global capture related queries"""
    if 'status' in query:
        import subprocess
        try:
            result = subprocess.run(['pgrep', '-f', 'Universal Memory Capture'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return "✅ Global Capture Service is running\n🧠 Look for the brain icon in your menu bar\n⌨️ Press ⌘⇧M anywhere to capture"
            else:
                return "❌ Global Capture Service is not running\n💡 Install: cd global-capture && ./build.sh && cd build && ./install.sh"
        except:
            return "❓ Unable to check Global Capture Service status"
    
    elif 'recent' in query or 'captures' in query:
        global_memories = service.search_memories(tags=['global-capture'], limit=10)
        if global_memories:
            output = [f"📊 Recent Global Captures ({len(global_memories)} found):"]
            for i, memory in enumerate(global_memories[:5], 1):
                metadata = memory.get('metadata', {})
                app_name = metadata.get('app_name', 'Unknown')
                content = memory.get('content', '')[:60] + ('...' if len(memory.get('content', '')) > 60 else '')
                output.append(f"  {i}. [{app_name}] {content}")
            return "\n".join(output)
        else:
            return "No global captures found yet.\n💡 Press ⌘⇧M anywhere in macOS to start capturing!"
    
    else:
        return "🧠 Global Capture Service captures from any macOS app:\n⌨️ Press ⌘⇧M to capture selected text\n📋 Clipboard monitoring (auto-capture)\n🖼️ OCR screenshot text extraction\n💡 Use 'memory capture status' for more details"

def handle_github_query(query: str, service) -> str:
    """Handle GitHub integration queries"""
    if 'status' in query:
        github_memories = service.search_memories(tags=['github'], limit=5)
        if github_memories:
            return f"✅ GitHub integration active with {len(github_memories)} knowledge items\n💡 Use 'memory github status' for detailed information"
        else:
            return "❌ No GitHub integration found\n💡 Use 'memory github init' to set up repository integration"
    
    elif 'recent' in query or 'repository' in query:
        github_memories = service.search_memories(tags=['github'], limit=10)
        if github_memories:
            output = [f"📊 Recent GitHub Knowledge ({len(github_memories)} items):"]
            for i, memory in enumerate(github_memories[:3], 1):
                project = memory.get('project', 'Unknown')
                content = memory.get('content', '')[:60] + ('...' if len(memory.get('content', '')) > 60 else '')
                output.append(f"  {i}. [{project}] {content}")
            return "\n".join(output)
        else:
            return "No GitHub knowledge found.\n💡 Use 'memory github init' to analyze a repository"
    
    else:
        return "🐙 GitHub Integration captures repository knowledge:\n📊 Repository analysis and documentation\n🐛 Issues and solutions\n💡 Commit patterns and insights\n💡 Use 'memory github init' to get started"

def format_statistics(stats: Dict[str, Any]) -> str:
    """Enhanced statistics formatting with global capture info"""
    output = []
    output.append("🧠 Universal AI Memory System - Statistics")
    output.append("=" * 60)
    
    overall = stats.get('overall', {})
    output.append(f"\n📊 Overall Statistics:")
    output.append(f"   Total Memories: {overall.get('total_memories', 0):,}")
    output.append(f"   Total Projects: {overall.get('total_projects', 0)}")
    output.append(f"   Database Size: {overall.get('database_size', 'Unknown')}")
    output.append(f"   Vector Index Size: {overall.get('vector_index_size', 'Unknown')}")
    output.append(f"   Embedding Provider: {overall.get('embedding_provider', 'Unknown')}")
    output.append(f"   Vector Search: {'✅ Enabled' if overall.get('vector_search_enabled') else '❌ Disabled'}")
    
    # Global Capture Statistics
    global_captures = stats.get('by_source', {}).get('global_capture', 0)
    if global_captures > 0:
        output.append(f"\n🌍 Global Capture Statistics:")
        output.append(f"   Total Global Captures: {global_captures}")
        
        # Break down by capture method if available
        global_methods = {}
        for source, count in stats.get('by_source', {}).items():
            if 'global_capture' in source:
                method = source.replace('global_capture_', '')
                global_methods[method] = count
        
        if global_methods:
            output.append(f"   Capture Methods:")
            for method, count in sorted(global_methods.items(), key=lambda x: x[1], reverse=True):
                output.append(f"     {method}: {count}")
    
    # Categories
    if stats.get('by_category'):
        output.append(f"\n📂 By Category:")
        for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
            output.append(f"   {category.title()}: {count}")
    
    # Projects
    if stats.get('by_project'):
        output.append(f"\n📁 By Project (Top 10):")
        for project, count in sorted(stats['by_project'].items(), key=lambda x: x[1], reverse=True)[:10]:
            output.append(f"   {project}: {count}")
    
    # Recent activity
    if stats.get('by_date'):
        output.append(f"\n📅 Recent Activity:")
        recent_dates = sorted(stats['by_date'].items(), key=lambda x: x[0], reverse=True)[:7]
        for date, count in recent_dates:
            output.append(f"   {date}: {count} memories")
    
    return "\n".join(output)

def format_memory_table(memories: List[Dict[str, Any]], limit: int = None) -> str:
    """Enhanced memory table formatting"""
    if not memories:
        return "No memories found."
    
    if limit:
        memories = memories[:limit]
    
    output = []
    output.append("📋 Memory Search Results")
    output.append("=" * 80)
    
    for i, memory in enumerate(memories, 1):
        # Enhanced content display
        content = memory.get('content', '')
        if len(content) > 100:
            content = content[:97] + "..."
        
        # Category with emoji
        category = memory.get('category', 'unknown')
        category_emojis = {
            'solution': '🔧', 'code': '💻', 'configuration': '⚙️',
            'troubleshooting': '🐛', 'development': '👨‍💻', 'research': '🔍',
            'note': '📝', 'insight': '💡', 'pattern': '🔄', 'github': '🐙'
        }
        category_emoji = category_emojis.get(category, '📄')
        
        output.append(f"\n{i}. {category_emoji} {category.title()}: {content}")
        
        # Project and metadata
        project = memory.get('project', 'None')
        importance = '⭐' * memory.get('importance', 0) if memory.get('importance', 0) > 0 else 'N/A'
        output.append(f"   📁 Project: {project} | {importance} | 📅 {memory.get('created_at', 'Unknown')}")
        
        # Tags
        if memory.get('tags'):
            tags = memory['tags'] if isinstance(memory['tags'], list) else memory['tags'].split(',')
            output.append(f"   🏷️  Tags: {', '.join(tags)}")
        
        # Source with enhanced display
        source = memory.get('source', '')
        if source:
            source_emojis = {
                'global_capture': '🌍', 'browser_extension': '🌐', 'github': '🐙',
                'cli': '💻', 'manual': '✍️', 'ai_chat': '🤖'
            }
            
            for key, emoji in source_emojis.items():
                if key in source:
                    source = f"{emoji} {source}"
                    break
            
            output.append(f"   📍 Source: {source}")
        
        # Global capture specific metadata
        metadata = memory.get('metadata', {})
        if metadata.get('app_name'):
            app_name = metadata['app_name']
            capture_method = metadata.get('capture_method', '')
            output.append(f"   🖥️  App: {app_name} ({capture_method})")
        
        # Similarity score
        if memory.get('similarity_score'):
            output.append(f"   🎯 Relevance: {memory['similarity_score']:.2f}")
    
    output.append(f"\n📊 Showing {len(memories)} results")
    return "\n".join(output)

# Add new command for natural language queries
@cli.command()
@click.argument('query')
def ask(query):
    """Ask a natural language question to your memory system.
    
    Examples:
      memory ask "What solutions have I found for React performance?"
      memory ask "Show me recent global captures"
      memory ask "What's the status of GitHub integration?"
      memory ask "Summarize my authentication-related memories"
    """
    try:
        service = cli_instance._get_service()
        result = handle_natural_language_query(query, service)
        
        if HAS_RICH and console:
            # Try to render as markdown if it looks like structured content
            if any(marker in result for marker in ['#', '*', '-', '=']):
                from rich.markdown import Markdown
                try:
                    md = Markdown(result)
                    console.print(md)
                    return
                except:
                    pass
        
        print(result)
    
    except Exception as e:
        cli_instance._print(f"❌ Error processing query: {e}", "red")

# GitHub Integration Commands
@cli.group()
def github():
    """GitHub repository integration commands."""
    if not HAS_GITHUB_INTEGRATION:
        cli_instance._print("❌ GitHub integration not available. Please install required dependencies.", "red")
        sys.exit(1)

@github.command('init')
@click.option('--repo', help='Repository URL or owner/repo format')
@click.option('--token', help='GitHub personal access token')
@click.option('--comprehensive', is_flag=True, help='Perform comprehensive analysis (slower)')
def github_init(repo, token, comprehensive):
    """Initialize GitHub integration for a repository.
    
    Examples:
      memory github init --repo owner/repo
      memory github init --repo https://github.com/owner/repo.git --comprehensive
    """
    try:
        # Detect current repository if not specified
        if not repo:
            service = cli_instance._get_service()
            git_info = service._get_git_info()
            if git_info['is_git_repo'] and git_info['github_repo']:
                repo = git_info['github_repo']
                cli_instance._print(f"Auto-detected repository: {repo}", "cyan")
            else:
                cli_instance._print("❌ No repository specified and current directory is not a GitHub repository", "red")
                cli_instance._print("Use: memory github init --repo owner/repo")
                return
        
        # Initialize GitHub client
        github_token = token or os.getenv('GITHUB_TOKEN')
        github_client = GitHubClient(github_token)
        
        if not github_client.is_available():
            cli_instance._print("❌ GitHub API client not available. Check network connection and token.", "red")
            return
        
        # Show rate limit status
        rate_limit = github_client.get_rate_limit_status()
        cli_instance._print(f"GitHub API: {rate_limit['remaining']}/{rate_limit['limit']} requests remaining", "cyan")
        
        # Perform knowledge synthesis
        synthesizer = GitHubKnowledgeSynthesizer(github_client)
        
        if HAS_RICH and console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing repository...", total=None)
                synthesis = synthesizer.synthesize_repository_knowledge(repo, comprehensive)
        else:
            print(f"Analyzing repository {repo}...")
            synthesis = synthesizer.synthesize_repository_knowledge(repo, comprehensive)
        
        # Store knowledge items in memory
        service = cli_instance._get_service()
        stored_count = 0
        
        for item in synthesis['consolidated_knowledge']:
            try:
                service.store_memory(
                    content=item['content'],
                    category=item.get('category', 'github'),
                    tags=item.get('tags', []),
                    importance=item.get('importance', 5),
                    source=item.get('source', 'github'),
                    source_url=item.get('source_url', ''),
                    metadata=item.get('metadata', {})
                )
                stored_count += 1
            except Exception as e:
                cli_instance._print(f"Warning: Failed to store item: {e}", "yellow")
        
        cli_instance._print(f"✅ GitHub integration complete!", "green")
        cli_instance._print(f"📊 Analyzed repository: {synthesis['repository']['name']}", "cyan")
        cli_instance._print(f"💾 Stored {stored_count} knowledge items", "cyan")
        cli_instance._print(f"📈 Repository maturity: {synthesis.get('summary', {}).get('repository_overview', {}).get('maturity', 'unknown')}", "cyan")
        
        # Show summary if rich is available
        if HAS_RICH and console and synthesis.get('summary'):
            summary = synthesis['summary']
            
            # Technology stack
            if summary.get('technology_stack'):
                console.print("\n[bold]Technology Stack:[/bold]")
                for tech in summary['technology_stack'][:5]:
                    console.print(f"  • {tech['name']} ({tech.get('category', 'detected')})")
            
            # Key insights
            if summary.get('key_insights'):
                console.print("\n[bold]Key Insights:[/bold]")
                for insight in summary['key_insights'][:3]:
                    console.print(f"  • [{insight['category']}] {insight['content']}")
            
            # Recommendations
            if synthesis.get('recommendations'):
                console.print("\n[bold]Recommendations:[/bold]")
                for rec in synthesis['recommendations'][:3]:
                    priority_color = {"high": "red", "medium": "yellow", "low": "green"}.get(rec['priority'], "white")
                    console.print(f"  • [{priority_color}]{rec['priority'].upper()}[/{priority_color}] {rec['title']}: {rec['description']}")
    
    except Exception as e:
        cli_instance._print(f"❌ GitHub integration failed: {e}", "red")
        if cli_instance.verbose:
            import traceback
            traceback.print_exc()

@github.command('sync')
@click.option('--repo', help='Repository URL or owner/repo format') 
@click.option('--issues', is_flag=True, help='Sync issues and solutions')
@click.option('--commits', is_flag=True, help='Sync commit patterns')
@click.option('--docs', is_flag=True, help='Sync documentation')
@click.option('--all', 'sync_all', is_flag=True, help='Sync everything')
def github_sync(repo, issues, commits, docs, sync_all):
    """Sync specific GitHub repository data.
    
    Examples:
      memory github sync --issues
      memory github sync --repo owner/repo --all
      memory github sync --commits --docs
    """
    try:
        # Detect current repository if not specified
        if not repo:
            service = cli_instance._get_service()
            git_info = service._get_git_info()
            if git_info['is_git_repo'] and git_info['github_repo']:
                repo = git_info['github_repo']
                cli_instance._print(f"Auto-detected repository: {repo}", "cyan")
            else:
                cli_instance._print("❌ No repository specified and current directory is not a GitHub repository", "red")
                return
        
        if not any([issues, commits, docs, sync_all]):
            cli_instance._print("❌ Please specify what to sync: --issues, --commits, --docs, or --all", "red")
            return
        
        github_client = GitHubClient(os.getenv('GITHUB_TOKEN'))
        if not github_client.is_available():
            cli_instance._print("❌ GitHub API not available", "red")
            return
        
        # Parse repository
        parts = repo.split('/')
        if len(parts) != 2:
            cli_instance._print("❌ Invalid repository format. Use: owner/repo", "red")
            return
        
        owner, repo_name = parts
        service = cli_instance._get_service()
        total_stored = 0
        
        # Sync issues
        if issues or sync_all:
            cli_instance._print("Syncing issues and solutions...", "cyan")
            from github_integration.issue_processor import IssueKnowledgeExtractor
            
            extractor = IssueKnowledgeExtractor(github_client)
            issue_knowledge = extractor.extract_issues_knowledge(owner, repo_name)
            
            for item in issue_knowledge.get('knowledge_items', []):
                service.store_memory(
                    content=item['content'],
                    category=item.get('category', 'github-issue'),
                    tags=item.get('tags', []),
                    importance=item.get('importance', 6),
                    source=item.get('source', 'github-issues'),
                    source_url=item.get('source_url', ''),
                    metadata=item.get('metadata', {})
                )
                total_stored += 1
        
        # Sync commits
        if commits or sync_all:
            cli_instance._print("Syncing commit patterns...", "cyan")
            from github_integration.commit_parser import CommitIntelligenceParser
            
            parser = CommitIntelligenceParser(github_client)
            commit_knowledge = parser.analyze_commits(owner, repo_name, limit=100)
            
            for item in commit_knowledge.get('knowledge_items', []):
                service.store_memory(
                    content=item['content'],
                    category=item.get('category', 'github-commit'),
                    tags=item.get('tags', []),
                    importance=item.get('importance', 5),
                    source=item.get('source', 'github-commits'),
                    source_url=item.get('source_url', ''),
                    metadata=item.get('metadata', {})
                )
                total_stored += 1
        
        # Sync documentation
        if docs or sync_all:
            cli_instance._print("Syncing documentation...", "cyan")
            from github_integration.docs_importer import DocumentationImporter
            
            importer = DocumentationImporter(github_client)
            docs_knowledge = importer.import_documentation(owner, repo_name)
            
            for item in docs_knowledge.get('knowledge_items', []):
                service.store_memory(
                    content=item['content'],
                    category=item.get('category', 'github-docs'),
                    tags=item.get('tags', []),
                    importance=item.get('importance', 6),
                    source=item.get('source', 'github-docs'),
                    source_url=item.get('source_url', ''),
                    metadata=item.get('metadata', {})
                )
                total_stored += 1
        
        cli_instance._print(f"✅ GitHub sync complete! Stored {total_stored} new knowledge items", "green")
    
    except Exception as e:
        cli_instance._print(f"❌ GitHub sync failed: {e}", "red")
        if cli_instance.verbose:
            import traceback
            traceback.print_exc()

@github.command('status')
@click.option('--repo', help='Repository URL or owner/repo format')
def github_status(repo):
    """Show GitHub integration status for repository.
    
    Examples:
      memory github status
      memory github status --repo owner/repo
    """
    try:
        # Detect current repository if not specified
        if not repo:
            service = cli_instance._get_service()
            git_info = service._get_git_info()
            if git_info['is_git_repo']:
                repo = git_info['github_repo'] if git_info['github_repo'] else git_info['repo_name']
                cli_instance._print(f"Repository: {repo}", "cyan")
                cli_instance._print(f"Git root: {git_info['repo_root']}", "cyan")
                cli_instance._print(f"Branch: {git_info['current_branch']}", "cyan")
                cli_instance._print(f"Commit: {git_info['commit_hash']}", "cyan")
            else:
                cli_instance._print("❌ Current directory is not a git repository", "red")
                return
        
        # Check GitHub API status
        github_client = GitHubClient(os.getenv('GITHUB_TOKEN'))
        if github_client.is_available():
            rate_limit = github_client.get_rate_limit_status()
            cli_instance._print(f"✅ GitHub API available", "green")
            cli_instance._print(f"Rate limit: {rate_limit['remaining']}/{rate_limit['limit']}", "cyan")
            cli_instance._print(f"Authenticated: {'Yes' if rate_limit['authenticated'] else 'No'}", "cyan")
        else:
            cli_instance._print("❌ GitHub API not available", "red")
        
        # Check stored GitHub knowledge
        service = cli_instance._get_service()
        github_memories = service.search_memories(
            query="", 
            tags=['github'], 
            limit=1000
        )
        
        if github_memories:
            github_count = len(github_memories)
            cli_instance._print(f"📊 {github_count} GitHub knowledge items stored", "green")
            
            # Count by source
            sources = {}
            for memory in github_memories:
                source = memory.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            if HAS_RICH and console:
                table = Table(title="GitHub Knowledge Sources")
                table.add_column("Source", style="cyan")
                table.add_column("Count", style="green")
                
                for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                    table.add_row(source, str(count))
                
                console.print(table)
            else:
                print("GitHub Knowledge Sources:")
                for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {source}: {count}")
        else:
            cli_instance._print("No GitHub knowledge items found", "yellow")
    
    except Exception as e:
        cli_instance._print(f"❌ Status check failed: {e}", "red")

# Shell completion setup
@cli.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), help='Shell type')
@click.option('--install', is_flag=True, help='Install completion automatically')
def completion(shell, install):
    """Set up shell completion for the memory command.
    
    Examples:
      memory completion --shell bash --install
      memory completion --shell zsh
    """
    if not shell:
        # Detect shell
        shell_path = os.environ.get('SHELL', '')
        if 'bash' in shell_path:
            shell = 'bash'
        elif 'zsh' in shell_path:
            shell = 'zsh'
        elif 'fish' in shell_path:
            shell = 'fish'
        else:
            cli_instance._print("Could not detect shell. Please specify --shell", "yellow")
            return
    
    # Generate completion script
    completion_script = f"eval \"$(_MEMORY_COMPLETE={shell}_source memory)\""
    
    if install:
        # Install completion
        if shell == 'bash':
            completion_file = Path.home() / '.bashrc'
        elif shell == 'zsh':
            completion_file = Path.home() / '.zshrc'
        elif shell == 'fish':
            completion_file = Path.home() / '.config' / 'fish' / 'config.fish'
            completion_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if already installed
        try:
            with open(completion_file, 'r') as f:
                content = f.read()
            if '_MEMORY_COMPLETE' in content:
                cli_instance._print("Completion already installed", "yellow")
                return
        except FileNotFoundError:
            pass
        
        # Add completion
        with open(completion_file, 'a') as f:
            f.write(f"\n# Memory CLI completion\n{completion_script}\n")
        
        cli_instance._print(f"✅ Completion installed for {shell}", "green")
        cli_instance._print(f"Restart your shell or run: source {completion_file}")
    else:
        # Just show the script
        cli_instance._print(f"Add this line to your {shell} configuration:")
        cli_instance._print(completion_script)

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        if os.environ.get('MEMORY_VERBOSE'):
            raise
        print(f"Error: {e}")
        sys.exit(1)