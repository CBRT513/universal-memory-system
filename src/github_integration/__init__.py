"""
GitHub Integration Module for Universal AI Memory System

This module provides comprehensive GitHub API integration for:
- Repository metadata extraction
- Issue and PR knowledge mining
- Commit analysis and pattern extraction
- Documentation parsing and indexing
- Real-time repository monitoring
"""

from .github_client import GitHubClient
from .repo_analyzer import RepositoryAnalyzer
from .commit_parser import CommitIntelligenceParser
from .issue_processor import IssueKnowledgeExtractor
from .docs_importer import DocumentationImporter
from .knowledge_synthesizer import GitHubKnowledgeSynthesizer

__all__ = [
    'GitHubClient',
    'RepositoryAnalyzer',
    'CommitIntelligenceParser', 
    'IssueKnowledgeExtractor',
    'DocumentationImporter',
    'GitHubKnowledgeSynthesizer'
]

__version__ = "1.0.0"