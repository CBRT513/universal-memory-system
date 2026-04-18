#!/usr/bin/env python3
"""
GitHub API Client for Universal AI Memory System
Handles GitHub API interactions with rate limiting and caching
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests not available. GitHub API features disabled.")

logger = logging.getLogger(__name__)

class GitHubClient:
    """GitHub API client with intelligent rate limiting and caching"""
    
    def __init__(self, token: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize GitHub API client
        
        Args:
            token: GitHub personal access token (optional for public repos)
            cache_dir: Directory for API response caching
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        
        # Set up cache directory
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / '.memory_cache' / 'github'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self.rate_limit = {
            'remaining': 60,  # Unauthenticated limit
            'reset_time': time.time() + 3600,
            'limit': 60
        }
        
        # Session for connection pooling
        if HAS_REQUESTS:
            self.session = requests.Session()
            if self.token:
                self.session.headers.update({'Authorization': f'token {self.token}'})
                self.rate_limit['remaining'] = 5000  # Authenticated limit
                self.rate_limit['limit'] = 5000
            
            self.session.headers.update({
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Universal-AI-Memory-System/1.0'
            })
        else:
            self.session = None
            logger.warning("requests library not available - GitHub API disabled")
    
    def _get_cache_key(self, endpoint: str, params: Dict = None) -> str:
        """Generate cache key for endpoint and parameters"""
        param_str = json.dumps(params or {}, sort_keys=True)
        import hashlib
        return hashlib.md5(f"{endpoint}:{param_str}".encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str, max_age_hours: int = 1) -> Optional[Dict]:
        """Get cached response if still valid"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cached_data['cached_at'])
            if datetime.now() - cached_time < timedelta(hours=max_age_hours):
                logger.debug(f"Using cached response for {cache_key}")
                return cached_data['data']
            
        except Exception as e:
            logger.debug(f"Cache read error: {e}")
        
        return None
    
    def _cache_response(self, cache_key: str, data: Dict):
        """Cache API response"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'data': data,
                    'cached_at': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.debug(f"Cache write error: {e}")
    
    def _wait_for_rate_limit(self):
        """Wait if rate limit is exceeded"""
        if self.rate_limit['remaining'] <= 1:
            wait_time = max(0, self.rate_limit['reset_time'] - time.time())
            if wait_time > 0:
                logger.info(f"Rate limit exceeded. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
    
    def _update_rate_limit(self, response_headers: Dict):
        """Update rate limit info from response headers"""
        if 'X-RateLimit-Remaining' in response_headers:
            self.rate_limit['remaining'] = int(response_headers['X-RateLimit-Remaining'])
            self.rate_limit['reset_time'] = int(response_headers['X-RateLimit-Reset'])
            self.rate_limit['limit'] = int(response_headers['X-RateLimit-Limit'])
    
    def _make_request(self, endpoint: str, params: Dict = None, use_cache: bool = True, 
                     cache_hours: int = 1) -> Optional[Dict]:
        """Make GitHub API request with caching and rate limiting"""
        if not HAS_REQUESTS or not self.session:
            logger.error("GitHub API not available - requests library missing")
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params)
        if use_cache:
            cached = self._get_cached_response(cache_key, cache_hours)
            if cached:
                return cached
        
        # Check rate limit
        self._wait_for_rate_limit()
        
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = self.session.get(url, params=params or {})
            
            # Update rate limit info
            self._update_rate_limit(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache successful response
                if use_cache:
                    self._cache_response(cache_key, data)
                
                return data
            
            elif response.status_code == 404:
                logger.warning(f"GitHub API 404: {endpoint}")
                return None
            
            elif response.status_code == 403:
                if 'rate limit' in response.text.lower():
                    logger.warning("GitHub API rate limit exceeded")
                    # Update rate limit and retry once
                    self._update_rate_limit(response.headers)
                    self._wait_for_rate_limit()
                    return self._make_request(endpoint, params, False, cache_hours)
                else:
                    logger.error(f"GitHub API 403 Forbidden: {endpoint}")
                    return None
            
            else:
                logger.error(f"GitHub API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"GitHub API request failed: {e}")
            return None
    
    def get_repository(self, owner: str, repo: str) -> Optional[Dict]:
        """Get repository information"""
        return self._make_request(f"/repos/{owner}/{repo}")
    
    def get_repository_from_url(self, repo_url: str) -> Optional[Dict]:
        """Get repository info from GitHub URL"""
        try:
            # Parse GitHub URL to get owner/repo
            if 'github.com' not in repo_url:
                return None
            
            # Handle different URL formats
            if repo_url.startswith('git@github.com:'):
                # SSH format: git@github.com:owner/repo.git
                repo_path = repo_url.split(':')[1].replace('.git', '')
            elif 'https://github.com/' in repo_url:
                # HTTPS format: https://github.com/owner/repo
                repo_path = repo_url.replace('https://github.com/', '').replace('.git', '')
            else:
                return None
            
            owner, repo = repo_path.split('/', 1)
            return self.get_repository(owner, repo)
            
        except Exception as e:
            logger.error(f"Failed to parse repository URL {repo_url}: {e}")
            return None
    
    def get_readme(self, owner: str, repo: str, branch: str = 'main') -> Optional[str]:
        """Get repository README content"""
        # Try common README file names
        readme_files = ['README.md', 'README.rst', 'README.txt', 'README']
        
        for readme_file in readme_files:
            endpoint = f"/repos/{owner}/{repo}/contents/{readme_file}"
            content_data = self._make_request(endpoint, {'ref': branch}, cache_hours=6)
            
            if content_data:
                try:
                    import base64
                    content = base64.b64decode(content_data['content']).decode('utf-8')
                    return content
                except Exception as e:
                    logger.debug(f"Failed to decode README content: {e}")
        
        # Try with 'master' branch if 'main' failed
        if branch == 'main':
            return self.get_readme(owner, repo, 'master')
        
        return None
    
    def get_issues(self, owner: str, repo: str, state: str = 'all', 
                   since: Optional[datetime] = None, limit: int = 100) -> List[Dict]:
        """Get repository issues"""
        params = {
            'state': state,
            'per_page': min(limit, 100),
            'sort': 'updated',
            'direction': 'desc'
        }
        
        if since:
            params['since'] = since.isoformat()
        
        issues = []
        page = 1
        
        while len(issues) < limit:
            params['page'] = page
            page_data = self._make_request(f"/repos/{owner}/{repo}/issues", params, cache_hours=0.5)
            
            if not page_data:
                break
            
            issues.extend(page_data)
            
            if len(page_data) < 100:  # Last page
                break
            
            page += 1
        
        return issues[:limit]
    
    def get_pull_requests(self, owner: str, repo: str, state: str = 'all', 
                         since: Optional[datetime] = None, limit: int = 100) -> List[Dict]:
        """Get repository pull requests"""
        params = {
            'state': state,
            'per_page': min(limit, 100),
            'sort': 'updated',
            'direction': 'desc'
        }
        
        if since:
            params['since'] = since.isoformat()
        
        prs = []
        page = 1
        
        while len(prs) < limit:
            params['page'] = page
            page_data = self._make_request(f"/repos/{owner}/{repo}/pulls", params, cache_hours=0.5)
            
            if not page_data:
                break
            
            prs.extend(page_data)
            
            if len(page_data) < 100:  # Last page
                break
            
            page += 1
        
        return prs[:limit]
    
    def get_commits(self, owner: str, repo: str, since: Optional[datetime] = None, 
                    until: Optional[datetime] = None, limit: int = 100) -> List[Dict]:
        """Get repository commits"""
        params = {
            'per_page': min(limit, 100)
        }
        
        if since:
            params['since'] = since.isoformat()
        if until:
            params['until'] = until.isoformat()
        
        commits = []
        page = 1
        
        while len(commits) < limit:
            params['page'] = page
            page_data = self._make_request(f"/repos/{owner}/{repo}/commits", params, cache_hours=6)
            
            if not page_data:
                break
            
            commits.extend(page_data)
            
            if len(page_data) < 100:  # Last page
                break
            
            page += 1
        
        return commits[:limit]
    
    def get_repository_contents(self, owner: str, repo: str, path: str = '', 
                               branch: str = 'main') -> Optional[List[Dict]]:
        """Get repository contents at path"""
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {'ref': branch}
        
        contents = self._make_request(endpoint, params, cache_hours=12)
        
        # Try master branch if main fails
        if not contents and branch == 'main':
            return self.get_repository_contents(owner, repo, path, 'master')
        
        return contents
    
    def get_file_content(self, owner: str, repo: str, file_path: str, 
                        branch: str = 'main') -> Optional[str]:
        """Get content of a specific file"""
        endpoint = f"/repos/{owner}/{repo}/contents/{file_path}"
        params = {'ref': branch}
        
        file_data = self._make_request(endpoint, params, cache_hours=6)
        
        if file_data and file_data.get('content'):
            try:
                import base64
                content = base64.b64decode(file_data['content']).decode('utf-8')
                return content
            except Exception as e:
                logger.debug(f"Failed to decode file content: {e}")
        
        # Try master branch if main fails
        if branch == 'main':
            return self.get_file_content(owner, repo, file_path, 'master')
        
        return None
    
    def get_repository_languages(self, owner: str, repo: str) -> Optional[Dict]:
        """Get programming languages used in repository"""
        return self._make_request(f"/repos/{owner}/{repo}/languages", cache_hours=24)
    
    def get_repository_topics(self, owner: str, repo: str) -> Optional[List[str]]:
        """Get repository topics/tags"""
        repo_data = self._make_request(f"/repos/{owner}/{repo}", cache_hours=12)
        return repo_data.get('topics', []) if repo_data else None
    
    def search_repositories(self, query: str, limit: int = 50) -> List[Dict]:
        """Search for repositories"""
        params = {
            'q': query,
            'per_page': min(limit, 100),
            'sort': 'updated'
        }
        
        search_data = self._make_request("/search/repositories", params, cache_hours=1)
        
        if search_data and 'items' in search_data:
            return search_data['items'][:limit]
        
        return []
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status"""
        return {
            'remaining': self.rate_limit['remaining'],
            'limit': self.rate_limit['limit'],
            'reset_time': datetime.fromtimestamp(self.rate_limit['reset_time']),
            'authenticated': bool(self.token)
        }
    
    def clear_cache(self, older_than_hours: int = 24):
        """Clear cached responses older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cleared = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                cached_time = datetime.fromisoformat(cached_data['cached_at'])
                if cached_time < cutoff_time:
                    cache_file.unlink()
                    cleared += 1
                    
            except Exception as e:
                logger.debug(f"Error clearing cache file {cache_file}: {e}")
        
        if cleared > 0:
            logger.info(f"Cleared {cleared} cached GitHub API responses")
    
    def is_available(self) -> bool:
        """Check if GitHub API client is available and functional"""
        if not HAS_REQUESTS or not self.session:
            return False
        
        try:
            # Test with a simple API call
            response = self._make_request("/rate_limit", use_cache=False)
            return response is not None
        except:
            return False