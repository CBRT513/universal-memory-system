#!/usr/bin/env python3
"""
Galactica Context Detection Service
Automatically identifies projects and their memory needs
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

@dataclass
class ProjectContext:
    """Represents a project's context and memory needs"""
    name: str
    path: str
    type: str  # python, node, ios, rust, etc.
    keywords: List[str]
    relevance_rules: Dict
    ignore_patterns: List[str]
    detected_at: str
    fingerprint: str  # Unique ID based on path and type
    
    def to_dict(self):
        return asdict(self)

class ContextDetector:
    """Detects and manages project contexts"""
    
    PROJECT_INDICATORS = {
        'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
        'node': ['package.json', 'node_modules', 'yarn.lock'],
        'ios': ['Package.swift', '*.xcodeproj', 'Podfile'],
        'rust': ['Cargo.toml', 'Cargo.lock'],
        'go': ['go.mod', 'go.sum'],
        'java': ['pom.xml', 'build.gradle'],
        'agentforge': ['.agentforge', 'forge.yaml'],
        'galactica': ['galactica.yaml', '.galactica/'],
    }
    
    TYPE_KEYWORDS = {
        'python': ['python', 'pip', 'django', 'flask', 'fastapi', 'pytest'],
        'node': ['npm', 'node', 'react', 'vue', 'express', 'webpack'],
        'ios': ['swift', 'xcode', 'ios', 'swiftui', 'uikit'],
        'rust': ['cargo', 'rust', 'rustc', 'crate'],
        'agentforge': ['memory', 'forge', 'agent', 'hnswlib', 'embeddings'],
        'galactica': ['universal memory', 'UMS', 'context', 'triage'],
    }
    
    def __init__(self, registry_path: str = "/usr/local/var/universal-memory-system/contexts"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.contexts_file = self.registry_path / "projects.json"
        self.contexts = self.load_contexts()
        
    def load_contexts(self) -> Dict[str, ProjectContext]:
        """Load existing project contexts from registry"""
        if self.contexts_file.exists():
            with open(self.contexts_file, 'r') as f:
                data = json.load(f)
                return {
                    k: ProjectContext(**v) for k, v in data.items()
                }
        return {}
        
    def save_contexts(self):
        """Persist contexts to registry"""
        with open(self.contexts_file, 'w') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.contexts.items()},
                f, indent=2
            )
    
    def detect_project_type(self, path: Path) -> str:
        """Detect project type based on files present"""
        for proj_type, indicators in self.PROJECT_INDICATORS.items():
            for indicator in indicators:
                if indicator.startswith('*'):
                    # Handle wildcards
                    if list(path.glob(indicator)):
                        return proj_type
                elif (path / indicator).exists():
                    return proj_type
        return 'generic'
    
    def extract_keywords(self, path: Path, project_type: str) -> List[str]:
        """Extract relevant keywords for the project"""
        keywords = self.TYPE_KEYWORDS.get(project_type, []).copy()
        
        # Add project name
        keywords.append(path.name.lower())
        
        # Check for .galactica/keywords.txt
        keywords_file = path / '.galactica' / 'keywords.txt'
        if keywords_file.exists():
            with open(keywords_file, 'r') as f:
                keywords.extend([k.strip() for k in f.readlines()])
                
        # Check README for keywords
        for readme in ['README.md', 'README.rst', 'README.txt']:
            readme_path = path / readme
            if readme_path.exists():
                with open(readme_path, 'r') as f:
                    content = f.read().lower()
                    # Extract likely keywords from first paragraph
                    first_para = content.split('\n\n')[0]
                    words = set(first_para.split())
                    tech_words = [w for w in words if len(w) > 3 and not w.startswith('#')]
                    keywords.extend(tech_words[:5])  # Top 5 words
                break
                
        return list(set(keywords))  # Unique keywords
    
    def load_custom_rules(self, path: Path) -> Dict:
        """Load project-specific rules if they exist"""
        rules_file = path / '.galactica' / 'memory_rules.yaml'
        if rules_file.exists():
            with open(rules_file, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def get_ignore_patterns(self, path: Path, project_type: str) -> List[str]:
        """Get patterns to ignore for this project"""
        # Default ignores
        ignores = [
            '*.pyc', '__pycache__', '.git', '.DS_Store',
            'node_modules', '.venv', 'venv', 'env',
            'build', 'dist', '*.log'
        ]
        
        # Type-specific ignores
        type_ignores = {
            'python': ['*.egg-info', '.pytest_cache', '.mypy_cache'],
            'node': ['npm-debug.log', '.next', '.nuxt'],
            'ios': ['DerivedData', '*.xcworkspace/xcuserdata'],
        }
        ignores.extend(type_ignores.get(project_type, []))
        
        # Custom ignores
        ignore_file = path / '.galactica' / 'ignore.txt'
        if ignore_file.exists():
            with open(ignore_file, 'r') as f:
                ignores.extend([line.strip() for line in f])
                
        return ignores
    
    def detect_context(self, path: str) -> ProjectContext:
        """Detect or retrieve context for a project path"""
        path_obj = Path(path).resolve()
        fingerprint = hashlib.md5(str(path_obj).encode()).hexdigest()
        
        # Check if we already know this project
        if fingerprint in self.contexts:
            return self.contexts[fingerprint]
            
        # Detect new project
        project_type = self.detect_project_type(path_obj)
        keywords = self.extract_keywords(path_obj, project_type)
        custom_rules = self.load_custom_rules(path_obj)
        ignore_patterns = self.get_ignore_patterns(path_obj, project_type)
        
        context = ProjectContext(
            name=path_obj.name,
            path=str(path_obj),
            type=project_type,
            keywords=keywords,
            relevance_rules=custom_rules.get('relevance_rules', {}),
            ignore_patterns=ignore_patterns,
            detected_at=datetime.now().isoformat(),
            fingerprint=fingerprint
        )
        
        # Cache and save
        self.contexts[fingerprint] = context
        self.save_contexts()
        
        return context
    
    def get_all_contexts(self) -> List[ProjectContext]:
        """Get all known project contexts"""
        return list(self.contexts.values())
    
    def find_related_projects(self, context: ProjectContext) -> List[ProjectContext]:
        """Find projects related to the given context"""
        related = []
        context_keywords = set(context.keywords)
        
        for other_context in self.contexts.values():
            if other_context.fingerprint == context.fingerprint:
                continue
                
            # Check keyword overlap
            other_keywords = set(other_context.keywords)
            overlap = context_keywords & other_keywords
            
            if len(overlap) >= 2:  # At least 2 keywords in common
                related.append(other_context)
                
        return related
    
    def suggest_keywords(self, context: ProjectContext) -> List[str]:
        """Suggest additional keywords based on similar projects"""
        suggested = set()
        related = self.find_related_projects(context)
        
        for related_context in related:
            for keyword in related_context.keywords:
                if keyword not in context.keywords:
                    suggested.add(keyword)
                    
        return list(suggested)


class ContextAwareMemory:
    """Memory operations that respect project context"""
    
    def __init__(self, detector: ContextDetector):
        self.detector = detector
        self.current_context = None
        
    def set_context(self, path: str):
        """Set the current working context"""
        self.current_context = self.detector.detect_context(path)
        return self.current_context
        
    def score_relevance(self, memory_content: str) -> float:
        """Score memory relevance to current context"""
        if not self.current_context:
            return 5.0  # Default middle score
            
        score = 0.0
        content_lower = memory_content.lower()
        
        # Check keyword matches
        for keyword in self.current_context.keywords:
            if keyword in content_lower:
                score += 2.0
                
        # Apply custom rules
        for rule in self.current_context.relevance_rules:
            if rule.get('pattern') in content_lower:
                score = max(score, rule.get('relevance', 5))
                
        # Check ignore patterns (negative score)
        for pattern in self.current_context.ignore_patterns:
            if pattern.replace('*', '') in content_lower:
                score -= 3.0
                
        return min(max(score, 0), 10)  # Clamp to 0-10
        
    def filter_memories(self, memories: List[Dict], threshold: float = 3.0) -> List[Dict]:
        """Filter memories based on context relevance"""
        filtered = []
        for memory in memories:
            relevance = self.score_relevance(memory.get('content', ''))
            if relevance >= threshold:
                memory['context_relevance'] = relevance
                filtered.append(memory)
                
        return sorted(filtered, key=lambda m: m['context_relevance'], reverse=True)


# CLI interface
if __name__ == "__main__":
    import sys
    
    detector = ContextDetector()
    
    if len(sys.argv) < 2:
        print("Usage: python galactica_context.py <path>")
        sys.exit(1)
        
    path = sys.argv[1]
    context = detector.detect_context(path)
    
    print(f"Project: {context.name}")
    print(f"Type: {context.type}")
    print(f"Path: {context.path}")
    print(f"Keywords: {', '.join(context.keywords)}")
    print(f"Ignore patterns: {', '.join(context.ignore_patterns)}")
    
    related = detector.find_related_projects(context)
    if related:
        print(f"\nRelated projects:")
        for r in related:
            print(f"  - {r.name} ({r.type})")
            
    suggested = detector.suggest_keywords(context)
    if suggested:
        print(f"\nSuggested keywords: {', '.join(suggested[:5])}")