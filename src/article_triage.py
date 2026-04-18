#!/usr/bin/env python3
"""
Article Triage System - Intelligent article analysis using Ollama
Automatically detects, analyzes, and classifies articles for actionability
"""

import re
import json
import time
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import sqlite3

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleDetector:
    """Detects if content is an article vs other content types"""
    
    @staticmethod
    def detect_content_type(content: str, metadata: Dict[str, Any] = None) -> str:
        """Detect if content is an article, code, note, or other"""
        
        if not content or len(content) < 50:
            return 'note'
            
        content_lower = content.lower()
        word_count = len(content.split())
        line_count = content.count('\n')
        
        # Code detection (high priority)
        code_indicators = [
            '```', 'def ', 'function ', 'class ', 'import ', 'const ', 
            'let ', 'var ', '#!/', 'package ', 'public static void'
        ]
        if any(indicator in content for indicator in code_indicators):
            if word_count < 200:  # Short code snippets
                return 'code'
            elif '```' in content and content.count('```') >= 2:
                # Mixed content with code blocks - might be article
                non_code_content = re.sub(r'```[\s\S]*?```', '', content)
                if len(non_code_content.split()) > 150:
                    return 'article'
                return 'code'
        
        # Article detection
        article_markers = [
            'published', 'author', 'minute read', 'originally posted',
            'subscribe', 'follow', 'share this', 'comments', 'views',
            'tldr', 'conclusion', 'introduction', 'summary', 'abstract',
            'table of contents', 'references', 'related articles'
        ]
        
        article_score = 0
        
        # Check for article markers
        for marker in article_markers:
            if marker in content_lower:
                article_score += 2
        
        # Check structure patterns
        has_title = bool(re.search(r'^#\s+.+|^[A-Z][^.!?]{10,50}[.!?]?\s*$', content, re.MULTILINE))
        has_sections = bool(re.search(r'^#{2,}\s+', content, re.MULTILINE)) or content.count('\n\n') > 3
        has_paragraphs = line_count > 10 and word_count / max(line_count, 1) > 5
        
        if has_title:
            article_score += 3
        if has_sections:
            article_score += 2
        if has_paragraphs:
            article_score += 1
            
        # Word count scoring
        if word_count > 500:
            article_score += 5
        elif word_count > 300:
            article_score += 3
        elif word_count > 150:
            article_score += 1
            
        # Check metadata hints
        if metadata:
            source = metadata.get('source', '').lower()
            if any(site in source for site in ['medium', 'dev.to', 'blog', 'article', 'post']):
                article_score += 5
                
        # Decision threshold
        if article_score >= 8 or (article_score >= 5 and word_count > 200):
            return 'article'
        elif word_count > 100:
            return 'note'
        else:
            return 'snippet'

