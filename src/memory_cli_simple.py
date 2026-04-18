#!/usr/bin/env python3
"""
Universal AI Memory System - Simple CLI (no external dependencies)
Works without click, rich, or numpy
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from memory_service import get_memory_service, UniversalMemoryService

class SimpleMemoryCLI:
    """Simple CLI for memory management without external dependencies"""
    
    def __init__(self):
        self.service = get_memory_service()
    
    def add_memory(self, content: str, project: str = None, tags: List[str] = None, 
                   importance: int = 5, category: str = None):
        """Add a new memory"""
        try:
            result = self.service.store_memory(
                content=content,
                project=project or "general",
                category=category or "insight",
                importance=importance,
                tags=tags or [],
                source="cli"
            )
            print(f"✅ Memory stored successfully!")
            print(f"   ID: {result.get('id', 'N/A')}")
            print(f"   Project: {project or 'general'}")
            if tags:
                print(f"   Tags: {', '.join(tags)}")
            return result
        except Exception as e:
            print(f"❌ Error storing memory: {str(e)}")
            return None
    
    def search_memories(self, query: str, limit: int = 10, project: str = None):
        """Search for memories"""
        try:
            results = self.service.search_memories(
                query=query,
                project=project,
                limit=limit
            )
            
            if not results:
                print("No memories found matching your query.")
                return []
            
            print(f"\n📚 Found {len(results)} memories:\n")
            for i, memory in enumerate(results, 1):
                print(f"{i}. [{memory.get('project', 'general')}] {memory.get('content', '')[:100]}...")
                if memory.get('tags'):
                    print(f"   Tags: {', '.join(memory['tags'])}")
                print(f"   Importance: {'⭐' * memory.get('importance', 0)}")
                print(f"   Created: {datetime.fromtimestamp(memory.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M')}")
                print()
            
            return results
        except Exception as e:
            print(f"❌ Error searching memories: {str(e)}")
            return []
    
    def get_stats(self):
        """Get memory system statistics"""
        try:
            stats = self.service.get_statistics()
            
            print("\n📊 Memory System Statistics\n")
            print(f"Total Memories: {stats.get('total_memories', 0)}")
            print(f"Total Projects: {stats.get('total_projects', 0)}")
            print(f"Vector Search: {'✅ Enabled' if stats.get('vector_enabled', False) else '❌ Disabled'}")
            
            if stats.get('projects'):
                print("\n📁 Projects:")
                for project, count in stats['projects'].items():
                    print(f"   • {project}: {count} memories")
            
            if stats.get('categories'):
                print("\n📂 Categories:")
                for category, count in stats['categories'].items():
                    print(f"   • {category}: {count} memories")
            
            if stats.get('top_tags'):
                print("\n🏷️  Top Tags:")
                for tag, count in stats['top_tags'][:10]:
                    print(f"   • {tag}: {count} uses")
            
            return stats
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
            return {}
    
    def list_recent(self, limit: int = 10):
        """List recent memories"""
        try:
            # Search with empty query to get all, sorted by recency
            results = self.service.search_memories(query="", limit=limit)
            
            if not results:
                print("No memories found.")
                return []
            
            print(f"\n📝 {len(results)} Most Recent Memories:\n")
            for i, memory in enumerate(results, 1):
                print(f"{i}. {memory.get('content', '')[:100]}...")
                print(f"   Project: {memory.get('project', 'general')}")
                if memory.get('tags'):
                    print(f"   Tags: {', '.join(memory['tags'])}")
                print(f"   Created: {datetime.fromtimestamp(memory.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M')}")
                print()
            
            return results
        except Exception as e:
            print(f"❌ Error listing memories: {str(e)}")
            return []
    
    def ask_question(self, question: str):
        """Ask a question and get context from memories"""
        try:
            # Search for relevant memories
            results = self.service.search_memories(query=question, limit=5)
            
            print(f"\n🤔 Question: {question}\n")
            
            if results:
                print("📚 Relevant memories found:\n")
                for i, memory in enumerate(results, 1):
                    print(f"{i}. {memory.get('content', '')[:150]}...")
                    print(f"   Relevance: {memory.get('relevance_score', 0):.2f}")
                    print()
            else:
                print("No relevant memories found for your question.")
            
            return results
        except Exception as e:
            print(f"❌ Error processing question: {str(e)}")
            return []

def main():
    parser = argparse.ArgumentParser(
        description='Universal AI Memory System - Simple CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add "Important insight about Python decorators" --tags python,decorators
  %(prog)s search "React hooks"
  %(prog)s stats
  %(prog)s list --limit 5
  %(prog)s ask "What do I know about authentication?"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new memory')
    add_parser.add_argument('content', help='Memory content')
    add_parser.add_argument('--project', '-p', help='Project name')
    add_parser.add_argument('--tags', '-t', help='Comma-separated tags')
    add_parser.add_argument('--importance', '-i', type=int, default=5, help='Importance (1-10)')
    add_parser.add_argument('--category', '-c', help='Category (insight, solution, etc.)')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search memories')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', '-l', type=int, default=10, help='Number of results')
    search_parser.add_argument('--project', '-p', help='Filter by project')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List recent memories')
    list_parser.add_argument('--limit', '-l', type=int, default=10, help='Number of memories')
    
    # Ask command
    ask_parser = subparsers.add_parser('ask', help='Ask a question')
    ask_parser.add_argument('question', help='Your question')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = SimpleMemoryCLI()
    
    if args.command == 'add':
        tags = args.tags.split(',') if args.tags else []
        cli.add_memory(
            content=args.content,
            project=args.project,
            tags=tags,
            importance=args.importance,
            category=args.category
        )
    
    elif args.command == 'search':
        cli.search_memories(args.query, args.limit, args.project)
    
    elif args.command == 'stats':
        cli.get_stats()
    
    elif args.command == 'list':
        cli.list_recent(args.limit)
    
    elif args.command == 'ask':
        cli.ask_question(args.question)

if __name__ == "__main__":
    main()