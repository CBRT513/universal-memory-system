#!/usr/bin/env python3
"""
Article Capture Service - Milestone A
Handles URL fetching, content extraction, and summarization
"""

import asyncio
import hashlib
import json
import logging
import random
import sqlite3
import time
import uuid
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from readability import Document

# Import site adapters - check if module is available
try:
    from site_adapters import adapter_registry
except ImportError:
    try:
        from src.site_adapters import adapter_registry
    except ImportError:
        adapter_registry = None
        logger = logging.getLogger(__name__)
        logger.warning("Site adapters not available")

logger = logging.getLogger(__name__)

class CaptureService:
    """Service for capturing and processing articles"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "memories.db"
        self.db_path = str(db_path)
        self.job_queue = asyncio.Queue()
        self.job_states = {}  # job_id -> state info for SSE
        self.headers_config = self._load_headers_config()
        
    def _load_headers_config(self) -> Dict:
        """Load headers configuration from YAML file"""
        config_path = Path(__file__).parent.parent / "config" / "capture_headers.yml"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load headers config: {e}")
        
        # Fallback config if file not found
        return {
            "user_agents": {
                "desktop": [
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                ]
            },
            "headers": {
                "default": {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9"
                }
            },
            "timeouts": {"connect": 8.0, "read": 8.0, "total": 30.0},
            "retry": {"max_attempts": 2, "backoff_factor": 2}
        }
    
    def generate_capture_id(self) -> str:
        """Generate unique capture ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        rand = str(uuid.uuid4())[:8]
        return f"cap_{timestamp}_{rand}"
    
    def generate_job_id(self) -> str:
        """Generate unique job ID"""
        return f"job_{uuid.uuid4().hex[:12]}"
    
    def compute_dedup_hash(self, url: str) -> str:
        """Compute deduplication hash for URL"""
        # Normalize URL for dedup
        parsed = urlparse(url.lower().strip())
        normalized = f"{parsed.netloc}{parsed.path}"
        return hashlib.sha1(normalized.encode()).hexdigest()
    
    async def check_duplicate(self, url: str) -> Optional[Dict]:
        """Check if URL was captured in last 24 hours"""
        if not url:
            return None
            
        dedup_hash = self.compute_dedup_hash(url)
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT c.*, cc.text, cc.summary
                FROM captures c
                LEFT JOIN capture_content cc ON c.id = cc.capture_id
                WHERE c.dedup_hash = ? AND c.created_at > ?
                ORDER BY c.created_at DESC
                LIMIT 1
            """, (dedup_hash, cutoff))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
        finally:
            conn.close()
            
        return None
    
    async def fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch and extract content from URL with smart headers and retry"""
        # Select random user agent
        user_agents = self.headers_config.get("user_agents", {}).get("desktop", [])
        ua = random.choice(user_agents) if user_agents else "Mozilla/5.0"
        
        # Build headers
        headers = self.headers_config.get("headers", {}).get("default", {}).copy()
        headers["User-Agent"] = ua
        
        # Check for special domain headers
        domain = urlparse(url).netloc
        special = self.headers_config.get("special_domains", {})
        if domain in special:
            headers.update(special[domain].get("headers", {}))
        
        # Get timeout config
        timeouts = self.headers_config.get("timeouts", {})
        timeout = httpx.Timeout(
            connect=timeouts.get("connect", 8.0),
            read=timeouts.get("read", 8.0),
            write=None,
            pool=None
        )
        
        # Retry config
        retry_config = self.headers_config.get("retry", {})
        max_attempts = retry_config.get("max_attempts", 2)
        backoff_factor = retry_config.get("backoff_factor", 2)
        
        last_error = None
        for attempt in range(max_attempts):
            if attempt > 0:
                # Exponential backoff
                await asyncio.sleep(backoff_factor ** (attempt - 1))
                logger.info(f"Retry attempt {attempt + 1} for {url}")
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        url, 
                        headers=headers, 
                        timeout=timeout, 
                        follow_redirects=True
                    )
                    http_status = response.status_code
                    
                    # Check if we should retry this status
                    retry_statuses = retry_config.get("retry_on_status", [])
                    if http_status in retry_statuses and attempt < max_attempts - 1:
                        last_error = f"HTTP {http_status}"
                        continue
                    
                    response.raise_for_status()
                    html = response.text
                    
                    # Try site-specific adapter first
                    adapter_result = None
                    if adapter_registry:
                        adapter_result = adapter_registry.extract(url, html)
                    if adapter_result:
                        # Adapter succeeded, merge with required fields
                        return {
                            'text': adapter_result.get('text', '')[:50000],
                            'title': adapter_result.get('title', urlparse(url).netloc),
                            'domain': urlparse(url).netloc,
                            'author': adapter_result.get('author'),
                            'url': url,
                            'http_status': http_status,
                            'extraction_method': adapter_result.get('extraction_method', 'adapter'),
                            'metadata': {k: v for k, v in adapter_result.items() 
                                       if k not in ['text', 'title', 'author', 'extraction_method']}
                        }
                    
                    # No adapter or adapter failed, use generic extraction
                    doc = Document(html)
                    clean_html = doc.summary()
                    title = doc.short_title()
                    
                    if clean_html and len(clean_html) > 100:
                        soup = BeautifulSoup(clean_html, 'html.parser')
                        text = soup.get_text(strip=True, separator='\n')
                    else:
                        # Fallback to BeautifulSoup
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        text = soup.get_text(strip=True, separator='\n')
                        title = soup.find('title')
                        title = title.string if title else urlparse(url).netloc
                    
                    # Extract domain
                    domain = urlparse(url).netloc
                    
                    # Try to find author
                    author = None
                    author_meta = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'article:author'})
                    if author_meta:
                        author = author_meta.get('content')
                    
                    return {
                        'text': text[:50000],  # Limit to ~50k chars
                        'title': title,
                        'domain': domain,
                        'author': author,
                        'url': url,
                        'http_status': http_status,
                        'extraction_method': 'readability_fallback'
                    }
                    
                except httpx.HTTPStatusError as e:
                    # Capture HTTP error details
                    http_status = e.response.status_code if e.response else 0
                    last_error = f"HTTP {http_status}: {str(e)}"
                    logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                    
                    # Check if we should retry
                    retry_statuses = retry_config.get("retry_on_status", [])
                    if http_status in retry_statuses and attempt < max_attempts - 1:
                        continue
                    
                    # Don't retry, propagate error
                    logger.error(f"HTTP error fetching {url}: {http_status} - {e}")
                    raise Exception(f"HTTP {http_status}: {str(e)}")
                    
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                    
                    if attempt < max_attempts - 1:
                        continue
                    
                    logger.error(f"Error fetching {url}: {e}")
                    raise
        
        # If we get here, all retries failed
        if last_error:
            raise Exception(f"All retry attempts failed: {last_error}")
        raise Exception("Fetch failed with no error details")
    
    def summarize_text(self, text: str, max_sentences: int = 3) -> str:
        """Create simple summary - just first N sentences for MVP"""
        if not text:
            return ""
        
        # Split into sentences (simple approach)
        sentences = text.replace('\n', ' ').split('. ')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Take first N sentences
        summary = '. '.join(sentences[:max_sentences])
        if summary and not summary.endswith('.'):
            summary += '.'
            
        return summary[:500]  # Max 500 chars
    
    async def process_capture(self, job_id: str, url: Optional[str], text: Optional[str], 
                            notes: Optional[str], project: str = "vader-lab", 
                            mode: str = "server", title: Optional[str] = None):
        """Process a capture job"""
        capture_id = self.generate_capture_id()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Track timings
        start_time = time.time()
        timings = {"queued_ms": 0, "fetch_ms": 0, "normalize_ms": 0, "summarize_ms": 0, "total_ms": 0}
        http_status = 200
        cause = "ok"
        
        try:
            # Update job state
            self.job_states[job_id] = {"state": "processing", "msg": "Starting capture...", "stage": "starting"}
            
            # Initialize capture record
            created_at = datetime.now().isoformat()
            source_url = url
            source_domain = None
            source_title = None
            source_author = None
            content_text = text or ""
            dedup_hash = None
            
            # Handle content based on mode
            if mode == "client":
                # Client-provided content, skip fetch
                fetch_start = time.time()
                self.job_states[job_id] = {"state": "processing", "msg": "Processing client content...", "stage": "processing"}
                content_text = text
                source_title = title
                source_domain = urlparse(url).netloc if url else None
                source_author = None
                http_status = 200
                dedup_hash = self.compute_dedup_hash(url) if url else None
                cause = "ok"
                timings["fetch_ms"] = 0  # No fetch for client mode
            elif url:
                # Server-side fetch
                fetch_start = time.time()
                self.job_states[job_id] = {"state": "fetching", "msg": f"Fetching {url}...", "stage": "fetching"}
                try:
                    fetched = await self.fetch_url(url)
                    content_text = fetched['text']
                    source_title = fetched['title']
                    source_domain = fetched['domain']
                    source_author = fetched['author']
                    http_status = fetched.get('http_status', 200)
                    dedup_hash = self.compute_dedup_hash(url)
                    timings["fetch_ms"] = int((time.time() - fetch_start) * 1000)
                except Exception as e:
                    timings["fetch_ms"] = int((time.time() - fetch_start) * 1000)
                    # Determine cause from error
                    error_str = str(e)
                    if "HTTP 403" in error_str or "HTTP 401" in error_str or "HTTP 429" in error_str:
                        cause = "blocked"
                        http_status = 403
                    elif "HTTP 404" in error_str:
                        cause = "not_found"
                        http_status = 404
                    elif "HTTP 5" in error_str:
                        cause = "server_error"
                        http_status = 500
                    else:
                        cause = "invalid"
                    
                    # If fetch fails, continue with provided text if any
                    logger.error(f"Fetch failed: {e}")
                    if not text:
                        raise
            
            # Normalize content
            normalize_start = time.time()
            self.job_states[job_id] = {"state": "normalizing", "msg": "Processing content...", "stage": "normalizing"}
            timings["normalize_ms"] = int((time.time() - normalize_start) * 1000)
            
            # Summarize
            summarize_start = time.time()
            self.job_states[job_id] = {"state": "summarizing", "msg": "Creating summary...", "stage": "summarizing"}
            summary = self.summarize_text(content_text)
            timings["summarize_ms"] = int((time.time() - summarize_start) * 1000)
            
            # Persist
            self.job_states[job_id] = {"state": "persisting", "msg": "Saving to database..."}
            
            # Insert capture record
            cursor.execute("""
                INSERT INTO captures (
                    id, created_at, project, source_url, source_domain,
                    source_title, source_author, notes, status, dedup_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                capture_id, created_at, project, source_url, source_domain,
                source_title, source_author, notes, 'done', dedup_hash
            ))
            
            # Insert content
            cursor.execute("""
                INSERT INTO capture_content (
                    capture_id, text, summary, length_tokens
                ) VALUES (?, ?, ?, ?)
            """, (
                capture_id, content_text, summary, len(content_text.split())
            ))
            
            # Update job status
            cursor.execute("""
                UPDATE capture_status 
                SET capture_id = ?, state = 'done', last_update = ?
                WHERE job_id = ?
            """, (capture_id, datetime.now().isoformat(), job_id))
            
            conn.commit()
            
            # Extract entities after successful capture
            try:
                from entity_extraction import extract_entities
                from graph_operations import GraphOperations
                
                # Create document node for this capture using the same database
                graph_ops = GraphOperations(db_path=self.db_path)
                doc_id = graph_ops.create_document_node(capture_id, project)
                
                # Extract entities from content
                extraction_result = extract_entities(
                    text=content_text,
                    doc_id=doc_id,
                    project=project
                )
                
                # Persist entities and edges
                for entity in extraction_result['entities']:
                    entity_id = graph_ops.upsert_entity(
                        project_id=project,
                        name=entity['name'],
                        etype=entity['type'],
                        belief=entity.get('confidence', 0.7)
                    )
                    
                    # Create MENTIONS edge from document to entity
                    graph_ops.upsert_edge(
                        project_id=project,
                        src_id=doc_id,
                        dst_id=entity_id,
                        etype="MENTIONS",
                        confidence=entity.get('confidence', 0.8),
                        origin="extractor",
                        extractor_version="d1"
                    )
                
                logger.info(f"Extracted {len(extraction_result['entities'])} entities from capture {capture_id}")
                
            except Exception as e:
                logger.warning(f"Failed to extract entities for capture {capture_id}: {e}")
                # Continue even if extraction fails - don't fail the whole capture
            
            # Calculate total time
            timings["total_ms"] = int((time.time() - start_time) * 1000)
            
            # Update job state with all metadata
            self.job_states[job_id] = {
                "state": "done", 
                "msg": "Capture complete!",
                "capture_id": capture_id,
                "http_status": http_status,
                "cause": cause,
                "timings": timings,
                "cached": False
            }
            
            # Record capture event for metrics
            extraction_method = None
            if mode == "client":
                extraction_method = "client_capture"
            
            self.record_capture_event(
                job_id=job_id,
                capture_id=capture_id,
                url=source_url,
                http_status=http_status,
                cause=cause,
                cached=False,
                fetch_time_ms=timings["fetch_ms"],
                total_time_ms=timings["total_ms"],
                extraction_method=extraction_method,
                project=project
            )
            
            return capture_id
            
        except Exception as e:
            logger.error(f"Error processing capture: {e}")
            
            # Update error state
            cursor.execute("""
                UPDATE capture_status 
                SET state = 'error', last_update = ?
                WHERE job_id = ?
            """, (datetime.now().isoformat(), job_id))
            
            if capture_id:
                cursor.execute("""
                    UPDATE captures 
                    SET status = 'error', error = ?
                    WHERE id = ?
                """, (str(e), capture_id))
            
            conn.commit()
            
            # Calculate total time even on error
            timings["total_ms"] = int((time.time() - start_time) * 1000)
            
            self.job_states[job_id] = {
                "state": "error",
                "msg": f"Error: {str(e)}",
                "http_status": http_status,
                "cause": cause,
                "timings": timings,
                "cached": False
            }
            
            # Record failed capture event for metrics
            self.record_capture_event(
                job_id=job_id,
                capture_id=capture_id if 'capture_id' in locals() else None,
                url=url,
                http_status=http_status,
                cause=cause,
                cached=False,
                fetch_time_ms=timings.get("fetch_ms", 0),
                total_time_ms=timings["total_ms"],
                project=project
            )
            
            raise
            
        finally:
            conn.close()
    
    async def worker(self):
        """Background worker to process capture jobs"""
        while True:
            try:
                job = await self.job_queue.get()
                await self.process_capture(**job)
            except Exception as e:
                logger.error(f"Worker error: {e}")
            
    def start_worker(self):
        """Start the background worker"""
        asyncio.create_task(self.worker())
    
    async def enqueue_capture_from_client(self, url: str, title: str, text: str,
                                         notes: Optional[str], project: str = "vader-lab") -> str:
        """
        Enqueue a capture job from client-provided content (browser extension/bookmarklet).
        Skips fetch since we have the content, but still runs dedup/summarize.
        """
        
        # Check for duplicate based on URL
        duplicate = await self.check_duplicate(url)
        if duplicate:
            # Return existing capture as cached
            job_id = self.generate_job_id()
            self.job_states[job_id] = {
                "state": "done",
                "msg": "Retrieved from cache",
                "capture_id": duplicate['id'],
                "cached": True,
                "http_status": 200,
                "cause": "ok",
                "timings": {"queued_ms": 0, "fetch_ms": 0, "normalize_ms": 0, "summarize_ms": 0, "total_ms": 5}
            }
            
            # Create a job record for consistency
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO capture_status (
                    job_id, capture_id, created_at, last_update, state
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                job_id, duplicate['id'], 
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                'done'
            ))
            conn.commit()
            conn.close()
            
            return job_id
        
        # Create new job with client-provided content
        job_id = self.generate_job_id()
        
        # Create job record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO capture_status (
                job_id, created_at, last_update, state, progress_msg
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            job_id,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            'queued',
            'Processing client capture...'
        ))
        conn.commit()
        conn.close()
        
        # Enqueue for processing with mode indicator
        await self.job_queue.put({
            'job_id': job_id,
            'url': url,
            'text': text,
            'title': title,
            'notes': notes,
            'project': project,
            'mode': 'client'  # Indicates client-provided content
        })
        
        self.job_states[job_id] = {"state": "queued", "msg": "Processing client capture..."}
        
        return job_id
    
    async def enqueue_capture(self, url: Optional[str], text: Optional[str], 
                             notes: Optional[str], project: str = "vader-lab") -> str:
        """Enqueue a capture job"""
        
        # Check for duplicate if URL provided
        if url:
            duplicate = await self.check_duplicate(url)
            if duplicate:
                # Return existing capture as cached
                job_id = self.generate_job_id()
                self.job_states[job_id] = {
                    "state": "done",
                    "msg": "Retrieved from cache",
                    "capture_id": duplicate['id'],
                    "cached": True,
                    "http_status": 200,
                    "cause": "ok",
                    "timings": {"queued_ms": 0, "fetch_ms": 0, "normalize_ms": 0, "summarize_ms": 0, "total_ms": 5}
                }
                
                # Create a job record for consistency
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO capture_status (
                        job_id, capture_id, created_at, last_update, state
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    job_id, duplicate['id'], 
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    'done'
                ))
                conn.commit()
                conn.close()
                
                return job_id
        
        # Create new job
        job_id = self.generate_job_id()
        
        # Create job record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO capture_status (
                job_id, created_at, last_update, state, progress_msg
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            job_id,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            'queued',
            'Waiting to process...'
        ))
        conn.commit()
        conn.close()
        
        # Enqueue for processing
        await self.job_queue.put({
            'job_id': job_id,
            'url': url,
            'text': text,
            'notes': notes,
            'project': project
        })
        
        self.job_states[job_id] = {"state": "queued", "msg": "Job queued..."}
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get current job status"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT cs.*, c.*, cc.summary
                FROM capture_status cs
                LEFT JOIN captures c ON cs.capture_id = c.id
                LEFT JOIN capture_content cc ON c.id = cc.capture_id
                WHERE cs.job_id = ?
            """, (job_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # Add live state if available
                if job_id in self.job_states:
                    result.update(self.job_states[job_id])
                return result
            
            return None
            
        finally:
            conn.close()
    
    def record_capture_event(self, job_id: str, capture_id: Optional[str], 
                            url: Optional[str], http_status: int, cause: str,
                            cached: bool, fetch_time_ms: int, total_time_ms: int,
                            extraction_method: Optional[str] = None,
                            user_agent: Optional[str] = None, project: str = "vader-lab"):
        """Record a capture event for metrics tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            domain = urlparse(url).netloc if url else None
            cursor.execute("""
                INSERT INTO capture_events (
                    job_id, capture_id, url, domain, http_status, cause, cached,
                    fetch_time_ms, total_time_ms, extraction_method, user_agent, project
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, capture_id, url, domain, http_status, cause, cached,
                fetch_time_ms, total_time_ms, extraction_method, user_agent, project
            ))
            conn.commit()
        except Exception as e:
            logger.warning(f"Failed to record capture event: {e}")
        finally:
            conn.close()
    
    def get_capture(self, capture_id: str) -> Dict:
        """Get capture by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT c.*, cc.text, cc.summary, cc.length_tokens
                FROM captures c
                LEFT JOIN capture_content cc ON c.id = cc.capture_id
                WHERE c.id = ?
            """, (capture_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        finally:
            conn.close()

# Singleton instance
_capture_service = None

def get_capture_service() -> CaptureService:
    """Get or create the capture service singleton"""
    global _capture_service
    if _capture_service is None:
        _capture_service = CaptureService()
    return _capture_service