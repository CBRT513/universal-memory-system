#!/usr/bin/env python3
"""
GitHub Knowledge Synthesizer for Universal AI Memory System
Combines and synthesizes knowledge from multiple GitHub sources
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from .github_client import GitHubClient
from .repo_analyzer import RepositoryAnalyzer
from .commit_parser import CommitIntelligenceParser
from .issue_processor import IssueKnowledgeExtractor
from .docs_importer import DocumentationImporter

logger = logging.getLogger(__name__)

class GitHubKnowledgeSynthesizer:
    """Synthesizes knowledge from multiple GitHub analysis sources"""
    
    def __init__(self, github_client: GitHubClient):
        """Initialize with GitHub client"""
        self.github = github_client
        
        # Initialize analyzers
        self.repo_analyzer = RepositoryAnalyzer(github_client)
        self.commit_parser = CommitIntelligenceParser(github_client)
        self.issue_processor = IssueKnowledgeExtractor(github_client)
        self.docs_importer = DocumentationImporter(github_client)
    
    def synthesize_repository_knowledge(self, repo_url: str, 
                                      comprehensive: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive repository knowledge synthesis
        
        Args:
            repo_url: GitHub repository URL or owner/repo
            comprehensive: Whether to perform full analysis (slower but more complete)
            
        Returns:
            Synthesized knowledge from all sources
        """
        logger.info(f"Starting comprehensive knowledge synthesis for {repo_url}")
        
        # Parse repository identifier
        owner, repo_name = self._parse_repo_identifier(repo_url)
        if not owner or not repo_name:
            raise ValueError(f"Invalid repository identifier: {repo_url}")
        
        synthesis = {
            'repository': {
                'owner': owner,
                'name': repo_name,
                'url': f"https://github.com/{owner}/{repo_name}",
                'synthesized_at': datetime.now().isoformat()
            },
            'sources': {},
            'consolidated_knowledge': [],
            'summary': {},
            'recommendations': []
        }
        
        try:
            # 1. Repository Analysis
            logger.info("Analyzing repository structure and metadata...")
            repo_analysis = self.repo_analyzer.analyze_repository(
                repo_url, deep_analysis=comprehensive
            )
            synthesis['sources']['repository'] = repo_analysis
            
            # 2. Documentation Import
            logger.info("Importing repository documentation...")
            docs_analysis = self.docs_importer.import_documentation(owner, repo_name)
            synthesis['sources']['documentation'] = docs_analysis
            
            # 3. Commit Analysis (if comprehensive)
            if comprehensive:
                logger.info("Analyzing commit patterns and history...")
                commit_analysis = self.commit_parser.analyze_commits(
                    owner, repo_name, limit=200, deep_analysis=True
                )
                synthesis['sources']['commits'] = commit_analysis
            
            # 4. Issue Analysis (if comprehensive)
            if comprehensive:
                logger.info("Extracting knowledge from issues...")
                issue_analysis = self.issue_processor.extract_issues_knowledge(
                    owner, repo_name, states=['closed'], limit=100
                )
                synthesis['sources']['issues'] = issue_analysis
                
                logger.info("Extracting knowledge from pull requests...")
                pr_analysis = self.issue_processor.extract_pr_knowledge(
                    owner, repo_name, states=['closed'], limit=50
                )
                synthesis['sources']['pull_requests'] = pr_analysis
            
            # 5. Synthesize consolidated knowledge
            synthesis['consolidated_knowledge'] = self._consolidate_knowledge_items(synthesis['sources'])
            
            # 6. Generate summary
            synthesis['summary'] = self._generate_synthesis_summary(synthesis)
            
            # 7. Generate recommendations
            synthesis['recommendations'] = self._generate_recommendations(synthesis)
            
            logger.info(f"Knowledge synthesis complete: {len(synthesis['consolidated_knowledge'])} total knowledge items")
            
        except Exception as e:
            logger.error(f"Error during knowledge synthesis: {e}")
            synthesis['error'] = str(e)
        
        return synthesis
    
    def _parse_repo_identifier(self, repo_identifier: str) -> tuple:
        """Parse repository identifier into owner and repo name"""
        try:
            if repo_identifier.startswith('https://github.com/'):
                path = repo_identifier.replace('https://github.com/', '').replace('.git', '')
                owner, repo = path.split('/', 1)
                return owner, repo
            elif repo_identifier.startswith('git@github.com:'):
                path = repo_identifier.split(':')[1].replace('.git', '')
                owner, repo = path.split('/', 1)
                return owner, repo
            elif '/' in repo_identifier and not repo_identifier.startswith('http'):
                owner, repo = repo_identifier.split('/', 1)
                return owner, repo
            else:
                return None, None
        except:
            return None, None
    
    def _consolidate_knowledge_items(self, sources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Consolidate knowledge items from all sources"""
        all_knowledge = []
        
        # Collect all knowledge items
        for source_name, source_data in sources.items():
            if 'knowledge_items' in source_data:
                for item in source_data['knowledge_items']:
                    # Add source information
                    item['analysis_source'] = source_name
                    all_knowledge.append(item)
        
        # Deduplicate similar items
        deduplicated = self._deduplicate_knowledge_items(all_knowledge)
        
        # Rank by importance and recency
        ranked = sorted(deduplicated, key=lambda x: (x.get('importance', 5), x.get('created_at', '')), reverse=True)
        
        return ranked
    
    def _deduplicate_knowledge_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or very similar knowledge items"""
        deduplicated = []
        seen_content = set()
        
        for item in items:
            content = item.get('content', '').lower()
            # Simple deduplication based on content similarity
            content_key = content[:100]  # First 100 characters as key
            
            if content_key not in seen_content:
                seen_content.add(content_key)
                deduplicated.append(item)
        
        return deduplicated
    
    def _generate_synthesis_summary(self, synthesis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the knowledge synthesis"""
        repo_info = synthesis['repository']
        sources = synthesis['sources']
        knowledge_items = synthesis['consolidated_knowledge']
        
        summary = {
            'repository_overview': {},
            'knowledge_statistics': {},
            'key_insights': [],
            'technology_stack': [],
            'development_patterns': {}
        }
        
        # Repository overview
        if 'repository' in sources and sources['repository'].get('metadata'):
            metadata = sources['repository']['metadata']
            summary['repository_overview'] = {
                'description': metadata.get('description', ''),
                'primary_language': metadata.get('language', ''),
                'size': metadata.get('size', 0),
                'stars': metadata.get('stars', 0),
                'activity': {
                    'last_updated': metadata.get('updated_at', ''),
                    'is_active': self._is_repository_active(metadata)
                },
                'maturity': self._assess_repository_maturity(metadata, sources)
            }
        
        # Knowledge statistics
        summary['knowledge_statistics'] = {
            'total_items': len(knowledge_items),
            'by_category': self._count_by_category(knowledge_items),
            'by_source': self._count_by_source(knowledge_items),
            'importance_distribution': self._analyze_importance_distribution(knowledge_items)
        }
        
        # Technology stack
        tech_items = [item for item in knowledge_items if item.get('category') in ['technology', 'technology-issues']]
        summary['technology_stack'] = self._extract_technology_summary(tech_items, sources)
        
        # Key insights (highest importance items)
        high_importance = [item for item in knowledge_items if item.get('importance', 0) >= 8]
        summary['key_insights'] = [
            {
                'content': item['content'][:200] + '...' if len(item['content']) > 200 else item['content'],
                'category': item.get('category', 'unknown'),
                'importance': item.get('importance', 0),
                'source': item.get('analysis_source', 'unknown')
            }
            for item in high_importance[:10]
        ]
        
        # Development patterns
        summary['development_patterns'] = self._analyze_development_patterns(sources)
        
        return summary
    
    def _is_repository_active(self, metadata: Dict[str, Any]) -> bool:
        """Determine if repository is actively maintained"""
        last_update = metadata.get('updated_at', '')
        if last_update:
            try:
                last_date = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                days_since_update = (datetime.now() - last_date.replace(tzinfo=None)).days
                return days_since_update < 90  # Active if updated in last 90 days
            except:
                pass
        return False
    
    def _assess_repository_maturity(self, metadata: Dict[str, Any], sources: Dict[str, Any]) -> str:
        """Assess repository maturity level"""
        stars = metadata.get('stars', 0)
        age_days = 0
        
        created_at = metadata.get('created_at', '')
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                age_days = (datetime.now() - created_date.replace(tzinfo=None)).days
            except:
                pass
        
        has_docs = bool(sources.get('documentation', {}).get('documentation'))
        has_issues = 'issues' in sources and len(sources['issues'].get('issues', [])) > 0
        
        # Simple maturity assessment
        if stars > 1000 and age_days > 365 and has_docs:
            return 'mature'
        elif stars > 100 and age_days > 180:
            return 'established'
        elif age_days > 30 and (has_docs or has_issues):
            return 'developing'
        else:
            return 'early'
    
    def _count_by_category(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count items by category"""
        counts = {}
        for item in items:
            category = item.get('category', 'unknown')
            counts[category] = counts.get(category, 0) + 1
        return counts
    
    def _count_by_source(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count items by analysis source"""
        counts = {}
        for item in items:
            source = item.get('analysis_source', 'unknown')
            counts[source] = counts.get(source, 0) + 1
        return counts
    
    def _analyze_importance_distribution(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of importance scores"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        for item in items:
            importance = item.get('importance', 5)
            if importance >= 8:
                distribution['high'] += 1
            elif importance >= 6:
                distribution['medium'] += 1
            else:
                distribution['low'] += 1
        return distribution
    
    def _extract_technology_summary(self, tech_items: List[Dict[str, Any]], 
                                  sources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract technology stack summary"""
        tech_summary = []
        
        # From repository analysis
        if 'repository' in sources and sources['repository'].get('technologies'):
            for tech in sources['repository']['technologies'][:10]:
                tech_summary.append({
                    'name': tech['name'],
                    'category': tech['category'],
                    'confidence': tech['confidence'],
                    'source': 'repository_analysis'
                })
        
        # From commit analysis
        if 'commits' in sources and sources['commits'].get('technology_trends'):
            tech_mentions = sources['commits']['technology_trends'].get('technology_mentions', {})
            for tech, mentions in sorted(tech_mentions.items(), key=lambda x: x[1], reverse=True)[:5]:
                tech_summary.append({
                    'name': tech,
                    'category': 'commit_mentions',
                    'mentions': mentions,
                    'source': 'commit_analysis'
                })
        
        return tech_summary
    
    def _analyze_development_patterns(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze development patterns from all sources"""
        patterns = {
            'commit_patterns': {},
            'issue_patterns': {},
            'architecture_patterns': [],
            'development_velocity': {}
        }
        
        # Commit patterns
        if 'commits' in sources:
            commit_data = sources['commits']
            if 'patterns' in commit_data:
                patterns['commit_patterns'] = {
                    'categories': dict(commit_data['patterns'].get('categories', {})),
                    'frequent_words': commit_data['patterns'].get('frequent_words', [])[:10]
                }
        
        # Issue patterns
        if 'issues' in sources:
            issue_data = sources['issues']
            if 'patterns' in issue_data:
                patterns['issue_patterns'] = {
                    'categories': dict(issue_data['patterns'].get('categories', {})),
                    'priorities': dict(issue_data['patterns'].get('priorities', {}))
                }
        
        # Architecture patterns
        if 'repository' in sources:
            repo_data = sources['repository']
            if 'architecture' in repo_data:
                patterns['architecture_patterns'] = repo_data['architecture'].get('patterns', [])
        
        return patterns
    
    def _generate_recommendations(self, synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis"""
        recommendations = []
        sources = synthesis['sources']
        summary = synthesis['summary']
        
        # Documentation recommendations
        if 'documentation' in sources:
            doc_count = len(sources['documentation'].get('documentation', {}))
            if doc_count < 3:
                recommendations.append({
                    'type': 'documentation',
                    'priority': 'medium',
                    'title': 'Improve Documentation',
                    'description': 'Consider adding more comprehensive documentation to help users understand and contribute to the project.',
                    'rationale': f'Only {doc_count} documentation files found'
                })
        
        # Issue resolution recommendations
        if 'issues' in sources:
            resolution_times = sources['issues'].get('patterns', {}).get('resolution_times', [])
            if resolution_times:
                avg_resolution = sum(rt['days'] for rt in resolution_times) / len(resolution_times)
                if avg_resolution > 30:
                    recommendations.append({
                        'type': 'maintenance',
                        'priority': 'high',
                        'title': 'Improve Issue Resolution Time',
                        'description': f'Average issue resolution time is {avg_resolution:.1f} days. Consider triaging and addressing issues more quickly.',
                        'rationale': 'Long resolution times may indicate maintenance issues'
                    })
        
        # Technology modernization
        tech_stack = summary.get('technology_stack', [])
        older_technologies = [tech for tech in tech_stack if tech['name'] in ['jquery', 'bower', 'grunt']]
        if older_technologies:
            recommendations.append({
                'type': 'technology',
                'priority': 'low',
                'title': 'Consider Technology Updates',
                'description': f'Some older technologies detected: {", ".join([t["name"] for t in older_technologies])}. Consider modernizing.',
                'rationale': 'Keeping dependencies current improves security and maintainability'
            })
        
        # Activity recommendations
        repo_overview = summary.get('repository_overview', {})
        if not repo_overview.get('activity', {}).get('is_active'):
            recommendations.append({
                'type': 'maintenance',
                'priority': 'medium',
                'title': 'Repository Activity',
                'description': 'Repository appears to have low recent activity. Consider regular maintenance or archiving if no longer maintained.',
                'rationale': 'Inactive repositories may have security or compatibility issues'
            })
        
        return recommendations