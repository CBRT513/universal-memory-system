#!/usr/bin/env python3
"""
Documentation Importer for Universal AI Memory System
Imports and processes repository documentation
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from .github_client import GitHubClient

logger = logging.getLogger(__name__)

class DocumentationImporter:
    """Imports and processes repository documentation"""
    
    def __init__(self, github_client: GitHubClient):
        self.github = github_client
        
        # Documentation patterns
        self.doc_extensions = ['.md', '.rst', '.txt', '.adoc']
        self.doc_directories = ['docs', 'doc', 'documentation', 'wiki']
        
    def import_documentation(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Import all documentation from repository"""
        logger.info(f"Importing documentation from {owner}/{repo_name}")
        
        docs = {
            'repository': {'owner': owner, 'name': repo_name},
            'documentation': {},
            'knowledge_items': []
        }
        
        # Import main documentation files
        main_docs = self._import_main_docs(owner, repo_name)
        docs['documentation'].update(main_docs)
        
        # Import docs directory
        docs_dir = self._import_docs_directory(owner, repo_name)
        docs['documentation'].update(docs_dir)
        
        # Generate knowledge items
        docs['knowledge_items'] = self._generate_docs_knowledge_items(docs)
        
        return docs
    
    def _import_main_docs(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Import main documentation files from repository root"""
        main_docs = {}
        
        # Common documentation files
        doc_files = [
            'README.md', 'README.rst', 'README.txt',
            'CONTRIBUTING.md', 'CHANGELOG.md', 'LICENSE',
            'INSTALL.md', 'SETUP.md', 'API.md'
        ]
        
        for doc_file in doc_files:
            content = self.github.get_file_content(owner, repo_name, doc_file)
            if content:
                parsed = self._parse_documentation(content, doc_file)
                main_docs[doc_file.lower().replace('.', '_')] = {
                    'file': doc_file,
                    'content': content,
                    'parsed': parsed
                }
        
        return main_docs
    
    def _import_docs_directory(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Import documentation from docs directory"""
        docs_content = {}
        
        for doc_dir in self.doc_directories:
            contents = self.github.get_repository_contents(owner, repo_name, doc_dir)
            if contents:
                for item in contents:
                    if item['type'] == 'file' and any(item['name'].endswith(ext) for ext in self.doc_extensions):
                        file_path = f"{doc_dir}/{item['name']}"
                        content = self.github.get_file_content(owner, repo_name, file_path)
                        if content:
                            parsed = self._parse_documentation(content, item['name'])
                            docs_content[f"{doc_dir}_{item['name'].lower().replace('.', '_')}"] = {
                                'file': file_path,
                                'content': content,
                                'parsed': parsed
                            }
        
        return docs_content
    
    def _parse_documentation(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse documentation content"""
        parsed = {
            'sections': [],
            'code_blocks': [],
            'links': [],
            'summary': '',
            'key_concepts': []
        }
        
        # Extract sections
        parsed['sections'] = self._extract_sections(content)
        
        # Extract code blocks
        parsed['code_blocks'] = self._extract_code_blocks(content)
        
        # Extract links
        parsed['links'] = self._extract_links(content)
        
        # Generate summary
        parsed['summary'] = self._generate_summary(content)
        
        # Extract key concepts
        parsed['key_concepts'] = self._extract_key_concepts(content)
        
        return parsed
    
    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract sections from markdown/rst content"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Markdown headers
            if line.startswith('#'):
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip(),
                        'level': len(current_section.split('#')[0])
                    })
                current_section = line.lstrip('#').strip()
                current_content = []
            # RST headers (simplified)
            elif len(line) > 0 and len(lines) > lines.index(line) + 1:
                next_line = lines[lines.index(line) + 1] if lines.index(line) + 1 < len(lines) else ''
                if next_line and all(c in '=-~^' for c in next_line) and len(next_line) >= len(line):
                    if current_section:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content).strip(),
                            'level': 1
                        })
                    current_section = line.strip()
                    current_content = []
                else:
                    current_content.append(line)
            else:
                current_content.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip(),
                'level': 1
            })
        
        return sections
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from content"""
        code_blocks = []
        
        # Triple backtick blocks
        pattern = r'```(\w+)?\n(.*?)```'
        for match in re.finditer(pattern, content, re.DOTALL):
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            code_blocks.append({
                'language': language,
                'code': code
            })
        
        # Indented code blocks
        lines = content.split('\n')
        in_code_block = False
        current_code = []
        
        for line in lines:
            if line.startswith('    ') and line.strip():
                in_code_block = True
                current_code.append(line[4:])  # Remove 4-space indent
            else:
                if in_code_block and current_code:
                    code_blocks.append({
                        'language': 'text',
                        'code': '\n'.join(current_code)
                    })
                    current_code = []
                in_code_block = False
        
        return code_blocks
    
    def _extract_links(self, content: str) -> List[Dict[str, str]]:
        """Extract links from markdown content"""
        links = []
        
        # Markdown links
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(pattern, content):
            text = match.group(1)
            url = match.group(2)
            links.append({
                'text': text,
                'url': url,
                'type': 'markdown'
            })
        
        # Plain URLs
        url_pattern = r'https?://[^\s)]+(?:\([^)]*\))?'
        for match in re.finditer(url_pattern, content):
            url = match.group(0)
            links.append({
                'text': url,
                'url': url,
                'type': 'plain'
            })
        
        return links
    
    def _generate_summary(self, content: str) -> str:
        """Generate summary from documentation content"""
        # Get first meaningful paragraph
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            # Skip headers and short lines
            clean = paragraph.strip()
            if not clean.startswith('#') and len(clean) > 100:
                # Clean up formatting
                clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)  # Remove markdown links
                clean = re.sub(r'`([^`]+)`', r'\1', clean)  # Remove inline code
                clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean)  # Remove bold
                clean = re.sub(r'\*([^*]+)\*', r'\1', clean)  # Remove italic
                clean = re.sub(r'\n+', ' ', clean)  # Replace newlines
                return clean[:300] + '...' if len(clean) > 300 else clean
        
        return ''
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from documentation"""
        concepts = []
        
        # Look for definition patterns
        definition_patterns = [
            r'(?i)^([A-Z][A-Za-z\s]+):\s*(.+)$',  # Term: definition
            r'(?i)\*\*([A-Za-z\s]+)\*\*:?\s*(.+)',  # **Term**: definition
            r'(?i)##?\s+([A-Za-z\s]+)',  # Headers as concepts
        ]
        
        for pattern in definition_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                concept = match.group(1).strip()
                if len(concept) > 3 and len(concept) < 50:
                    concepts.append(concept)
        
        # Deduplicate and return top concepts
        unique_concepts = list(set(concepts))
        return unique_concepts[:10]
    
    def _generate_docs_knowledge_items(self, docs_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate knowledge items from documentation"""
        knowledge_items = []
        repo_info = docs_data['repository']
        
        for doc_key, doc_info in docs_data['documentation'].items():
            parsed = doc_info['parsed']
            
            # Summary knowledge item
            if parsed['summary']:
                knowledge_items.append({
                    'content': f"{repo_info['name']} documentation: {parsed['summary']}",
                    'category': 'documentation',
                    'tags': ['github', 'documentation', doc_key, repo_info['name'].lower()],
                    'importance': 6,
                    'source': 'github_documentation',
                    'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/blob/main/{doc_info['file']}",
                    'metadata': {
                        'repo_name': repo_info['name'],
                        'doc_file': doc_info['file'],
                        'doc_type': doc_key
                    }
                })
            
            # Key concepts
            for concept in parsed['key_concepts'][:5]:
                knowledge_items.append({
                    'content': f"Key concept in {repo_info['name']}: {concept}",
                    'category': 'concept',
                    'tags': ['github', 'concept', 'documentation', repo_info['name'].lower()],
                    'importance': 5,
                    'source': 'github_docs_concept',
                    'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/blob/main/{doc_info['file']}",
                    'metadata': {
                        'repo_name': repo_info['name'],
                        'concept': concept,
                        'doc_file': doc_info['file']
                    }
                })
            
            # Code examples
            for code_block in parsed['code_blocks'][:3]:  # Limit to 3 per doc
                if len(code_block['code']) > 50:  # Meaningful code blocks
                    knowledge_items.append({
                        'content': f"Code example from {repo_info['name']} docs: {code_block['code'][:200]}",
                        'category': 'code-example',
                        'tags': ['github', 'code', code_block['language'], repo_info['name'].lower()],
                        'importance': 7,
                        'source': 'github_docs_code',
                        'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/blob/main/{doc_info['file']}",
                        'metadata': {
                            'repo_name': repo_info['name'],
                            'language': code_block['language'],
                            'full_code': code_block['code'],
                            'doc_file': doc_info['file']
                        }
                    })
        
        return knowledge_items