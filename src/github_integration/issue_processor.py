#!/usr/bin/env python3
"""
Issue and PR Knowledge Extractor for Universal AI Memory System
Extracts knowledge from GitHub issues and pull requests
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, Counter
import logging

from .github_client import GitHubClient

logger = logging.getLogger(__name__)

class IssueKnowledgeExtractor:
    """Extracts knowledge from GitHub issues and pull requests"""
    
    def __init__(self, github_client: GitHubClient):
        """
        Initialize issue knowledge extractor
        
        Args:
            github_client: Configured GitHub API client
        """
        self.github = github_client
        
        # Issue classification patterns
        self.issue_patterns = {
            'bug': [
                r'\b(bug|error|crash|fail|broken|not working|doesn\'t work)\b',
                r'\b(exception|traceback|stack trace)\b',
                r'\b(unexpected|incorrect|wrong)\b'
            ],
            'feature_request': [
                r'\b(feature|enhancement|improvement|suggestion)\b',
                r'\b(would like|could you|please add|add support)\b',
                r'\b(new|implement|create|build)\b'
            ],
            'question': [
                r'\b(question|how to|how do|help|support)\b',
                r'\b(confused|understand|clarification)\b',
                r'\?\s*$'  # Ends with question mark
            ],
            'documentation': [
                r'\b(docs|documentation|readme|guide|tutorial)\b',
                r'\b(example|usage|instruction)\b'
            ],
            'performance': [
                r'\b(performance|slow|speed|optimization|memory|cpu)\b',
                r'\b(lag|delay|timeout|bottleneck)\b'
            ],
            'security': [
                r'\b(security|vulnerability|exploit|attack)\b',
                r'\b(auth|authentication|permission|access)\b'
            ]
        }
        
        # Solution patterns in comments
        self.solution_patterns = [
            r'(?i)\b(solved|fixed|resolved|solution|workaround|fix)\b.*?(?=\n\n|\n$|$)',
            r'(?i)\btry this\b.*?(?=\n\n|\n$|$)',
            r'(?i)\bthe issue is\b.*?(?=\n\n|\n$|$)',
            r'(?i)\bhere\'s how\b.*?(?=\n\n|\n$|$)',
            r'(?i)\byou need to\b.*?(?=\n\n|\n$|$)'
        ]
        
        # Code block patterns
        self.code_patterns = [
            r'```[\s\S]*?```',  # Triple backtick code blocks
            r'`[^`\n]+`',       # Inline code
            r'^\s{4,}.*$'       # Indented code (multiline)
        ]
        
        # Priority keywords
        self.priority_keywords = {
            'critical': ['critical', 'urgent', 'blocker', 'breaking', 'production', 'security'],
            'high': ['high priority', 'important', 'major', 'regression', 'data loss'],
            'medium': ['enhancement', 'improvement', 'feature request', 'medium'],
            'low': ['minor', 'low priority', 'nice to have', 'cleanup', 'documentation']
        }
        
        # Technology detection
        self.tech_keywords = {
            'python', 'javascript', 'typescript', 'react', 'vue', 'angular', 'node',
            'django', 'flask', 'express', 'fastapi', 'spring', 'rails',
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'api', 'rest', 'graphql', 'websocket', 'grpc',
            'css', 'html', 'scss', 'sass', 'bootstrap', 'tailwind'
        }
    
    def extract_issues_knowledge(self, owner: str, repo_name: str, 
                                since: Optional[datetime] = None,
                                states: List[str] = ['closed'],
                                limit: int = 100) -> Dict[str, Any]:
        """
        Extract knowledge from repository issues
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            since: Only analyze issues updated since this date
            states: Issue states to include ('open', 'closed', 'all')
            limit: Maximum number of issues to analyze
            
        Returns:
            Dictionary containing extracted knowledge
        """
        logger.info(f"Extracting knowledge from issues in {owner}/{repo_name}")
        
        # Default to analyzing last 180 days for closed issues
        if not since and 'closed' in states:
            since = datetime.now() - timedelta(days=180)
        
        knowledge = {
            'repository': {'owner': owner, 'name': repo_name},
            'analysis_period': {
                'since': since.isoformat() if since else None,
                'states': states,
                'total_analyzed': 0
            },
            'issues': [],
            'patterns': {},
            'solutions': [],
            'knowledge_items': []
        }
        
        # Get issues from GitHub
        all_issues = []
        for state in states:
            state_issues = self.github.get_issues(
                owner, repo_name, state=state, since=since, limit=limit//len(states)
            )
            all_issues.extend(state_issues)
        
        if not all_issues:
            logger.warning("No issues found for analysis")
            return knowledge
        
        knowledge['issues'] = all_issues
        knowledge['analysis_period']['total_analyzed'] = len(all_issues)
        
        # Analyze issues
        knowledge['patterns'] = self._analyze_issue_patterns(all_issues)
        knowledge['solutions'] = self._extract_solutions(all_issues)
        
        # Generate knowledge items
        knowledge['knowledge_items'] = self._generate_issue_knowledge_items(knowledge)
        
        logger.info(f"Issue analysis complete: {len(knowledge['knowledge_items'])} knowledge items extracted")
        return knowledge
    
    def extract_pr_knowledge(self, owner: str, repo_name: str,
                           since: Optional[datetime] = None,
                           states: List[str] = ['closed'],
                           limit: int = 50) -> Dict[str, Any]:
        """
        Extract knowledge from repository pull requests
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            since: Only analyze PRs updated since this date
            states: PR states to include
            limit: Maximum number of PRs to analyze
            
        Returns:
            Dictionary containing extracted knowledge
        """
        logger.info(f"Extracting knowledge from pull requests in {owner}/{repo_name}")
        
        # Default to analyzing last 90 days for merged PRs
        if not since:
            since = datetime.now() - timedelta(days=90)
        
        knowledge = {
            'repository': {'owner': owner, 'name': repo_name},
            'analysis_period': {
                'since': since.isoformat() if since else None,
                'states': states,
                'total_analyzed': 0
            },
            'pull_requests': [],
            'patterns': {},
            'implementations': [],
            'knowledge_items': []
        }
        
        # Get PRs from GitHub
        all_prs = []
        for state in states:
            state_prs = self.github.get_pull_requests(
                owner, repo_name, state=state, since=since, limit=limit//len(states)
            )
            all_prs.extend(state_prs)
        
        if not all_prs:
            logger.warning("No pull requests found for analysis")
            return knowledge
        
        knowledge['pull_requests'] = all_prs
        knowledge['analysis_period']['total_analyzed'] = len(all_prs)
        
        # Analyze PRs
        knowledge['patterns'] = self._analyze_pr_patterns(all_prs)
        knowledge['implementations'] = self._extract_implementations(all_prs)
        
        # Generate knowledge items
        knowledge['knowledge_items'] = self._generate_pr_knowledge_items(knowledge)
        
        logger.info(f"PR analysis complete: {len(knowledge['knowledge_items'])} knowledge items extracted")
        return knowledge
    
    def _analyze_issue_patterns(self, issues: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in issues"""
        patterns = {
            'categories': defaultdict(int),
            'priorities': defaultdict(int),
            'technologies': defaultdict(int),
            'common_problems': [],
            'resolution_times': [],
            'labels': defaultdict(int),
            'author_activity': defaultdict(int)
        }
        
        for issue in issues:
            title = issue.get('title', '').lower()
            body = issue.get('body', '').lower() if issue.get('body') else ''
            combined_text = f"{title} {body}"
            
            # Categorize issue
            category = self._categorize_issue(combined_text)
            patterns['categories'][category] += 1
            
            # Determine priority
            priority = self._determine_priority(combined_text, issue.get('labels', []))
            patterns['priorities'][priority] += 1
            
            # Extract technologies
            for tech in self.tech_keywords:
                if tech in combined_text:
                    patterns['technologies'][tech] += 1
            
            # Track labels
            for label in issue.get('labels', []):
                label_name = label.get('name', '').lower()
                patterns['labels'][label_name] += 1
            
            # Track author activity
            author = issue.get('user', {}).get('login', 'unknown')
            patterns['author_activity'][author] += 1
            
            # Calculate resolution time for closed issues
            if issue.get('state') == 'closed':
                created_at = issue.get('created_at')
                closed_at = issue.get('closed_at')
                if created_at and closed_at:
                    try:
                        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        closed = datetime.fromisoformat(closed_at.replace('Z', '+00:00'))
                        resolution_days = (closed - created).days
                        patterns['resolution_times'].append({
                            'issue_number': issue.get('number'),
                            'days': resolution_days,
                            'category': category
                        })
                    except:
                        pass
            
            # Extract common problems
            if category == 'bug' and issue.get('state') == 'closed':
                problem_description = self._extract_problem_description(title, body)
                if problem_description:
                    patterns['common_problems'].append({
                        'issue_number': issue.get('number'),
                        'title': issue.get('title'),
                        'description': problem_description,
                        'url': issue.get('html_url')
                    })
        
        return patterns
    
    def _analyze_pr_patterns(self, prs: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in pull requests"""
        patterns = {
            'categories': defaultdict(int),
            'merge_patterns': defaultdict(int),
            'size_distribution': [],
            'review_patterns': [],
            'author_contributions': defaultdict(int),
            'technologies': defaultdict(int)
        }
        
        for pr in prs:
            title = pr.get('title', '').lower()
            body = pr.get('body', '').lower() if pr.get('body') else ''
            combined_text = f"{title} {body}"
            
            # Categorize PR
            category = self._categorize_pr(combined_text)
            patterns['categories'][category] += 1
            
            # Track merge patterns
            if pr.get('merged_at'):
                patterns['merge_patterns']['merged'] += 1
            elif pr.get('state') == 'closed':
                patterns['merge_patterns']['closed_unmerged'] += 1
            else:
                patterns['merge_patterns']['open'] += 1
            
            # Extract technologies
            for tech in self.tech_keywords:
                if tech in combined_text:
                    patterns['technologies'][tech] += 1
            
            # Track author contributions
            author = pr.get('user', {}).get('login', 'unknown')
            patterns['author_contributions'][author] += 1
            
            # Track PR size (approximation based on title/body content)
            pr_size = 'small'
            if 'major' in combined_text or 'large' in combined_text or 'refactor' in combined_text:
                pr_size = 'large'
            elif 'medium' in combined_text or len(combined_text) > 500:
                pr_size = 'medium'
            
            patterns['size_distribution'].append({
                'pr_number': pr.get('number'),
                'size': pr_size,
                'category': category,
                'changed_files': pr.get('changed_files', 0),
                'additions': pr.get('additions', 0),
                'deletions': pr.get('deletions', 0)
            })
        
        return patterns
    
    def _categorize_issue(self, text: str) -> str:
        """Categorize issue based on content"""
        scores = {}
        for category, patterns_list in self.issue_patterns.items():
            score = 0
            for pattern in patterns_list:
                matches = len(re.findall(pattern, text))
                score += matches
            scores[category] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category
        
        return 'other'
    
    def _categorize_pr(self, text: str) -> str:
        """Categorize pull request based on content"""
        # PR-specific patterns
        pr_patterns = {
            'feature': [
                r'\b(add|implement|create|new feature|feature)\b',
                r'\b(functionality|capability|enhancement)\b'
            ],
            'bugfix': [
                r'\b(fix|fixed|fixes|resolve|bug|error)\b',
                r'\b(issue|problem|crash)\b'
            ],
            'refactor': [
                r'\b(refactor|restructure|cleanup|improve)\b',
                r'\b(optimize|simplify|reorganize)\b'
            ],
            'docs': [
                r'\b(docs|documentation|readme|comment)\b',
                r'\b(update|add|fix).*\b(doc|guide)\b'
            ],
            'test': [
                r'\b(test|testing|spec|coverage)\b',
                r'\b(unit|integration|e2e)\b'
            ],
            'chore': [
                r'\b(chore|update|upgrade|dependency)\b',
                r'\b(version|build|ci|cd)\b'
            ]
        }
        
        scores = {}
        for category, patterns_list in pr_patterns.items():
            score = 0
            for pattern in patterns_list:
                matches = len(re.findall(pattern, text))
                score += matches
            scores[category] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category
        
        return 'other'
    
    def _determine_priority(self, text: str, labels: List[Dict]) -> str:
        """Determine issue priority based on content and labels"""
        # Check labels first
        for label in labels:
            label_name = label.get('name', '').lower()
            for priority, keywords in self.priority_keywords.items():
                if any(keyword in label_name for keyword in keywords):
                    return priority
        
        # Analyze text content
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return priority
        
        return 'medium'  # default
    
    def _extract_problem_description(self, title: str, body: str) -> Optional[str]:
        """Extract concise problem description from issue"""
        # Try to find the problem statement in the body
        problem_patterns = [
            r'(?i)problem\s*:?\s*(.+?)(?:\n|$)',
            r'(?i)issue\s*:?\s*(.+?)(?:\n|$)',
            r'(?i)bug\s*:?\s*(.+?)(?:\n|$)',
            r'(?i)error\s*:?\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in problem_patterns:
            match = re.search(pattern, body)
            if match:
                description = match.group(1).strip()
                if len(description) > 20:  # Meaningful description
                    return description[:200] + '...' if len(description) > 200 else description
        
        # Fallback to title if no pattern found
        if len(title) > 10:
            return title[:200] + '...' if len(title) > 200 else title
        
        return None
    
    def _extract_solutions(self, issues: List[Dict]) -> List[Dict[str, Any]]:
        """Extract solutions from closed issues"""
        solutions = []
        
        for issue in issues:
            if issue.get('state') != 'closed':
                continue
            
            # Note: GitHub API doesn't include comments in issue list
            # In a full implementation, we would fetch comments separately
            # For now, we'll extract what we can from the issue body
            
            body = issue.get('body', '') if issue.get('body') else ''
            title = issue.get('title', '')
            
            # Look for solution patterns in the issue body
            solution_text = self._extract_solution_from_text(body)
            
            if solution_text:
                solutions.append({
                    'issue_number': issue.get('number'),
                    'title': title,
                    'solution': solution_text,
                    'url': issue.get('html_url'),
                    'labels': [label.get('name') for label in issue.get('labels', [])],
                    'category': self._categorize_issue(f"{title} {body}".lower()),
                    'created_at': issue.get('created_at'),
                    'closed_at': issue.get('closed_at')
                })
        
        return solutions
    
    def _extract_implementations(self, prs: List[Dict]) -> List[Dict[str, Any]]:
        """Extract implementation details from merged PRs"""
        implementations = []
        
        for pr in prs:
            if not pr.get('merged_at'):
                continue  # Only merged PRs
            
            title = pr.get('title', '')
            body = pr.get('body', '') if pr.get('body') else ''
            
            # Extract implementation approach
            approach = self._extract_implementation_approach(title, body)
            
            if approach:
                implementations.append({
                    'pr_number': pr.get('number'),
                    'title': title,
                    'approach': approach,
                    'url': pr.get('html_url'),
                    'category': self._categorize_pr(f"{title} {body}".lower()),
                    'author': pr.get('user', {}).get('login'),
                    'merged_at': pr.get('merged_at'),
                    'changes': {
                        'files': pr.get('changed_files', 0),
                        'additions': pr.get('additions', 0),
                        'deletions': pr.get('deletions', 0)
                    }
                })
        
        return implementations
    
    def _extract_solution_from_text(self, text: str) -> Optional[str]:
        """Extract solution description from text"""
        for pattern in self.solution_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                solution = match.group(0).strip()
                # Clean up the solution text
                solution = re.sub(r'\n+', ' ', solution)  # Replace newlines with spaces
                solution = re.sub(r'\s+', ' ', solution)  # Normalize whitespace
                if len(solution) > 50:  # Meaningful solution
                    return solution[:300] + '...' if len(solution) > 300 else solution
        
        return None
    
    def _extract_implementation_approach(self, title: str, body: str) -> Optional[str]:
        """Extract implementation approach from PR"""
        approach_patterns = [
            r'(?i)approach\s*:?\s*(.+?)(?:\n\n|\n$|$)',
            r'(?i)implementation\s*:?\s*(.+?)(?:\n\n|\n$|$)',
            r'(?i)changes\s*:?\s*(.+?)(?:\n\n|\n$|$)',
            r'(?i)this pr\s*(.+?)(?:\n\n|\n$|$)'
        ]
        
        for pattern in approach_patterns:
            match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
            if match:
                approach = match.group(1).strip()
                # Clean up
                approach = re.sub(r'\n+', ' ', approach)
                approach = re.sub(r'\s+', ' ', approach)
                if len(approach) > 30:
                    return approach[:250] + '...' if len(approach) > 250 else approach
        
        # Fallback to title
        if len(title) > 20:
            return title
        
        return None
    
    def _generate_issue_knowledge_items(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate knowledge items from issue analysis"""
        knowledge_items = []
        repo_info = analysis['repository']
        patterns = analysis['patterns']
        solutions = analysis['solutions']
        
        # Common issue patterns
        if patterns['categories']:
            category_summary = ', '.join([f"{cat}: {count}" for cat, count 
                                        in sorted(patterns['categories'].items(), 
                                                key=lambda x: x[1], reverse=True)[:5]])
            
            knowledge_items.append({
                'content': f"Common issue types in {repo_info['name']}: {category_summary}",
                'category': 'project-issues',
                'tags': ['github', 'issues', 'patterns', repo_info['name'].lower()],
                'importance': 6,
                'source': 'github_issue_analysis',
                'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/issues",
                'metadata': {
                    'repo_name': repo_info['name'],
                    'issue_categories': dict(patterns['categories']),
                    'analysis_period': analysis['analysis_period']
                }
            })
        
        # Technology-specific issues
        if patterns['technologies']:
            tech_issues = sorted(patterns['technologies'].items(), key=lambda x: x[1], reverse=True)[:5]
            tech_summary = ', '.join([f"{tech} ({count})" for tech, count in tech_issues])
            
            knowledge_items.append({
                'content': f"Technology-related issues in {repo_info['name']}: {tech_summary}",
                'category': 'technology-issues',
                'tags': ['github', 'technology', 'issues'] + [tech for tech, _ in tech_issues[:3]],
                'importance': 7,
                'source': 'github_tech_issues',
                'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/issues",
                'metadata': {
                    'repo_name': repo_info['name'],
                    'tech_issues': dict(patterns['technologies'])
                }
            })
        
        # Solutions knowledge
        for solution in solutions[:10]:  # Limit to top 10 solutions
            knowledge_items.append({
                'content': f"Solution for {repo_info['name']} issue #{solution['issue_number']}: {solution['solution']}",
                'category': 'solution',
                'tags': ['github', 'solution', solution['category'], repo_info['name'].lower()],
                'importance': 8,
                'source': 'github_issue_solution',
                'source_url': solution['url'],
                'metadata': {
                    'repo_name': repo_info['name'],
                    'issue_number': solution['issue_number'],
                    'issue_title': solution['title'],
                    'category': solution['category']
                }
            })
        
        # Resolution time insights
        if patterns['resolution_times']:
            avg_resolution = sum(rt['days'] for rt in patterns['resolution_times']) / len(patterns['resolution_times'])
            
            knowledge_items.append({
                'content': f"Issue resolution in {repo_info['name']}: Average {avg_resolution:.1f} days to close issues",
                'category': 'project-metrics',
                'tags': ['github', 'metrics', 'resolution-time', repo_info['name'].lower()],
                'importance': 5,
                'source': 'github_issue_metrics',
                'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/issues",
                'metadata': {
                    'repo_name': repo_info['name'],
                    'average_resolution_days': avg_resolution,
                    'total_resolved': len(patterns['resolution_times'])
                }
            })
        
        return knowledge_items
    
    def _generate_pr_knowledge_items(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate knowledge items from PR analysis"""
        knowledge_items = []
        repo_info = analysis['repository']
        patterns = analysis['patterns']
        implementations = analysis['implementations']
        
        # PR patterns
        if patterns['categories']:
            category_summary = ', '.join([f"{cat}: {count}" for cat, count 
                                        in sorted(patterns['categories'].items(), 
                                                key=lambda x: x[1], reverse=True)[:5]])
            
            knowledge_items.append({
                'content': f"Pull request patterns in {repo_info['name']}: {category_summary}",
                'category': 'development-patterns',
                'tags': ['github', 'pull-requests', 'patterns', repo_info['name'].lower()],
                'importance': 6,
                'source': 'github_pr_analysis',
                'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/pulls",
                'metadata': {
                    'repo_name': repo_info['name'],
                    'pr_categories': dict(patterns['categories']),
                    'analysis_period': analysis['analysis_period']
                }
            })
        
        # Implementation approaches
        for implementation in implementations[:8]:  # Limit to top 8
            knowledge_items.append({
                'content': f"Implementation approach in {repo_info['name']} PR #{implementation['pr_number']}: {implementation['approach']}",
                'category': 'implementation',
                'tags': ['github', 'implementation', implementation['category'], repo_info['name'].lower()],
                'importance': 7,
                'source': 'github_pr_implementation',
                'source_url': implementation['url'],
                'metadata': {
                    'repo_name': repo_info['name'],
                    'pr_number': implementation['pr_number'],
                    'pr_title': implementation['title'],
                    'category': implementation['category'],
                    'author': implementation['author']
                }
            })
        
        # Contributor patterns
        if patterns['author_contributions']:
            top_contributors = sorted(patterns['author_contributions'].items(), 
                                    key=lambda x: x[1], reverse=True)[:5]
            contrib_summary = ', '.join([f"{author} ({count})" for author, count in top_contributors])
            
            knowledge_items.append({
                'content': f"Top contributors to {repo_info['name']}: {contrib_summary}",
                'category': 'project-contributors',
                'tags': ['github', 'contributors', 'development', repo_info['name'].lower()],
                'importance': 5,
                'source': 'github_contributor_analysis',
                'source_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/pulls",
                'metadata': {
                    'repo_name': repo_info['name'],
                    'contributors': dict(patterns['author_contributions'])
                }
            })
        
        return knowledge_items