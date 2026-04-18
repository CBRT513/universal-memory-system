#!/usr/bin/env python3
"""
Site-specific content adapters for improved extraction
"""

import re
from typing import Dict, Optional, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class SiteAdapter:
    """Base class for site-specific adapters"""
    
    def can_handle(self, url: str) -> bool:
        """Check if this adapter can handle the given URL"""
        raise NotImplementedError
    
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        """Extract content from HTML"""
        raise NotImplementedError


class MDNAdapter(SiteAdapter):
    """Adapter for developer.mozilla.org documentation"""
    
    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc
        return domain in ['developer.mozilla.org', 'mdn.mozillademos.org']
    
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # MDN-specific selectors
        title = None
        title_elem = soup.find('h1')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Find main content area
        content = ""
        main_content = soup.find('main') or soup.find('article')
        if main_content:
            # Remove code examples that are too verbose
            for pre in main_content.find_all('pre'):
                code_snippet = pre.get_text(strip=True)[:200]
                if len(pre.get_text()) > 200:
                    code_snippet += "..."
                pre.string = f"[CODE: {code_snippet}]"
            
            # Remove interactive examples
            for elem in main_content.find_all(class_='interactive'):
                elem.decompose()
            
            content = main_content.get_text(separator='\n', strip=True)
        
        # Extract metadata
        author = None
        last_modified = None
        
        # MDN often has contributors rather than single author
        contributors = soup.find(class_='contributors')
        if contributors:
            author = "MDN Contributors"
        
        # Look for last modified date
        modified_elem = soup.find(class_='last-modified')
        if modified_elem:
            last_modified = modified_elem.get_text(strip=True)
        
        # Extract categories/tags
        tags = []
        tag_list = soup.find(class_='tags') or soup.find(class_='tag-list')
        if tag_list:
            tags = [tag.get_text(strip=True) for tag in tag_list.find_all('a')]
        
        return {
            'title': title or urlparse(url).path.split('/')[-1],
            'text': content[:50000],
            'author': author,
            'tags': tags,
            'last_modified': last_modified,
            'extraction_method': 'mdn_adapter'
        }


class WikipediaAdapter(SiteAdapter):
    """Adapter for Wikipedia articles"""
    
    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc
        return 'wikipedia.org' in domain
    
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Wikipedia-specific selectors
        title = None
        title_elem = soup.find('h1', class_='firstHeading')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Find main content - Wikipedia stores it in mw-parser-output
        content = ""
        main_content = soup.find('div', class_='mw-parser-output')
        if main_content:
            # Remove infoboxes - they're too verbose
            for infobox in main_content.find_all(class_='infobox'):
                infobox.decompose()
            
            # Remove navigation boxes
            for navbox in main_content.find_all(class_='navbox'):
                navbox.decompose()
            
            # Remove edit links
            for edit_link in main_content.find_all(class_='mw-editsection'):
                edit_link.decompose()
            
            # Extract paragraphs and headers
            content_parts = []
            for elem in main_content.find_all(['p', 'h2', 'h3', 'h4']):
                text = elem.get_text(strip=True)
                # Skip empty paragraphs and references
                if text and not text.startswith('[') and len(text) > 20:
                    content_parts.append(text)
            
            content = '\n\n'.join(content_parts)
        
        # Extract categories
        categories = []
        cat_links = soup.find('div', id='mw-normal-catlinks')
        if cat_links:
            categories = [a.get_text(strip=True) for a in cat_links.find_all('a')][1:]  # Skip first "Categories" link
        
        # Wikipedia doesn't have single authors
        author = "Wikipedia Contributors"
        
        # Extract last modified from footer
        last_modified = None
        footer = soup.find('li', id='footer-info-lastmod')
        if footer:
            last_modified = footer.get_text(strip=True)
        
        return {
            'title': title or urlparse(url).path.split('/')[-1].replace('_', ' '),
            'text': content[:50000],
            'author': author,
            'categories': categories,
            'last_modified': last_modified,
            'extraction_method': 'wikipedia_adapter'
        }


class GitHubAdapter(SiteAdapter):
    """Adapter for GitHub repositories and pages"""
    
    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc
        return domain in ['github.com', 'raw.githubusercontent.com']
    
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'html.parser')
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        # Determine what type of GitHub page this is
        if 'raw.githubusercontent.com' in parsed_url.netloc:
            # Raw file content
            return {
                'title': path_parts[-1] if path_parts else 'Raw Content',
                'text': html[:50000],  # It's already plain text
                'author': path_parts[0] if path_parts else None,
                'extraction_method': 'github_raw'
            }
        
        # Regular GitHub page
        title = None
        content = ""
        author = None
        
        # Try to extract repo name
        if len(path_parts) >= 2:
            title = f"{path_parts[0]}/{path_parts[1]}"
            author = path_parts[0]
        
        # Check if it's a README or file view
        readme = soup.find('article', class_='markdown-body')
        if readme:
            content = readme.get_text(separator='\n', strip=True)
            # If we're viewing a specific file
            file_name = soup.find('div', class_='final-path')
            if file_name:
                title = file_name.get_text(strip=True)
        else:
            # Try to get repository description
            about = soup.find('p', class_='f4')
            if about:
                content = about.get_text(strip=True) + "\n\n"
            
            # Get file list preview
            file_list = soup.find('div', class_='js-details-container')
            if file_list:
                files = []
                for item in file_list.find_all('a', class_='Link--primary')[:20]:
                    files.append(item.get_text(strip=True))
                if files:
                    content += "Files:\n" + '\n'.join(files)
        
        # Extract stats (stars, forks, etc)
        stats = {}
        star_button = soup.find('a', href=re.compile(r'/stargazers'))
        if star_button:
            star_count = star_button.find('span')
            if star_count:
                stats['stars'] = star_count.get_text(strip=True)
        
        fork_button = soup.find('a', href=re.compile(r'/forks'))
        if fork_button:
            fork_count = fork_button.find('span')
            if fork_count:
                stats['forks'] = fork_count.get_text(strip=True)
        
        # Extract language stats
        languages = []
        lang_stats = soup.find('div', class_='BorderGrid-cell')
        if lang_stats:
            for lang in lang_stats.find_all('span', class_='ml-3'):
                languages.append(lang.get_text(strip=True))
        
        return {
            'title': title or 'GitHub Page',
            'text': content[:50000],
            'author': author,
            'stats': stats,
            'languages': languages,
            'extraction_method': 'github_adapter'
        }


class AdapterRegistry:
    """Registry for all site adapters"""
    
    def __init__(self):
        self.adapters = [
            MDNAdapter(),
            WikipediaAdapter(),
            GitHubAdapter()
        ]
    
    def get_adapter(self, url: str) -> Optional[SiteAdapter]:
        """Get the appropriate adapter for a URL"""
        for adapter in self.adapters:
            if adapter.can_handle(url):
                logger.info(f"Using {adapter.__class__.__name__} for {url}")
                return adapter
        return None
    
    def extract(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Extract content using the appropriate adapter"""
        adapter = self.get_adapter(url)
        if adapter:
            try:
                return adapter.extract(html, url)
            except Exception as e:
                logger.warning(f"Adapter extraction failed: {e}")
                return None
        return None


# Global registry instance
adapter_registry = AdapterRegistry()