#!/usr/bin/env python3
"""
Commit Intelligence Parser for Universal AI Memory System
Analyzes git commits to extract patterns, solutions, and knowledge
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, Counter
import logging

from .github_client import GitHubClient

logger = logging.getLogger(__name__)

class CommitIntelligenceParser:
    """Analyzes git commits to extract intelligence and patterns"""
    
    def __init__(self, github_client: GitHubClient):
        """
        Initialize commit parser
        
        Args:
            github_client: Configured GitHub API client
        """
        self.github = github_client
        
        # Commit message patterns for categorization
        self.commit_patterns = {
            'fix': [
                r'\b(fix|fixed|fixes|fixing|resolve|resolved|resolves|close|closed|closes)\b',
                r'\b(bug|issue|error|problem)\b',
                r'#\d+',  # Issue references
            ],
            'feature': [
                r'\b(add|added|adding|implement|implemented|implementing|create|created|creating)\b',
                r'\b(feature|functionality|capability)\b',
                r'\b(new|introduce|initial)\b'
            ],
            'refactor': [
                r'\b(refactor|refactored|refactoring|restructure|cleanup|clean up)\b',
                r'\b(improve|improved|improving|optimize|optimized|optimizing)\b',
                r'\b(reorganize|simplify|streamline)\b'
            ],
            'update': [
                r'\b(update|updated|updating|upgrade|upgraded|upgrading)\b',
                r'\b(modify|modified|modifying|change|changed|changing)\b',
                r'\b(version|dependency|dependencies)\b'
            ],
            'docs': [
                r'\b(docs|documentation|readme|comment|comments|commenting)\b',
                r'\b(document|documented|documenting)\b'
            ],
            'test': [
                r'\b(test|tests|testing|spec|specs)\b',
                r'\b(coverage|unit|integration)\b'
            ],
            'config': [
                r'\b(config|configuration|settings|setup|env|environment)\b',
                r'\b(deploy|deployment|build|ci|cd)\b'
            ],
            'security': [
                r'\b(security|secure|vulnerability|auth|authentication|permission)\b',
                r'\b(encrypt|decrypt|hash|ssl|tls)\b'
            ]
        }
        
        # Technology keywords for tagging
        self.tech_keywords = {
            'python', 'javascript', 'typescript', 'react', 'vue', 'angular', 'node',
            'django', 'flask', 'express', 'fastapi', 'spring', 'rails',
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'api', 'rest', 'graphql', 'websocket', 'grpc',
            'css', 'html', 'scss', 'sass', 'bootstrap', 'tailwind',
            'webpack', 'vite', 'rollup', 'babel', 'eslint',
            'pytest', 'jest', 'cypress', 'selenium', 'junit'
        }
        
        # File patterns for affected areas
        self.file_patterns = {
            'frontend': [r'\.jsx?$', r'\.tsx?$', r'\.vue$', r'\.css$', r'\.scss$', r'\.html$'],
            'backend': [r'\.py$', r'\.java$', r'\.php$', r'\.rb$', r'\.go$', r'\.rs$'],
            'database': [r'migration', r'schema', r'\.sql$', r'models?\.py$'],
            'config': [r'config', r'\.yml$', r'\.yaml$', r'\.json$', r'\.env', r'docker'],
            'tests': [r'test', r'spec', r'\.test\.', r'\.spec\.'],
            'docs': [r'readme', r'\.md$', r'docs?/', r'documentation']
        }
    
    def analyze_commits(self, owner: str, repo_name: str, since: Optional[datetime] = None, 
                       limit: int = 200, deep_analysis: bool = True) -> Dict[str, Any]:
        """
        Analyze repository commits for patterns and knowledge
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            since: Only analyze commits since this date
            limit: Maximum number of commits to analyze
            deep_analysis: Whether to perform detailed pattern analysis
            
        Returns:
            Dictionary containing commit analysis results
        """
        logger.info(f"Analyzing commits for {owner}/{repo_name} (limit: {limit})")
        
        # Default to analyzing last 90 days if no since date provided
        if not since:
            since = datetime.now() - timedelta(days=90)
        
        # Get commits from GitHub
        commits = self.github.get_commits(owner, repo_name, since=since, limit=limit)
        if not commits:
            logger.warning("No commits found for analysis")
            return {'commits': [], 'analysis': {}}
        
        analysis = {
            'repository': {'owner': owner, 'name': repo_name},
            'period': {
                'since': since.isoformat(),
                'until': datetime.now().isoformat(),
                'total_commits': len(commits)
            },
            'commits': commits,
            'patterns': {},
            'knowledge_items': []
        }
        
        # Perform analysis
        analysis['patterns'] = self._analyze_commit_patterns(commits)
        
        if deep_analysis:
            analysis['hotspots'] = self._identify_hotspots(commits)
            analysis['developer_insights'] = self._analyze_developer_patterns(commits)
            analysis['technology_trends'] = self._analyze_technology_trends(commits)
        
        # Generate knowledge items
        analysis['knowledge_items'] = self._generate_commit_knowledge_items(analysis)
        
        logger.info(f"Commit analysis complete: {len(analysis['knowledge_items'])} knowledge items extracted")
        return analysis
    
    def _analyze_commit_patterns(self, commits: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in commit messages"""
        patterns = {
            'categories': defaultdict(int),
            'fix_patterns': [],
            'feature_patterns': [],
            'frequent_words': [],
            'issue_references': [],
            'commit_frequency': defaultdict(int)
        }
        
        all_messages = []
        
        for commit in commits:
            message = commit.get('commit', {}).get('message', '').lower()
            if not message:
                continue
            
            all_messages.append(message)
            
            # Categorize commit
            category = self._categorize_commit_message(message)
            patterns['categories'][category] += 1
            
            # Extract issue references
            issue_refs = re.findall(r'#(\d+)', message)
            patterns['issue_references'].extend(issue_refs)
            
            # Track commit frequency by date
            commit_date = commit.get('commit', {}).get('author', {}).get('date', '')
            if commit_date:
                date_key = commit_date[:10]  # YYYY-MM-DD
                patterns['commit_frequency'][date_key] += 1
            
            # Extract fix patterns
            if category == 'fix':
                fix_pattern = self._extract_fix_pattern(message, commit)
                if fix_pattern:
                    patterns['fix_patterns'].append(fix_pattern)
            
            # Extract feature patterns
            elif category == 'feature':
                feature_pattern = self._extract_feature_pattern(message, commit)
                if feature_pattern:
                    patterns['feature_patterns'].append(feature_pattern)
        
        # Analyze frequent words
        if all_messages:
            patterns['frequent_words'] = self._extract_frequent_words(all_messages)
        
        return patterns
    
    def _categorize_commit_message(self, message: str) -> str:
        """Categorize commit message based on patterns"""
        message_lower = message.lower()
        
        # Score each category
        scores = {}
        for category, patterns_list in self.commit_patterns.items():
            score = 0
            for pattern in patterns_list:
                matches = len(re.findall(pattern, message_lower))
                score += matches
            scores[category] = score
        
        # Return category with highest score
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category
        
        return 'other'
    
    def _extract_fix_pattern(self, message: str, commit: Dict) -> Optional[Dict[str, Any]]:
        """Extract pattern information from fix commits"""
        pattern = {
            'message': message,
            'sha': commit.get('sha', '')[:8],
            'date': commit.get('commit', {}).get('author', {}).get('date', ''),
            'files_changed': [],
            'technologies': [],
            'issue_refs': re.findall(r'#(\d+)', message),
            'fix_type': 'unknown'
        }
        
        # Determine fix type
        if re.search(r'\b(crash|crashing|segfault|exception)\b', message.lower()):
            pattern['fix_type'] = 'crash_fix'
        elif re.search(r'\b(performance|slow|speed|optimize)\b', message.lower()):
            pattern['fix_type'] = 'performance_fix'
        elif re.search(r'\b(security|vulnerability|exploit)\b', message.lower()):
            pattern['fix_type'] = 'security_fix'
        elif re.search(r'\b(ui|interface|display|render)\b', message.lower()):
            pattern['fix_type'] = 'ui_fix'
        elif re.search(r'\b(api|endpoint|request|response)\b', message.lower()):
            pattern['fix_type'] = 'api_fix'
        elif re.search(r'\b(database|db|query|migration)\b', message.lower()):
            pattern['fix_type'] = 'database_fix'
        
        # Extract technologies mentioned
        for tech in self.tech_keywords:
            if tech in message.lower():
                pattern['technologies'].append(tech)
        
        return pattern
    
    def _extract_feature_pattern(self, message: str, commit: Dict) -> Optional[Dict[str, Any]]:
        """Extract pattern information from feature commits"""
        pattern = {
            'message': message,
            'sha': commit.get('sha', '')[:8],
            'date': commit.get('commit', {}).get('author', {}).get('date', ''),
            'feature_type': 'unknown',
            'technologies': [],
            'scope': 'unknown'
        }
        
        # Determine feature type
        if re.search(r'\b(api|endpoint|service)\b', message.lower()):
            pattern['feature_type'] = 'api_feature'
        elif re.search(r'\b(ui|interface|component|page)\b', message.lower()):
            pattern['feature_type'] = 'ui_feature'
        elif re.search(r'\b(auth|login|signup|permission)\b', message.lower()):
            pattern['feature_type'] = 'auth_feature'
        elif re.search(r'\b(database|model|schema)\b', message.lower()):
            pattern['feature_type'] = 'data_feature'
        elif re.search(r'\b(test|testing|spec)\b', message.lower()):
            pattern['feature_type'] = 'test_feature'
        elif re.search(r'\b(deploy|deployment|build|ci)\b', message.lower()):
            pattern['feature_type'] = 'deployment_feature'
        
        # Extract technologies
        for tech in self.tech_keywords:
            if tech in message.lower():
                pattern['technologies'].append(tech)
        
        return pattern
    
    def _extract_frequent_words(self, messages: List[str], min_length: int = 3, 
                               top_n: int = 20) -> List[Tuple[str, int]]:
        """Extract most frequent meaningful words from commit messages"""
        # Stop words to exclude
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use',
            'add', 'added', 'fix', 'fixed', 'update', 'updated', 'remove', 'removed',
            'commit', 'merge', 'branch', 'pull', 'request', 'pr'
        }
        
        # Extract words
        word_counts = Counter()
        for message in messages:
            # Remove punctuation and split
            words = re.findall(r'\b[a-z]+\b', message.lower())
            for word in words:
                if len(word) >= min_length and word not in stop_words:
                    word_counts[word] += 1
        
        return word_counts.most_common(top_n)
    
    def _identify_hotspots(self, commits: List[Dict]) -> Dict[str, Any]:
        """Identify code hotspots based on commit frequency"""
        hotspots = {
            'files': defaultdict(int),
            'directories': defaultdict(int),
            'areas': defaultdict(int)
        }
        
        for commit in commits:
            # Note: GitHub API doesn't include file changes in commit list
            # This would require additional API calls to get commit details
            # For now, we'll extract file info from commit messages when possible
            
            message = commit.get('commit', {}).get('message', '').lower()
            
            # Try to extract file references from commit messages
            file_refs = re.findall(r'[\w/]+\.\w+', message)
            for file_ref in file_refs:
                if '.' in file_ref and len(file_ref.split('/')) <= 5:  # Reasonable path
                    hotspots['files'][file_ref] += 1
                    
                    # Extract directory
                    if '/' in file_ref:
                        directory = '/'.join(file_ref.split('/')[:-1])
                        hotspots['directories'][directory] += 1
                    
                    # Categorize by area
                    for area, patterns in self.file_patterns.items():
                        if any(re.search(pattern, file_ref.lower()) for pattern in patterns):
                            hotspots['areas'][area] += 1
                            break
        
        # Convert to sorted lists
        hotspots['files'] = sorted(hotspots['files'].items(), key=lambda x: x[1], reverse=True)[:20]
        hotspots['directories'] = sorted(hotspots['directories'].items(), key=lambda x: x[1], reverse=True)[:10]
        hotspots['areas'] = sorted(hotspots['areas'].items(), key=lambda x: x[1], reverse=True)
        
        return hotspots
    
    def _analyze_developer_patterns(self, commits: List[Dict]) -> Dict[str, Any]:
        """Analyze developer contribution patterns"""
        developer_stats = defaultdict(lambda: {
            'commits': 0,
            'categories': defaultdict(int),
            'recent_activity': [],
            'specializations': []
        })
        
        for commit in commits:
            author = commit.get('commit', {}).get('author', {})
            author_name = author.get('name', 'Unknown')
            
            if author_name == 'Unknown':
                continue
            
            dev_stats = developer_stats[author_name]
            dev_stats['commits'] += 1
            
            # Categorize commit
            message = commit.get('commit', {}).get('message', '').lower()
            category = self._categorize_commit_message(message)
            dev_stats['categories'][category] += 1
            
            # Track recent activity
            commit_date = commit.get('commit', {}).get('author', {}).get('date', '')
            if commit_date:
                dev_stats['recent_activity'].append({
                    'date': commit_date,
                    'message': commit.get('commit', {}).get('message', '')[:100],
                    'category': category
                })
        
        # Determine specializations for each developer
        for author_name, stats in developer_stats.items():
            if stats['commits'] >= 3:  # Minimum commits to determine specialization
                # Find most common categories
                top_categories = sorted(stats['categories'].items(), 
                                      key=lambda x: x[1], reverse=True)[:3]
                stats['specializations'] = [cat for cat, count in top_categories if count >= 2]
        
        # Convert to regular dict and sort by commit count
        result = dict(developer_stats)
        result = dict(sorted(result.items(), key=lambda x: x[1]['commits'], reverse=True))
        
        return result
    
    def _analyze_technology_trends(self, commits: List[Dict]) -> Dict[str, Any]:
        """Analyze technology usage trends in commits"""
        tech_trends = {
            'technology_mentions': defaultdict(int),
            'trend_over_time': defaultdict(lambda: defaultdict(int)),
            'emerging_technologies': [],
            'declining_technologies': []
        }
        
        for commit in commits:
            message = commit.get('commit', {}).get('message', '').lower()
            commit_date = commit.get('commit', {}).get('author', {}).get('date', '')
            
            # Extract month for trending
            month_key = commit_date[:7] if commit_date else 'unknown'  # YYYY-MM
            
            # Count technology mentions
            for tech in self.tech_keywords:
                if tech in message:
                    tech_trends['technology_mentions'][tech] += 1
                    tech_trends['trend_over_time'][month_key][tech] += 1
        
        # Analyze trends (simplified - would need more sophisticated analysis for production)
        if len(tech_trends['trend_over_time']) >= 2:
            sorted_months = sorted(tech_trends['trend_over_time'].keys())
            
            if len(sorted_months) >= 2:
                recent_month = sorted_months[-1]
                previous_month = sorted_months[-2]
                
                recent_techs = tech_trends['trend_over_time'][recent_month]
                previous_techs = tech_trends['trend_over_time'][previous_month]
                
                # Find emerging technologies (appeared recently)
                for tech in recent_techs:
                    if tech not in previous_techs and recent_techs[tech] >= 2:
                        tech_trends['emerging_technologies'].append(tech)
                
                # Find declining technologies (less usage recently)
                for tech in previous_techs:
                    if tech in recent_techs:
                        if recent_techs[tech] < previous_techs[tech] * 0.5:  # 50% decline
                            tech_trends['declining_technologies'].append(tech)
        
        return tech_trends
    
    def _generate_commit_knowledge_items(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate knowledge items from commit analysis"""
        knowledge_items = []
        repo_info = analysis['repository']
        patterns = analysis['patterns']
        
        # Overall commit patterns
        if patterns['categories']:
            category_summary = ', '.join([f"{cat}: {count}" for cat, count 
                                        in sorted(patterns['categories'].items(), 
                                                key=lambda x: x[1], reverse=True)[:5]])
            
            knowledge_items.append({
                'content': f"Commit patterns for {repo_info['name']}: {category_summary}",
                'category': 'development-patterns',
                'tags': ['github', 'commits', 'patterns', repo_info['name'].lower()],
                'importance': 6,
                'source': 'github_commit_analysis',
                'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/commits",
                'metadata': {
                    'repo_name': repo_info['name'],
                    'analysis_period': analysis['period'],
                    'commit_categories': dict(patterns['categories'])
                }
            })
        
        # Fix patterns knowledge
        if patterns['fix_patterns']:
            fix_types = Counter([fp['fix_type'] for fp in patterns['fix_patterns']])
            common_fixes = ', '.join([f"{fix_type}: {count}" for fix_type, count 
                                    in fix_types.most_common(3)])
            
            knowledge_items.append({
                'content': f"Common fix patterns in {repo_info['name']}: {common_fixes}",
                'category': 'debugging',
                'tags': ['github', 'fixes', 'debugging', repo_info['name'].lower()],
                'importance': 7,
                'source': 'github_fix_analysis',
                'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/commits",
                'metadata': {
                    'repo_name': repo_info['name'],
                    'fix_patterns': patterns['fix_patterns'][:10]  # Limit to recent fixes
                }
            })
        
        # Technology trends
        if 'technology_trends' in analysis:
            tech_trends = analysis['technology_trends']
            if tech_trends['technology_mentions']:
                top_techs = sorted(tech_trends['technology_mentions'].items(), 
                                 key=lambda x: x[1], reverse=True)[:7]
                tech_list = ', '.join([f"{tech} ({count})" for tech, count in top_techs])
                
                knowledge_items.append({
                    'content': f"Technology usage in {repo_info['name']}: {tech_list}",
                    'category': 'technology',
                    'tags': ['github', 'technology', 'usage'] + [tech for tech, _ in top_techs[:5]],
                    'importance': 6,
                    'source': 'github_tech_analysis',
                    'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/commits",
                    'metadata': {
                        'repo_name': repo_info['name'],
                        'technology_mentions': dict(tech_trends['technology_mentions'])
                    }
                })
        
        # Hotspots knowledge
        if 'hotspots' in analysis:
            hotspots = analysis['hotspots']
            if hotspots['areas']:
                active_areas = ', '.join([f"{area} ({count})" for area, count 
                                        in hotspots['areas'][:5]])
                
                knowledge_items.append({
                    'content': f"Development hotspots in {repo_info['name']}: {active_areas}",
                    'category': 'development-insights',
                    'tags': ['github', 'hotspots', 'development', repo_info['name'].lower()],
                    'importance': 5,
                    'source': 'github_hotspot_analysis',
                    'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/commits",
                    'metadata': {
                        'repo_name': repo_info['name'],
                        'hotspots': hotspots
                    }
                })
        
        # Recent high-impact commits
        recent_commits = analysis['commits'][:5]  # Most recent 5
        for commit in recent_commits:
            message = commit.get('commit', {}).get('message', '')
            if len(message) > 30:  # Skip trivial commits
                category = self._categorize_commit_message(message.lower())
                if category in ['fix', 'feature']:  # Focus on important commits
                    
                    knowledge_items.append({
                        'content': f"Recent {category} in {repo_info['name']}: {message[:200]}",
                        'category': 'recent-development',
                        'tags': ['github', 'recent', category, repo_info['name'].lower()],
                        'importance': 5,
                        'source': 'github_recent_commit',
                        'source_url': commit.get('html_url', ''),
                        'metadata': {
                            'repo_name': repo_info['name'],
                            'commit_sha': commit.get('sha', ''),
                            'commit_date': commit.get('commit', {}).get('author', {}).get('date', ''),
                            'category': category
                        }
                    })
        
        return knowledge_items