#!/usr/bin/env python3
"""
Repository Analyzer for Universal AI Memory System
Analyzes repository structure, documentation, and extracts knowledge
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

from .github_client import GitHubClient

logger = logging.getLogger(__name__)

class RepositoryAnalyzer:
    """Analyzes GitHub repositories and extracts knowledge for memory system"""
    
    def __init__(self, github_client: GitHubClient):
        """
        Initialize repository analyzer
        
        Args:
            github_client: Configured GitHub API client
        """
        self.github = github_client
        
        # Documentation file patterns
        self.doc_patterns = {
            'readme': ['README.md', 'README.rst', 'README.txt', 'readme.md'],
            'changelog': ['CHANGELOG.md', 'CHANGES.md', 'HISTORY.md', 'changelog.md'],
            'contributing': ['CONTRIBUTING.md', 'contributing.md', 'CONTRIBUTE.md'],
            'license': ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING'],
            'setup': ['INSTALL.md', 'INSTALLATION.md', 'SETUP.md', 'setup.md'],
            'api_docs': ['API.md', 'api.md', 'docs/API.md', 'docs/api.md'],
            'architecture': ['ARCHITECTURE.md', 'architecture.md', 'docs/architecture.md'],
            'deployment': ['DEPLOY.md', 'DEPLOYMENT.md', 'deploy.md', 'ops/deploy.md']
        }
        
        # Technology detection patterns
        self.tech_indicators = {
            'python': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile', '.py'],
            'node': ['package.json', 'yarn.lock', 'package-lock.json', '.js', '.ts'],
            'react': ['package.json', '.jsx', '.tsx'],
            'vue': ['vue.config.js', '.vue'],
            'angular': ['angular.json', '.ts'],
            'django': ['manage.py', 'settings.py', 'wsgi.py'],
            'flask': ['app.py', 'application.py'],
            'express': ['server.js', 'app.js'],
            'docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
            'kubernetes': ['deployment.yaml', 'service.yaml', 'ingress.yaml'],
            'terraform': ['.tf', 'terraform.tfvars'],
            'database': ['schema.sql', 'migrations/', 'alembic/'],
            'ci_cd': ['.github/workflows/', '.gitlab-ci.yml', 'Jenkinsfile', '.circleci/'],
            'testing': ['tests/', 'test/', 'spec/', 'jest.config.js', 'pytest.ini'],
            'monitoring': ['prometheus.yml', 'grafana/', 'datadog.yaml'],
            'security': ['.snyk', 'security.md', 'SECURITY.md']
        }
    
    def analyze_repository(self, repo_url: str, deep_analysis: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive repository analysis
        
        Args:
            repo_url: GitHub repository URL or owner/repo
            deep_analysis: Whether to perform deep file content analysis
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Analyzing repository: {repo_url}")
        
        # Parse repository identifier
        owner, repo_name = self._parse_repo_identifier(repo_url)
        if not owner or not repo_name:
            raise ValueError(f"Invalid repository identifier: {repo_url}")
        
        analysis = {
            'repository': {
                'owner': owner,
                'name': repo_name,
                'url': f"https://github.com/{owner}/{repo_name}",
                'analyzed_at': datetime.now().isoformat()
            },
            'metadata': {},
            'technologies': [],
            'documentation': {},
            'architecture': {},
            'knowledge_items': []
        }
        
        # Get basic repository metadata
        repo_data = self.github.get_repository(owner, repo_name)
        if repo_data:
            analysis['metadata'] = self._extract_metadata(repo_data)
        
        # Analyze repository structure and technologies
        technologies = self._detect_technologies(owner, repo_name)
        analysis['technologies'] = technologies
        
        # Extract documentation
        documentation = self._extract_documentation(owner, repo_name)
        analysis['documentation'] = documentation
        
        # Analyze architecture if deep analysis enabled
        if deep_analysis:
            architecture = self._analyze_architecture(owner, repo_name, technologies)
            analysis['architecture'] = architecture
        
        # Generate knowledge items for memory system
        knowledge_items = self._generate_knowledge_items(analysis)
        analysis['knowledge_items'] = knowledge_items
        
        logger.info(f"Repository analysis complete: {len(knowledge_items)} knowledge items extracted")
        return analysis
    
    def _parse_repo_identifier(self, repo_identifier: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse repository identifier into owner and repo name"""
        try:
            if repo_identifier.startswith('https://github.com/'):
                # HTTPS URL format
                path = repo_identifier.replace('https://github.com/', '').replace('.git', '')
                owner, repo = path.split('/', 1)
                return owner, repo
            elif repo_identifier.startswith('git@github.com:'):
                # SSH URL format
                path = repo_identifier.split(':')[1].replace('.git', '')
                owner, repo = path.split('/', 1)
                return owner, repo
            elif '/' in repo_identifier and not repo_identifier.startswith('http'):
                # owner/repo format
                owner, repo = repo_identifier.split('/', 1)
                return owner, repo
            else:
                return None, None
        except Exception as e:
            logger.error(f"Error parsing repository identifier: {e}")
            return None, None
    
    def _extract_metadata(self, repo_data: Dict) -> Dict[str, Any]:
        """Extract repository metadata"""
        return {
            'name': repo_data.get('name'),
            'full_name': repo_data.get('full_name'),
            'description': repo_data.get('description'),
            'language': repo_data.get('language'),
            'size': repo_data.get('size'),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'watchers': repo_data.get('watchers_count', 0),
            'issues': repo_data.get('open_issues_count', 0),
            'created_at': repo_data.get('created_at'),
            'updated_at': repo_data.get('updated_at'),
            'pushed_at': repo_data.get('pushed_at'),
            'default_branch': repo_data.get('default_branch', 'main'),
            'topics': repo_data.get('topics', []),
            'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
            'is_fork': repo_data.get('fork', False),
            'is_archived': repo_data.get('archived', False),
            'is_private': repo_data.get('private', False),
            'homepage': repo_data.get('homepage')
        }
    
    def _detect_technologies(self, owner: str, repo_name: str) -> List[Dict[str, Any]]:
        """Detect technologies used in the repository"""
        technologies = []
        
        # Get repository contents
        contents = self.github.get_repository_contents(owner, repo_name)
        if not contents:
            return technologies
        
        # Get language statistics from GitHub
        languages = self.github.get_repository_languages(owner, repo_name) or {}
        
        # Process GitHub language detection
        for lang, bytes_count in languages.items():
            technologies.append({
                'name': lang.lower(),
                'category': 'programming_language',
                'confidence': 'github_detected',
                'bytes': bytes_count,
                'evidence': ['github_language_detection']
            })
        
        # Analyze file structure for additional technologies
        file_list = [item['name'] for item in contents if item['type'] == 'file']
        
        for tech_name, indicators in self.tech_indicators.items():
            evidence = []
            
            for indicator in indicators:
                if indicator.endswith('/'):
                    # Directory indicator
                    dir_name = indicator.rstrip('/')
                    dir_contents = self.github.get_repository_contents(owner, repo_name, dir_name)
                    if dir_contents:
                        evidence.append(f"directory:{dir_name}")
                else:
                    # File indicator
                    if indicator in file_list:
                        evidence.append(f"file:{indicator}")
                    elif any(f.endswith(indicator) for f in file_list if indicator.startswith('.')):
                        matching_files = [f for f in file_list if f.endswith(indicator)]
                        evidence.append(f"extension:{indicator} ({len(matching_files)} files)")
            
            if evidence:
                # Determine confidence based on evidence strength
                confidence = 'high' if len(evidence) >= 3 else 'medium' if len(evidence) >= 2 else 'low'
                
                technologies.append({
                    'name': tech_name,
                    'category': 'technology_stack',
                    'confidence': confidence,
                    'evidence': evidence
                })
        
        return technologies
    
    def _extract_documentation(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Extract documentation from repository"""
        documentation = {}
        
        for doc_type, file_patterns in self.doc_patterns.items():
            for pattern in file_patterns:
                content = self.github.get_file_content(owner, repo_name, pattern)
                if content:
                    parsed_content = self._parse_documentation_content(content, doc_type)
                    documentation[doc_type] = {
                        'file': pattern,
                        'content': content,
                        'parsed': parsed_content,
                        'length': len(content),
                        'sections': self._extract_markdown_sections(content)
                    }
                    break  # Use first matching file
        
        return documentation
    
    def _parse_documentation_content(self, content: str, doc_type: str) -> Dict[str, Any]:
        """Parse documentation content to extract structured information"""
        parsed = {
            'summary': '',
            'installation_steps': [],
            'usage_examples': [],
            'dependencies': [],
            'api_endpoints': [],
            'configuration_options': []
        }
        
        if doc_type == 'readme':
            parsed.update(self._parse_readme_content(content))
        elif doc_type == 'api_docs':
            parsed.update(self._parse_api_documentation(content))
        elif doc_type == 'setup':
            parsed.update(self._parse_setup_documentation(content))
        
        return parsed
    
    def _parse_readme_content(self, content: str) -> Dict[str, Any]:
        """Parse README content for key information"""
        parsed = {
            'summary': '',
            'installation_steps': [],
            'usage_examples': [],
            'features': []
        }
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Detect sections
            if line.startswith('#'):
                section_title = line.lstrip('#').strip().lower()
                if any(keyword in section_title for keyword in ['install', 'setup', 'getting started']):
                    current_section = 'installation'
                elif any(keyword in section_title for keyword in ['usage', 'example', 'quick start']):
                    current_section = 'usage'
                elif any(keyword in section_title for keyword in ['feature', 'capability']):
                    current_section = 'features'
                else:
                    current_section = None
            
            # Extract installation steps
            elif current_section == 'installation':
                if line.startswith('```') or line.startswith('    '):
                    # Code block - likely installation command
                    code = line.strip('```').strip()
                    if code and not code.startswith('#'):
                        parsed['installation_steps'].append(code)
                elif re.match(r'^[0-9]+\\.', line):
                    # Numbered list item
                    parsed['installation_steps'].append(line)
            
            # Extract usage examples
            elif current_section == 'usage':
                if line.startswith('```') or line.startswith('    '):
                    code = line.strip('```').strip()
                    if code:
                        parsed['usage_examples'].append(code)
            
            # Extract features
            elif current_section == 'features':
                if line.startswith('-') or line.startswith('*'):
                    feature = line.lstrip('-*').strip()
                    if feature:
                        parsed['features'].append(feature)
        
        # Extract summary from first paragraph
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            clean_paragraph = re.sub(r'#+\s*', '', paragraph).strip()
            if clean_paragraph and not clean_paragraph.startswith('[') and len(clean_paragraph) > 50:
                parsed['summary'] = clean_paragraph[:300] + '...' if len(clean_paragraph) > 300 else clean_paragraph
                break
        
        return parsed
    
    def _parse_api_documentation(self, content: str) -> Dict[str, Any]:
        """Parse API documentation for endpoints and usage"""
        parsed = {
            'api_endpoints': [],
            'authentication': '',
            'examples': []
        }
        
        # Extract API endpoints
        endpoint_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)'
        for match in re.finditer(endpoint_pattern, content):
            method, endpoint = match.groups()
            parsed['api_endpoints'].append(f"{method} {endpoint}")
        
        # Look for authentication section
        auth_match = re.search(r'(?i)authentication.*?(?=\n##|\n#|$)', content, re.DOTALL)
        if auth_match:
            parsed['authentication'] = auth_match.group(0).strip()
        
        return parsed
    
    def _parse_setup_documentation(self, content: str) -> Dict[str, Any]:
        """Parse setup/installation documentation"""
        parsed = {
            'requirements': [],
            'installation_steps': [],
            'configuration': []
        }
        
        # Extract requirements
        req_section = re.search(r'(?i)(requirements?|prerequisites?).*?(?=\n##|\n#|$)', content, re.DOTALL)
        if req_section:
            lines = req_section.group(0).split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    req = line.lstrip('-*').strip()
                    if req:
                        parsed['requirements'].append(req)
        
        return parsed
    
    def _extract_markdown_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract sections from markdown content"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content),
                        'length': len('\n'.join(current_content))
                    })
                
                # Start new section
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content),
                'length': len('\n'.join(current_content))
            })
        
        return sections
    
    def _analyze_architecture(self, owner: str, repo_name: str, technologies: List[Dict]) -> Dict[str, Any]:
        """Analyze repository architecture and structure"""
        architecture = {
            'project_structure': {},
            'patterns': [],
            'frameworks': [],
            'deployment_info': {}
        }
        
        # Analyze project structure
        contents = self.github.get_repository_contents(owner, repo_name)
        if contents:
            structure = self._analyze_project_structure(contents)
            architecture['project_structure'] = structure
        
        # Identify architectural patterns
        patterns = self._identify_patterns(technologies, contents or [])
        architecture['patterns'] = patterns
        
        # Extract deployment information
        deployment_info = self._extract_deployment_info(owner, repo_name)
        architecture['deployment_info'] = deployment_info
        
        return architecture
    
    def _analyze_project_structure(self, contents: List[Dict]) -> Dict[str, Any]:
        """Analyze project directory structure"""
        structure = {
            'directories': [],
            'key_files': [],
            'structure_type': 'unknown'
        }
        
        dirs = [item['name'] for item in contents if item['type'] == 'dir']
        files = [item['name'] for item in contents if item['type'] == 'file']
        
        structure['directories'] = dirs
        structure['key_files'] = files
        
        # Identify project structure patterns
        if 'src' in dirs and 'tests' in dirs:
            structure['structure_type'] = 'standard_src_tests'
        elif 'app' in dirs or 'src' in dirs:
            structure['structure_type'] = 'source_based'
        elif 'lib' in dirs and 'bin' in dirs:
            structure['structure_type'] = 'traditional_unix'
        elif any(d in dirs for d in ['components', 'pages', 'public']):
            structure['structure_type'] = 'web_application'
        elif 'models' in dirs and 'views' in dirs:
            structure['structure_type'] = 'mvc_pattern'
        
        return structure
    
    def _identify_patterns(self, technologies: List[Dict], contents: List[Dict]) -> List[str]:
        """Identify architectural patterns from technologies and structure"""
        patterns = []
        
        tech_names = [t['name'] for t in technologies]
        dir_names = [item['name'] for item in contents if item['type'] == 'dir']
        
        # Web framework patterns
        if 'react' in tech_names:
            patterns.append('React SPA')
        if 'django' in tech_names:
            patterns.append('Django MVC')
        if 'flask' in tech_names:
            patterns.append('Flask Microservice')
        
        # Architecture patterns
        if 'docker' in tech_names:
            patterns.append('Containerized Application')
        if 'kubernetes' in tech_names:
            patterns.append('Microservices Architecture')
        if 'api' in dir_names or any('api' in t['name'] for t in technologies):
            patterns.append('REST API')
        
        # Database patterns
        if any(db in tech_names for db in ['postgresql', 'mysql', 'mongodb']):
            patterns.append('Database-backed Application')
        
        return patterns
    
    def _extract_deployment_info(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Extract deployment and infrastructure information"""
        deployment = {
            'dockerfile': None,
            'docker_compose': None,
            'ci_cd': [],
            'cloud_config': []
        }
        
        # Check for Docker files
        dockerfile_content = self.github.get_file_content(owner, repo_name, 'Dockerfile')
        if dockerfile_content:
            deployment['dockerfile'] = self._parse_dockerfile(dockerfile_content)
        
        compose_content = self.github.get_file_content(owner, repo_name, 'docker-compose.yml')
        if compose_content:
            deployment['docker_compose'] = compose_content[:500] + '...' if len(compose_content) > 500 else compose_content
        
        # Check for CI/CD configurations
        ci_files = ['.github/workflows/ci.yml', '.gitlab-ci.yml', 'Jenkinsfile', '.circleci/config.yml']
        for ci_file in ci_files:
            ci_content = self.github.get_file_content(owner, repo_name, ci_file)
            if ci_content:
                deployment['ci_cd'].append({
                    'file': ci_file,
                    'type': self._identify_ci_type(ci_file),
                    'content_preview': ci_content[:300] + '...' if len(ci_content) > 300 else ci_content
                })
        
        return deployment
    
    def _parse_dockerfile(self, dockerfile_content: str) -> Dict[str, Any]:
        """Parse Dockerfile for deployment information"""
        info = {
            'base_image': '',
            'exposed_ports': [],
            'commands': [],
            'env_vars': []
        }
        
        lines = dockerfile_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('FROM'):
                info['base_image'] = line.split()[1] if len(line.split()) > 1 else ''
            elif line.startswith('EXPOSE'):
                ports = line.split()[1:] if len(line.split()) > 1 else []
                info['exposed_ports'].extend(ports)
            elif line.startswith('RUN'):
                info['commands'].append(line[4:].strip())
            elif line.startswith('ENV'):
                info['env_vars'].append(line[4:].strip())
        
        return info
    
    def _identify_ci_type(self, filename: str) -> str:
        """Identify CI/CD system type from filename"""
        if 'github' in filename:
            return 'GitHub Actions'
        elif 'gitlab' in filename:
            return 'GitLab CI'
        elif 'jenkins' in filename.lower():
            return 'Jenkins'
        elif 'circleci' in filename:
            return 'CircleCI'
        else:
            return 'Unknown'
    
    def _generate_knowledge_items(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate knowledge items for the memory system"""
        knowledge_items = []
        repo_info = analysis['repository']
        metadata = analysis['metadata']
        
        # Repository overview knowledge item
        if metadata.get('description'):
            knowledge_items.append({
                'content': f"Repository: {repo_info['name']} - {metadata['description']}",
                'category': 'project-info',
                'tags': ['github', 'repository', 'project-overview'] + (metadata.get('topics', [])[:5]),
                'importance': 8,
                'source': 'github_repository',
                'source_url': repo_info['url'],
                'metadata': {
                    'repo_owner': repo_info['owner'],
                    'repo_name': repo_info['name'],
                    'stars': metadata.get('stars', 0),
                    'language': metadata.get('language'),
                    'last_updated': metadata.get('updated_at')
                }
            })
        
        # Technology stack knowledge
        if analysis['technologies']:
            tech_list = [t['name'] for t in analysis['technologies'] if t['confidence'] in ['high', 'github_detected']]
            if tech_list:
                knowledge_items.append({
                    'content': f"Technology Stack for {repo_info['name']}: {', '.join(tech_list)}",
                    'category': 'technology',
                    'tags': ['github', 'technology', 'stack'] + tech_list[:7],
                    'importance': 7,
                    'source': 'github_analysis',
                    'source_url': repo_info['url'],
                    'metadata': {
                        'repo_name': repo_info['name'],
                        'technologies': analysis['technologies']
                    }
                })
        
        # Documentation knowledge items
        for doc_type, doc_info in analysis['documentation'].items():
            if doc_info['parsed'].get('summary'):
                knowledge_items.append({
                    'content': f"{repo_info['name']} {doc_type}: {doc_info['parsed']['summary']}",
                    'category': 'documentation',
                    'tags': ['github', 'documentation', doc_type, repo_info['name'].lower()],
                    'importance': 6,
                    'source': f"github_{doc_type}",
                    'source_url': f"{repo_info['url']}/blob/main/{doc_info['file']}",
                    'metadata': {
                        'repo_name': repo_info['name'],
                        'doc_type': doc_type,
                        'file': doc_info['file']
                    }
                })
            
            # Installation steps as separate knowledge items
            if doc_info['parsed'].get('installation_steps'):
                steps = doc_info['parsed']['installation_steps'][:5]  # Limit to first 5 steps
                knowledge_items.append({
                    'content': f"Installation for {repo_info['name']}: {' → '.join(steps)}",
                    'category': 'setup',
                    'tags': ['github', 'installation', 'setup', repo_info['name'].lower()],
                    'importance': 8,
                    'source': 'github_installation',
                    'source_url': f"{repo_info['url']}/blob/main/{doc_info['file']}",
                    'metadata': {
                        'repo_name': repo_info['name'],
                        'steps': steps
                    }
                })
        
        # Architecture patterns knowledge
        if analysis['architecture'].get('patterns'):
            patterns = analysis['architecture']['patterns']
            knowledge_items.append({
                'content': f"Architecture patterns in {repo_info['name']}: {', '.join(patterns)}",
                'category': 'architecture',
                'tags': ['github', 'architecture', 'patterns'] + [p.lower().replace(' ', '-') for p in patterns],
                'importance': 7,
                'source': 'github_architecture',
                'source_url': repo_info['url'],
                'metadata': {
                    'repo_name': repo_info['name'],
                    'patterns': patterns,
                    'structure_type': analysis['architecture']['project_structure'].get('structure_type')
                }
            })
        
        # Deployment knowledge
        deployment_info = analysis['architecture'].get('deployment_info', {})
        if deployment_info.get('dockerfile'):
            dockerfile_info = deployment_info['dockerfile']
            knowledge_items.append({
                'content': f"Docker setup for {repo_info['name']}: Base image {dockerfile_info.get('base_image', 'unknown')}, Ports: {', '.join(dockerfile_info.get('exposed_ports', []))}",
                'category': 'deployment',
                'tags': ['github', 'docker', 'deployment', repo_info['name'].lower()],
                'importance': 7,
                'source': 'github_dockerfile',
                'source_url': f"{repo_info['url']}/blob/main/Dockerfile",
                'metadata': {
                    'repo_name': repo_info['name'],
                    'dockerfile_info': dockerfile_info
                }
            })
        
        return knowledge_items