class OllamaArticleAnalyzer:
    """Analyzes articles using local Ollama models"""
    
    def __init__(self, model: str = None, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = model or self._select_best_model()
        self.cache = {}
        self.cache_ttl = 3600 * 24  # 24 hours
        
    def _select_best_model(self) -> str:
        """Select the best available model for article analysis"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                # Preference order for article analysis
                preferred_models = [
                    'llama3.2:3b', 'phi3:mini', 'mistral:7b', 
                    'llama3.1:8b', 'qwen2.5:3b', 'gemma2:2b'
                ]
                
                for preferred in preferred_models:
                    if any(preferred in name for name in model_names):
                        logger.info(f"Selected Ollama model: {preferred}")
                        return preferred
                        
                # Fallback to any available model
                if model_names:
                    selected = model_names[0]
                    logger.info(f"Using fallback model: {selected}")
                    return selected
                    
        except Exception as e:
            logger.error(f"Error selecting Ollama model: {e}")
            
        # Default fallback
        return "llama3.2:3b"
    
    def _get_cache_key(self, content: str) -> str:
        """Generate cache key for content"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_item: dict) -> bool:
        """Check if cached item is still valid"""
        if not cached_item:
            return False
        timestamp = cached_item.get('timestamp', 0)
        return (time.time() - timestamp) < self.cache_ttl
    
    async def analyze_article_async(self, content: str, quick_mode: bool = False) -> Dict[str, Any]:
        """Async article analysis using Ollama"""
        if not HAS_AIOHTTP:
            return self.analyze_article(content, quick_mode)
            
        cache_key = self._get_cache_key(content)
        
        # Check cache
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.info("Returning cached article analysis")
            return self.cache[cache_key]['result']
        
        # Prepare prompt
        prompt = self._create_analysis_prompt(content, quick_mode)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,  # Lower temperature for more consistent output
                            "top_p": 0.9,
                            "num_predict": 500 if quick_mode else 1000
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        analysis = self._parse_ollama_response(result.get('response', ''))
                        
                        # Cache the result
                        self.cache[cache_key] = {
                            'result': analysis,
                            'timestamp': time.time()
                        }
                        
                        return analysis
                        
        except Exception as e:
            logger.error(f"Error in async Ollama analysis: {e}")
            return self._get_fallback_analysis(content)
    
    def analyze_article(self, content: str, quick_mode: bool = False) -> Dict[str, Any]:
        """Synchronous article analysis using Ollama"""
        if not HAS_REQUESTS:
            return self._get_fallback_analysis(content)
            
        cache_key = self._get_cache_key(content)
        
        # Check cache
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.info("Returning cached article analysis")
            return self.cache[cache_key]['result']
        
        # Prepare prompt
        prompt = self._create_analysis_prompt(content, quick_mode)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 500 if quick_mode else 1000
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = self._parse_ollama_response(result.get('response', ''))
                
                # Cache the result
                self.cache[cache_key] = {
                    'result': analysis,
                    'timestamp': time.time()
                }
                
                return analysis
                
        except Exception as e:
            logger.error(f"Error in Ollama analysis: {e}")
            
        return self._get_fallback_analysis(content)
    
    def _create_analysis_prompt(self, content: str, quick_mode: bool) -> str:
        """Create the analysis prompt for Ollama"""
        
        # Truncate content to fit context window
        max_content_length = 2000 if quick_mode else 3500
        truncated_content = content[:max_content_length]
        if len(content) > max_content_length:
            truncated_content += "\n...[truncated]"
        
        if quick_mode:
            prompt = f"""Quickly analyze this article and provide a JSON response:

ARTICLE:
{truncated_content}

Provide a JSON object with these fields:
- title: article title (string)
- summary: 1-2 sentence summary (string)
- classification: one of "implement_now", "reference", "monitor", or "archive" (string)
- actionability_score: 1-10 score (number)
- key_topics: array of 3-5 main topics (array of strings)

JSON Response:
"""
        else:
            prompt = f"""Analyze this article thoroughly and provide structured output:

ARTICLE:
{truncated_content}

Create a detailed JSON analysis with:
- title: extracted or inferred title (string)
- author: author name if found, else "unknown" (string)
- summary: 2-3 sentence summary (string)
- key_topics: list of 5-7 main topics discussed (array of strings)
- technologies: specific tools, frameworks, or technologies mentioned (array of strings)
- actionability_score: 1-10 based on how actionable the content is (number)
- relevance_score: 1-10 for AI/automation/CLI development relevance (number)
- classification: categorize as "implement_now" (immediate value), "reference" (future use), "monitor" (trending topic), or "archive" (low priority) (string)
- action_items: list of 3-5 concrete actions or implementations suggested (array of strings)
- key_insights: 2-3 important takeaways (array of strings)

Focus on practical, implementable content. Be concise but thorough.

JSON Response:
"""
        
        return prompt
    
    def _parse_ollama_response(self, response: str) -> Dict[str, Any]:
        """Parse Ollama response and extract JSON"""
        
        # Try to extract JSON from response
        try:
            # First try direct JSON parsing
            return json.loads(response)
        except:
            pass
        
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Parse structured text response as fallback
        return self._parse_text_response(response)
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Parse non-JSON text response from Ollama"""
        
        result = {
            "title": "Untitled Article",
            "author": "unknown",
            "summary": "",
            "key_topics": [],
            "technologies": [],
            "actionability_score": 5,
            "relevance_score": 5,
            "classification": "reference",
            "action_items": [],
            "key_insights": []
        }
        
        lines = response.split('\n')
        current_field = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for field markers
            for field in result.keys():
                if field.replace('_', ' ').lower() in line.lower():
                    current_field = field
                    # Try to extract value from same line
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        if field.endswith('_score'):
                            try:
                                result[field] = int(value)
                            except:
                                pass
                        elif field in ['key_topics', 'technologies', 'action_items', 'key_insights']:
                            result[field] = [v.strip() for v in value.split(',')]
                        else:
                            result[field] = value
                    break
            
            # Check for list items
            if current_field and line.startswith('-'):
                # List item
                if current_field in ['key_topics', 'technologies', 'action_items', 'key_insights']:
                    result[current_field].append(line[1:].strip())
        
        return result
    
    def _get_fallback_analysis(self, content: str) -> Dict[str, Any]:
        """Fallback analysis without Ollama"""
        
        # Basic text analysis
        words = content.split()
        word_count = len(words)
        
        # Extract potential title
        title = "Untitled Article"
        title_match = re.search(r'^#\s+(.+)|^([A-Z][^.!?]{10,50})', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1) or title_match.group(2)
        
        # Simple keyword extraction for topics
        tech_keywords = {
            'python', 'javascript', 'react', 'vue', 'angular', 'node',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'api',
            'database', 'sql', 'nosql', 'mongodb', 'postgresql',
            'machine learning', 'ai', 'deep learning', 'neural network',
            'cli', 'terminal', 'automation', 'script', 'tool'
        }
        
        found_topics = []
        content_lower = content.lower()
        for keyword in tech_keywords:
            if keyword in content_lower:
                found_topics.append(keyword)
        
        # Determine classification based on content patterns
        classification = "reference"
        if any(word in content_lower for word in ['tutorial', 'how to', 'step by step', 'guide']):
            classification = "implement_now"
        elif any(word in content_lower for word in ['announcement', 'release', 'beta', 'preview']):
            classification = "monitor"
        elif word_count < 200:
            classification = "archive"
        
        # Calculate basic scores
        actionability_score = min(10, 5 + len([w for w in ['step', 'install', 'create', 'build', 'implement'] if w in content_lower]))
        relevance_score = min(10, 5 + len(found_topics))
        
        return {
            "title": title[:100],
            "author": "unknown",
            "summary": f"Article with {word_count} words discussing {', '.join(found_topics[:3]) if found_topics else 'various topics'}",
            "key_topics": found_topics[:7],
            "technologies": found_topics[:5],
            "actionability_score": actionability_score,
            "relevance_score": relevance_score,
            "classification": classification,
            "action_items": [],
            "key_insights": [],
            "analysis_method": "fallback"
        }

class ArticleTriageService:
    """Main service for article triage operations"""
    
    def __init__(self, db_path: str = None):
        self.detector = ArticleDetector()
        self.analyzer = OllamaArticleAnalyzer()
        self.db_path = db_path or str(Path.home() / ".ai-memory" / "memories.db")
        self._init_article_tables()
        
    def _init_article_tables(self):
        """Initialize article-specific database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS article_metadata (
                    memory_id TEXT PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    publication_date INTEGER,
                    reading_time INTEGER,
                    relevance_score REAL,
                    actionability_score REAL,
                    classification TEXT,
                    key_topics TEXT,
                    technologies TEXT,
                    action_items TEXT,
                    key_insights TEXT,
                    summary TEXT,
                    analysis_timestamp INTEGER,
                    analysis_method TEXT,
                    FOREIGN KEY (memory_id) REFERENCES memories(id)
                )
            """)
            
            # Create indexes for efficient querying
            conn.execute("CREATE INDEX IF NOT EXISTS idx_article_classification ON article_metadata(classification)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_article_actionability ON article_metadata(actionability_score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_article_relevance ON article_metadata(relevance_score)")
            
            conn.commit()
    
    async def triage_content(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main triage entry point - detects and analyzes if article"""
        
        # Detect content type
        content_type = self.detector.detect_content_type(content, metadata)
        
        if content_type != 'article':
            return {
                'is_article': False,
                'content_type': content_type,
                'message': f'Content detected as {content_type}, not an article'
            }
        
        # Analyze the article
        logger.info("Content detected as article, running analysis...")
        
        # Use quick mode for real-time capture
        quick_mode = metadata and metadata.get('capture_method') == 'hotkey'
        
        if HAS_AIOHTTP:
            analysis = await self.analyzer.analyze_article_async(content, quick_mode)
        else:
            analysis = self.analyzer.analyze_article(content, quick_mode)
        
        # Calculate reading time
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)  # Assuming 200 wpm
        
        # Prepare triage result
        result = {
            'is_article': True,
            'content_type': 'article',
            'analysis': analysis,
            'metadata': {
                'word_count': word_count,
                'reading_time_minutes': reading_time,
                'analyzed_at': datetime.now().isoformat(),
                'model_used': self.analyzer.model
            },
            'recommendations': self._generate_recommendations(analysis)
        }
        
        return result
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on analysis"""
        
        classification = analysis.get('classification', 'reference')
        actionability = analysis.get('actionability_score', 5)
        relevance = analysis.get('relevance_score', 5)
        
        recommendations = {
            'priority': 'normal',
            'suggested_tags': [],
            'next_actions': []
        }
        
        # Set priority
        if classification == 'implement_now' and actionability >= 7:
            recommendations['priority'] = 'high'
            recommendations['next_actions'].append('Review action items and create implementation tasks')
        elif classification == 'monitor' and relevance >= 7:
            recommendations['priority'] = 'medium'
            recommendations['next_actions'].append('Set reminder to check for updates')
        elif classification == 'archive':
            recommendations['priority'] = 'low'
        
        # Suggest tags based on classification
        recommendations['suggested_tags'] = [
            classification,
            f"actionability-{actionability}",
            f"relevance-{relevance}"
        ]
        
        # Add technology-specific tags
        for tech in analysis.get('technologies', [])[:3]:
            recommendations['suggested_tags'].append(tech.lower())
        
        # Add topic-based recommendations
        topics = analysis.get('key_topics', [])
        if 'tutorial' in str(topics).lower() or 'guide' in str(topics).lower():
            recommendations['next_actions'].append('Follow tutorial steps')
        
        if 'security' in str(topics).lower():
            recommendations['priority'] = 'high'
            recommendations['next_actions'].append('Review security implications')
        
        return recommendations
    
    def store_article_metadata(self, memory_id: str, triage_result: Dict[str, Any]):
        """Store article metadata in database"""
        
        if not triage_result.get('is_article'):
            return
        
        analysis = triage_result.get('analysis', {})
        metadata = triage_result.get('metadata', {})
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO article_metadata (
                    memory_id, title, author, publication_date, reading_time,
                    relevance_score, actionability_score, classification,
                    key_topics, technologies, action_items, key_insights,
                    summary, analysis_timestamp, analysis_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                analysis.get('title', 'Untitled'),
                analysis.get('author', 'unknown'),
                int(time.time()),  # Publication date would need extraction
                metadata.get('reading_time_minutes', 0),
                analysis.get('relevance_score', 5),
                analysis.get('actionability_score', 5),
                analysis.get('classification', 'reference'),
                json.dumps(analysis.get('key_topics', [])),
                json.dumps(analysis.get('technologies', [])),
                json.dumps(analysis.get('action_items', [])),
                json.dumps(analysis.get('key_insights', [])),
                analysis.get('summary', ''),
                int(time.time()),
                analysis.get('analysis_method', 'ollama')
            ))
            conn.commit()
    
    def get_actionable_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get articles classified as 'implement_now' with high actionability"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    am.*,
                    m.content,
                    m.timestamp,
                    m.tags
                FROM article_metadata am
                JOIN memories m ON am.memory_id = m.id
                WHERE am.classification = 'implement_now'
                   OR am.actionability_score >= 7
                ORDER BY am.actionability_score DESC, am.analysis_timestamp DESC
                LIMIT ?
            """, (limit,))
            
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                article = dict(zip(columns, row))
                # Parse JSON fields
                for field in ['key_topics', 'technologies', 'action_items', 'key_insights']:
                    if field in article and article[field]:
                        try:
                            article[field] = json.loads(article[field])
                        except:
                            article[field] = []
                results.append(article)
            
            return results
    
    def get_article_stats(self) -> Dict[str, Any]:
        """Get statistics about triaged articles"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Total articles
            total = conn.execute("SELECT COUNT(*) FROM article_metadata").fetchone()[0]
            
            # By classification
            classifications = {}
            for row in conn.execute("""
                SELECT classification, COUNT(*) as count 
                FROM article_metadata 
                GROUP BY classification
            """):
                classifications[row[0]] = row[1]
            
            # Average scores
            avg_scores = conn.execute("""
                SELECT 
                    AVG(actionability_score) as avg_actionability,
                    AVG(relevance_score) as avg_relevance,
                    AVG(reading_time) as avg_reading_time
                FROM article_metadata
            """).fetchone()
            
            # Top technologies
            all_techs = []
            for row in conn.execute("SELECT technologies FROM article_metadata WHERE technologies IS NOT NULL"):
                try:
                    techs = json.loads(row[0])
                    all_techs.extend(techs)
                except:
                    pass
            
            tech_counts = {}
            for tech in all_techs:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1
            
            top_technologies = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_articles': total,
                'classifications': classifications,
                'average_actionability': round(avg_scores[0] or 0, 1),
                'average_relevance': round(avg_scores[1] or 0, 1),
                'average_reading_time': round(avg_scores[2] or 0, 1),
                'top_technologies': top_technologies
            }

# Singleton instance
_triage_service = None

def get_triage_service(db_path: str = None) -> ArticleTriageService:
    """Get or create the article triage service instance"""
    global _triage_service
    if _triage_service is None:
        _triage_service = ArticleTriageService(db_path)
    return _triage_service

if __name__ == "__main__":
    # Test the article triage system
    import asyncio
    
    test_content = """
    # Building a Modern CLI Tool with Python
    
    Published on Dev.to by John Developer - 5 minute read
    
    In this tutorial, we'll explore how to create a powerful command-line interface tool
    using Python's Click library and Rich for beautiful terminal output.
    
    ## Introduction
    
    Command-line tools are essential for developer productivity. They automate repetitive
    tasks, provide quick access to functionality, and integrate well with other tools.
    
    ## Getting Started
    
    First, install the required dependencies:
    
    ```bash
    pip install click rich
    ```
    
    ## Implementation
    
    Here's a basic structure for our CLI tool:
    
    ```python
    import click
    from rich.console import Console
    
    console = Console()
    
    @click.command()
    @click.option('--name', help='Your name')
    def hello(name):
        console.print(f"Hello, {name}!", style="bold blue")
    ```
    
    ## Conclusion
    
    With these tools, you can build powerful CLI applications that are both functional
    and visually appealing. The combination of Click and Rich provides everything you
    need for modern terminal applications.
    """
    
    async def test():
        service = get_triage_service()
        
        # Test content detection
        content_type = service.detector.detect_content_type(test_content)
        print(f"Content type detected: {content_type}")
        
        # Test article triage
        result = await service.triage_content(test_content, {
            'source': 'test',
            'capture_method': 'manual'
        })
        
        print("\nTriage Result:")
        print(json.dumps(result, indent=2))
    
    # Run the test
    asyncio.run(test())