
# Workspace configuration - automatically detect personal vs work
import sys
from pathlib import Path
sys.path.insert(0, '/usr/local/share/universal-memory-system')
try:
    from workspace_config import config
    # This automatically sets up the right database and port
    import os
    os.environ['MEMORY_API_PORT'] = str(config.api_port)
    os.environ['MEMORY_DB_PATH'] = config.database_path
except ImportError:
    pass  # Fallback to defaults if workspace config not available

import sys
sys.path.insert(0, "/usr/local/share/universal-memory-system")
from shared_config import *

#!/usr/bin/env python3
"""
Universal AI Memory System - REST API Service
Production-ready FastAPI service for memory operations
"""
import os
import sys
import json
import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException, Request, Depends
    from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("Error: FastAPI not available. Run setup.py first.")
    sys.exit(1)

from memory_service import get_memory_service, UniversalMemoryService
from article_triage import get_triage_service, ArticleTriageService
from capture_api import capture_router
from graph_api import graph_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Universal AI Memory API",
    description="REST API for the Universal AI Memory System - Never lose context again!",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Allow all origins for browser extension
    ],    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include capture router
app.include_router(capture_router)
app.include_router(graph_router)

# Galactica 2.0 Phase 1 — native MCP endpoint + OAuth 2.1 authorization server.
# Added via routers so the existing API surface is untouched.
from galactica_mcp.oauth_router import router as _galactica_oauth_router
from galactica_mcp.mcp_router import router as _galactica_mcp_router
from galactica_mcp import audit as _galactica_audit, oauth_storage as _galactica_oauth_storage
app.include_router(_galactica_oauth_router)
app.include_router(_galactica_mcp_router)


@app.on_event("startup")
async def _galactica_phase1_startup() -> None:
    """Initialize Phase 1 databases (audit + OAuth). Idempotent."""
    _galactica_audit.init_db()
    _galactica_oauth_storage.init_db()

# Global memory service
memory_service: Optional[UniversalMemoryService] = None

# Pydantic models for API
class MemoryStore(BaseModel):
    content: str = Field(..., description="Memory content to store")
    project: Optional[str] = Field(None, description="Project name (auto-detected if not provided)")
    category: Optional[str] = Field(None, description="Memory category")
    tags: Optional[List[str]] = Field(None, description="List of tags")
    importance: Optional[int] = Field(5, ge=1, le=10, description="Importance level 1-10")
    status: Optional[str] = Field("active", description="Memory status")
    protection_level: Optional[str] = Field("normal", description="Protection level")
    source: Optional[str] = Field(None, description="Source of the memory")
    source_url: Optional[str] = Field(None, description="Original URL")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class MemorySearch(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    project: Optional[str] = Field(None, description="Filter by project")
    category: Optional[str] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    min_importance: Optional[int] = Field(None, ge=1, le=10, description="Minimum importance")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum results")
    include_semantic: Optional[bool] = Field(True, description="Include semantic search")

class ContextRequest(BaseModel):
    relevant_to: Optional[str] = Field(None, description="Generate context relevant to this")
    project: Optional[str] = Field(None, description="Project context")
    max_tokens: Optional[int] = Field(4000, ge=100, le=10000, description="Maximum context tokens")
    include_cross_project: Optional[bool] = Field(True, description="Include cross-project insights")
    protection_aware: Optional[bool] = Field(True, description="Highlight protected systems")

class RelateRequest(BaseModel):
    content: str = Field(..., description="Content to find related memories for")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Maximum related memories")
    cross_project: Optional[bool] = Field(True, description="Search across projects")

@app.on_event("startup")
async def startup_event():
    """Initialize memory service on startup"""
    global memory_service
    
    try:
        memory_service = get_memory_service()
        logger.info("✅ Memory service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize memory service: {e}")
        raise

async def get_memory_service_instance() -> UniversalMemoryService:
    """Dependency to get memory service instance"""
    if memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    return memory_service

# Health check endpoint
@app.get("/api/health", response_model=Dict[str, Any])
async def health_check(service: UniversalMemoryService = Depends(get_memory_service_instance)):
    """Get system health status"""
    try:
        health = service.health_check()
        stats = service.get_statistics()
        
        return {
            "status": health["status"],
            "timestamp": datetime.now().isoformat(),
            "health": health,
            "total_memories": stats["overall"]["total_memories"],
            "total_projects": stats["overall"]["total_projects"],
            "embedding_provider": stats["overall"].get("embedding_provider"),
            "vector_search_enabled": stats["overall"].get("vector_search_enabled", False),
            "storage_path": stats["overall"].get("storage_path")
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the Action Plans Dashboard"""
    dashboard_file = Path(__file__).parent.parent / "master_dashboard.html"
    
    if dashboard_file.exists():
        with open(dashboard_file, 'r') as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        # Return a simple dashboard if the file doesn't exist
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Memory System Dashboard</title>
            <style>
                body { font-family: system-ui; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; }
                h1 { color: #333; }
                .info { background: #f0f0f0; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .links { display: flex; gap: 20px; margin-top: 30px; }
                .link { background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; }
                .link:hover { background: #5568d3; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧠 Universal AI Memory System</h1>
                <div class="info">
                    <h2>API is running on port 8091</h2>
                    <p>The memory system is active and ready to capture your knowledge.</p>
                </div>
                <div class="links">
                    <a href="/docs" class="link">📚 API Documentation</a>
                    <a href="/api/health" class="link">🏥 Health Status</a>
                    <a href="/api/article/stats" class="link">📊 Article Statistics</a>
                </div>
            </div>
        </body>
        </html>
        """)

# Memory operations
@app.post("/api/memory/store", response_model=Dict[str, Any])
async def store_memory(
    memory: MemoryStore,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Store a new memory with automatic article detection and triage"""
    try:
        # Check if content might be an article and auto-triage is enabled
        auto_triage = memory.metadata and memory.metadata.get('auto_triage', True)
        
        if auto_triage and len(memory.content) > 300:  # Only check longer content
            triage_service = get_triage_service(service.db_path)
            detector = triage_service.detector
            
            # Quick content type detection
            content_type = detector.detect_content_type(memory.content, memory.metadata)
            
            if content_type == 'article':
                # Run full article triage
                logger.info("Article detected, running intelligent triage...")
                
                triage_result = await triage_service.triage_content(
                    content=memory.content,
                    metadata={
                        'source': memory.source,
                        'source_url': memory.source_url,
                        'capture_method': memory.metadata.get('capture_method', 'api'),
                        **memory.metadata
                    }
                )
                
                if triage_result.get('is_article'):
                    analysis = triage_result['analysis']
                    recommendations = triage_result['recommendations']
                    
                    # Enhance tags with article metadata
                    enhanced_tags = list(set(
                        (memory.tags or []) +
                        recommendations.get('suggested_tags', []) +
                        ['article', analysis.get('classification', 'reference')]
                    ))
                    
                    # Use article importance scoring
                    article_importance = max(
                        analysis.get('actionability_score', 5),
                        analysis.get('relevance_score', 5),
                        memory.importance or 5
                    )
                    
                    # Store with enhanced metadata
                    result = service.store_memory(
                        content=memory.content,
                        project=memory.project or _detect_project(analysis),
                        category='article',
                        tags=enhanced_tags,
                        importance=article_importance,
                        status=memory.status,
                        protection_level=memory.protection_level,
                        source=memory.source or 'article_auto_triage',
                        source_url=memory.source_url,
                        metadata={
                            **memory.metadata,
                            'article_analysis': analysis,
                            'triage_metadata': triage_result['metadata'],
                            'recommendations': recommendations,
                            'auto_triaged': True
                        }
                    )
                    
                    # Store article-specific metadata
                    triage_service.store_article_metadata(result['id'], triage_result)
                    
                    logger.info(f"Article auto-triaged and stored: {result['id']} - {analysis.get('title', 'Untitled')}")
                    
                    # Add triage info to response
                    result['article_triage'] = {
                        'title': analysis.get('title'),
                        'classification': analysis.get('classification'),
                        'summary': analysis.get('summary'),
                        'priority': recommendations.get('priority')
                    }
                    
                    return result
        
        # Standard memory storage (not an article or triage disabled)
        result = service.store_memory(
            content=memory.content,
            project=memory.project,
            category=memory.category,
            tags=memory.tags,
            importance=memory.importance,
            status=memory.status,
            protection_level=memory.protection_level,
            source=memory.source,
            source_url=memory.source_url,
            metadata=memory.metadata
        )
        
        logger.info(f"Stored memory: {result['id']} ({result['status']})")
        return result
        
    except Exception as e:
        logger.error(f"Memory storage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _detect_project(analysis: dict) -> Optional[str]:
    """Auto-detect project from article analysis"""
    # Simple project detection based on technologies
    techs = analysis.get('technologies', [])
    topics = analysis.get('key_topics', [])
    
    all_keywords = [t.lower() for t in techs + topics]
    
    # Project mapping (customize based on your projects)
    project_keywords = {
        'universal-memory': ['memory', 'capture', 'knowledge', 'ai memory'],
        'agentforge': ['agent', 'llm', 'ollama', 'automation'],
        'cli-tools': ['cli', 'terminal', 'command line', 'bash'],
        'web-dev': ['react', 'vue', 'javascript', 'frontend', 'css'],
        'backend': ['api', 'fastapi', 'django', 'database', 'sql'],
        'ai-ml': ['machine learning', 'neural', 'model', 'training']
    }
    
    for project, keywords in project_keywords.items():
        if any(kw in all_keywords for kw in keywords):
            return project
    
    return None

@app.get("/api/memory/search", response_model=Dict[str, Any])
@app.post("/api/memory/search", response_model=Dict[str, Any])
async def search_memories(
    request: Request,
    search_params: Optional[MemorySearch] = None,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Search memories"""
    try:
        # Handle both GET and POST requests
        if request.method == "GET":
            # Extract query parameters for GET request
            query_params = dict(request.query_params)
            query = query_params.get("q")
            project = query_params.get("project")
            category = query_params.get("category")
            tags = query_params.get("tags")
            min_importance = query_params.get("min_importance")
            limit = int(query_params.get("limit", 10))
            include_semantic = query_params.get("include_semantic", "true").lower() == "true"
            
            # Parse tags
            tag_list = None
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",")]
            
            # Parse importance
            min_imp = None
            if min_importance:
                try:
                    min_imp = int(min_importance)
                except ValueError:
                    pass
        else:
            # Use POST body
            if search_params is None:
                raise HTTPException(status_code=400, detail="Request body required for POST")
            
            query = search_params.query
            project = search_params.project
            category = search_params.category
            tag_list = search_params.tags
            min_imp = search_params.min_importance
            limit = search_params.limit
            include_semantic = search_params.include_semantic
        
        # Perform search
        results = service.search_memories(
            query=query,
            project=project,
            category=category,
            tags=tag_list,
            min_importance=min_imp or 0,
            limit=limit,
            include_semantic=include_semantic
        )
        
        logger.info(f"Search: '{query}' returned {len(results)} results")
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/context", response_class=PlainTextResponse)
async def generate_context(
    context_req: ContextRequest,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Generate intelligent context for AI conversations"""
    try:
        context = service.get_context(
            relevant_to=context_req.relevant_to,
            project=context_req.project,
            max_tokens=context_req.max_tokens,
            include_cross_project=context_req.include_cross_project,
            protection_aware=context_req.protection_aware
        )
        
        logger.info(f"Generated context: {len(context)} characters")
        return context
        
    except Exception as e:
        logger.error(f"Context generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Capture Models
class AICaptureRequest(BaseModel):
    content: str = Field(..., description="AI response content to capture")
    ai_context: Optional[Dict[str, Any]] = Field({}, description="AI conversation context")

@app.post("/api/memory/capture-ai", response_model=Dict[str, Any])
async def capture_from_ai(
    capture_req: AICaptureRequest,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Enhanced capture specifically for AI conversations with smart categorization"""
    try:
        content = capture_req.content.strip()
        if len(content) < 10:
            raise HTTPException(status_code=400, detail="Content too short to be meaningful")
        
        ai_context = capture_req.ai_context or {}
        platform = ai_context.get('platform', 'unknown')
        detected_tags = ai_context.get('detected_tags', [])
        
        # Smart categorization for AI responses
        category = _categorize_ai_response(content)
        
        # Enhanced importance scoring based on content characteristics
        importance = _calculate_ai_importance(content, ai_context)
        
        # Extract additional tags from content
        auto_tags = _extract_ai_content_tags(content, platform)
        all_tags = list(set(detected_tags + auto_tags))
        
        # Store memory with enhanced metadata
        result = service.store_memory(
            content=content,
            category=category,
            importance=importance,
            source=f"ai_chat_{platform}",
            source_url=ai_context.get('url', ''),
            tags=all_tags,
            metadata={
                'ai_platform': platform,
                'captured_at': ai_context.get('timestamp', datetime.now().isoformat()),
                'conversation_context': ai_context.get('context_snippet', ''),
                'auto_categorized': True,
                'capture_method': 'browser_extension'
            }
        )
        
        logger.info(f"AI capture: {result['id']} from {platform} [{category}] importance={importance}")
        
        return {
            "status": "captured",
            "id": result["id"],
            "category": category,
            "importance": importance,
            "tags": all_tags,
            "platform": platform,
            "message": f"Successfully captured {category} from {platform} with importance {importance}"
        }
        
    except Exception as e:
        logger.error(f"AI capture error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _categorize_ai_response(content: str) -> str:
    """Smart categorization based on AI response characteristics"""
    content_lower = content.lower()
    
    # Solution indicators
    if any(indicator in content_lower for indicator in [
        'here\'s how', 'solution', 'fix this', 'resolve', 'troubleshoot',
        'step 1', 'first,', 'to solve', 'the answer is', 'here\'s the fix'
    ]):
        return 'solution'
    
    # Pattern/method indicators
    if any(indicator in content_lower for indicator in [
        'pattern', 'approach', 'method', 'technique', 'strategy',
        'best practice', 'recommended way', 'common pattern'
    ]):
        return 'pattern'
    
    # Code/technical indicators
    if '```' in content or any(indicator in content_lower for indicator in [
        'function', 'class', 'import', 'const ', 'let ', 'var ',
        'def ', 'public ', 'private ', 'async ', 'await '
    ]):
        return 'code'
    
    # Configuration indicators
    if any(indicator in content_lower for indicator in [
        'config', 'setting', 'environment', 'variable', '.env',
        'configuration', 'setup', 'install'
    ]):
        return 'configuration'
        
    # Learning/insight indicators  
    if any(indicator in content_lower for indicator in [
        'important to', 'key insight', 'remember that', 'note that',
        'keep in mind', 'understanding', 'concept'
    ]):
        return 'insight'
    
    # Default to insight for general knowledge
    return 'insight'

def _calculate_ai_importance(content: str, ai_context: dict) -> int:
    """Calculate importance score based on content characteristics"""
    base_importance = 6
    
    # Length bonus - longer responses often contain more detail
    if len(content) > 500:
        base_importance += 2
    elif len(content) > 200:
        base_importance += 1
    
    # Code snippet bonus
    if '```' in content:
        base_importance += 2
    
    # Step-by-step instruction bonus
    if any(indicator in content.lower() for indicator in [
        'step 1', 'first,', 'next,', 'then,', 'finally,'
    ]):
        base_importance += 1
    
    # Technical depth bonus
    if any(indicator in content.lower() for indicator in [
        'configuration', 'implementation', 'architecture', 'framework'
    ]):
        base_importance += 1
    
    # Problem-solving bonus
    if any(indicator in content.lower() for indicator in [
        'error', 'fix', 'solution', 'resolve', 'troubleshoot'
    ]):
        base_importance += 1
    
    # Cap at maximum importance
    return min(base_importance, 10)

def _extract_ai_content_tags(content: str, platform: str) -> list:
    """Extract relevant tags from AI response content"""
    tags = []
    content_lower = content.lower()
    
    # Platform tag
    if platform != 'unknown':
        tags.append(platform)
    
    # Technology tags
    tech_keywords = {
        'react': ['react', 'jsx', 'component', 'hook', 'usestate', 'useeffect'],
        'python': ['python', 'def ', 'import ', 'pip install', 'django', 'flask'],
        'javascript': ['javascript', 'js', 'const ', 'let ', 'var ', 'function'],
        'database': ['database', 'sql', 'query', 'table', 'mysql', 'postgres'],
        'api': ['api', 'endpoint', 'rest', 'graphql', 'http', 'request'],
        'css': ['css', 'style', 'flexbox', 'grid', 'responsive'],
        'git': ['git', 'commit', 'branch', 'merge', 'repository'],
        'docker': ['docker', 'container', 'dockerfile', 'compose'],
        'aws': ['aws', 'ec2', 's3', 'lambda', 'cloudformation'],
        'security': ['security', 'auth', 'jwt', 'oauth', 'encryption']
    }
    
    for tag, keywords in tech_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            tags.append(tag)
    
    # Problem type tags
    if any(word in content_lower for word in ['error', 'bug', 'fix', 'debug']):
        tags.append('debugging')
    
    if any(word in content_lower for word in ['optimize', 'performance', 'speed', 'slow']):
        tags.append('optimization')
    
    if any(word in content_lower for word in ['config', 'setup', 'install']):
        tags.append('configuration')
    
    return tags

# Article Triage Endpoints
class ArticleAnalysisRequest(BaseModel):
    content: str = Field(..., description="Article content to analyze")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Optional metadata")
    quick_mode: Optional[bool] = Field(False, description="Use quick analysis mode")

class ArticleTriageRequest(BaseModel):
    content: str = Field(..., description="Article content to triage")
    project: Optional[str] = Field(None, description="Project name")
    tags: Optional[List[str]] = Field(None, description="Additional tags")
    source: Optional[str] = Field(None, description="Source of the article")
    source_url: Optional[str] = Field(None, description="Original URL")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Additional metadata")

@app.post("/api/article/analyze", response_model=Dict[str, Any])
async def analyze_article(
    request: ArticleAnalysisRequest,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Analyze article and generate triage metadata without storing"""
    try:
        triage_service = get_triage_service(service.db_path)
        
        # Run article triage
        result = await triage_service.triage_content(
            content=request.content,
            metadata=request.metadata
        )
        
        if not result.get('is_article'):
            return {
                "status": "not_article",
                "content_type": result.get('content_type'),
                "message": result.get('message')
            }
        
        logger.info(f"Article analyzed: {result['analysis'].get('title', 'Untitled')}")
        
        return {
            "status": "analyzed",
            "analysis": result['analysis'],
            "metadata": result['metadata'],
            "recommendations": result['recommendations']
        }
        
    except Exception as e:
        logger.error(f"Article analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/article/triage", response_model=Dict[str, Any])
async def triage_and_store_article(
    request: ArticleTriageRequest,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Intelligently triage and store article with enhanced metadata"""
    try:
        triage_service = get_triage_service(service.db_path)
        
        # Run article triage
        triage_result = await triage_service.triage_content(
            content=request.content,
            metadata={
                'source': request.source,
                'source_url': request.source_url,
                'capture_method': request.metadata.get('capture_method', 'api'),
                **request.metadata
            }
        )
        
        if not triage_result.get('is_article'):
            # Fall back to regular memory storage
            memory_result = service.store_memory(
                content=request.content,
                project=request.project,
                category=triage_result.get('content_type', 'note'),
                tags=request.tags,
                source=request.source,
                source_url=request.source_url,
                metadata=request.metadata
            )
            
            return {
                "status": "stored_as_memory",
                "memory_id": memory_result['id'],
                "content_type": triage_result.get('content_type'),
                "message": "Content stored as regular memory (not detected as article)"
            }
        
        # Store as article with enhanced metadata
        analysis = triage_result['analysis']
        recommendations = triage_result['recommendations']
        
        # Combine tags
        all_tags = list(set(
            (request.tags or []) + 
            recommendations.get('suggested_tags', []) +
            ['article', analysis.get('classification', 'reference')]
        ))
        
        # Store the memory with article metadata
        memory_result = service.store_memory(
            content=request.content,
            project=request.project,
            category='article',
            tags=all_tags,
            importance=max(
                analysis.get('actionability_score', 5),
                analysis.get('relevance_score', 5)
            ),
            source=request.source or 'article_triage',
            source_url=request.source_url,
            metadata={
                **request.metadata,
                'article_analysis': analysis,
                'triage_metadata': triage_result['metadata'],
                'recommendations': recommendations
            }
        )
        
        # Store article-specific metadata
        triage_service.store_article_metadata(memory_result['id'], triage_result)
        
        logger.info(f"Article triaged and stored: {memory_result['id']} - {analysis.get('title', 'Untitled')}")
        
        return {
            "status": "triaged_and_stored",
            "memory_id": memory_result['id'],
            "title": analysis.get('title', 'Untitled'),
            "classification": analysis.get('classification'),
            "actionability_score": analysis.get('actionability_score'),
            "relevance_score": analysis.get('relevance_score'),
            "summary": analysis.get('summary'),
            "recommendations": recommendations,
            "message": f"Article successfully triaged as '{analysis.get('classification')}' with priority '{recommendations.get('priority')}'"
        }
        
    except Exception as e:
        logger.error(f"Article triage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/article/actionable", response_model=Dict[str, Any])
async def get_actionable_articles(
    limit: int = 10,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Get articles classified as 'implement_now' or with high actionability"""
    try:
        triage_service = get_triage_service(service.db_path)
        articles = triage_service.get_actionable_articles(limit)
        
        logger.info(f"Retrieved {len(articles)} actionable articles")
        
        return {
            "articles": articles,
            "count": len(articles),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get actionable articles error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/article/stats", response_model=Dict[str, Any])
async def get_article_statistics(
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Get statistics about triaged articles"""
    try:
        triage_service = get_triage_service(service.db_path)
        stats = triage_service.get_article_stats()
        
        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Article statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/article/extract", response_model=Dict[str, Any])
async def extract_action_items(
    memory_id: str,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Extract actionable items from a stored article"""
    try:
        # Get the memory
        memories = service.search_memories(query=None, limit=1)
        memory = None
        for m in memories:
            if m.get('id') == memory_id:
                memory = m
                break
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Get article metadata
        triage_service = get_triage_service(service.db_path)
        
        # Re-analyze for action items if needed
        triage_result = await triage_service.triage_content(
            content=memory['content'],
            metadata={'focus': 'action_items'}
        )
        
        if not triage_result.get('is_article'):
            return {
                "status": "not_article",
                "message": "Memory is not an article"
            }
        
        action_items = triage_result['analysis'].get('action_items', [])
        technologies = triage_result['analysis'].get('technologies', [])
        
        return {
            "memory_id": memory_id,
            "title": triage_result['analysis'].get('title', 'Untitled'),
            "action_items": action_items,
            "technologies": technologies,
            "implementation_steps": [
                f"Research/install {tech}" for tech in technologies[:3]
            ] + action_items[:5],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extract action items error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/relate", response_model=Dict[str, Any])
async def find_related_memories(
    relate_req: RelateRequest,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Find memories related to given content"""
    try:
        related = service.find_related_memories(
            content=relate_req.content,
            limit=relate_req.limit,
            cross_project=relate_req.cross_project
        )
        
        logger.info(f"Found {len(related)} related memories")
        
        return {
            "content": relate_req.content,
            "related": related,
            "count": len(related),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Related memories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/article/reclassify", response_model=Dict[str, Any])
async def reclassify_article(request: Dict[str, Any]):
    """Reclassify an article based on user feedback"""
    try:
        memory_id = request.get('memory_id')
        new_classification = request.get('new_classification', 'note')
        feedback = request.get('feedback', '')
        
        # Update the article_metadata table
        db_path = Path.home() / ".ai-memory" / "memories.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Update classification and set actionability to 0 for non-articles
        cursor.execute("""
            UPDATE article_metadata 
            SET classification = ?, 
                actionability_score = 0,
                updated_at = datetime('now')
            WHERE memory_id = ?
        """, (new_classification, memory_id))
        
        # Log the feedback for future training improvements
        cursor.execute("""
            INSERT INTO article_feedback (memory_id, feedback_type, feedback_text, created_at)
            VALUES (?, 'reclassification', ?, datetime('now'))
        """, (memory_id, f"Reclassified from article to {new_classification}: {feedback}"))
        
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        
        logger.info(f"Reclassified {memory_id} as {new_classification}")
        
        return {
            "success": True,
            "memory_id": memory_id,
            "new_classification": new_classification,
            "rows_affected": rows_affected,
            "message": f"Successfully reclassified as {new_classification}"
        }
        
    except Exception as e:
        logger.error(f"Reclassification error: {e}")
        # Create feedback table if it doesn't exist
        try:
            conn = sqlite3.connect(str(Path.home() / ".ai-memory" / "memories.db"))
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS article_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id TEXT,
                    feedback_type TEXT,
                    feedback_text TEXT,
                    created_at DATETIME
                )
            """)
            conn.commit()
            conn.close()
            return {"success": True, "message": "Feedback table created, please try again"}
        except:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/article/reclassification_history", response_model=Dict[str, Any])
async def get_reclassification_history(limit: int = 50):
    """Get recent reclassification history for learning and analysis"""
    try:
        db_path = Path.home() / ".ai-memory" / "memories.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get recent reclassifications with memory details
        cursor.execute("""
            SELECT 
                af.memory_id,
                af.feedback_text,
                af.created_at,
                m.content,
                m.category,
                am.classification,
                am.actionability_score
            FROM article_feedback af
            LEFT JOIN memories m ON af.memory_id = m.id
            LEFT JOIN article_metadata am ON af.memory_id = am.memory_id
            WHERE af.feedback_type = 'reclassification'
            ORDER BY af.created_at DESC
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        
        return {
            "history": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Reclassification history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics and analytics
@app.get("/api/memory/stats", response_model=Dict[str, Any])
async def get_statistics(service: UniversalMemoryService = Depends(get_memory_service_instance)):
    """Get system statistics"""
    try:
        stats = service.get_statistics()
        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/projects", response_model=Dict[str, Any])
async def get_projects(service: UniversalMemoryService = Depends(get_memory_service_instance)):
    """Get all projects with statistics"""
    try:
        projects = service.get_projects()
        return projects
    except Exception as e:
        logger.error(f"Projects error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export functionality
@app.get("/api/memory/export")
async def export_memories(
    format: str = "markdown",
    project: Optional[str] = None,
    category: Optional[str] = None,
    limit: Optional[int] = None,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Export memories in various formats"""
    try:
        exported_data = service.export_memories(
            format=format,
            project=project,
            category=category,
            limit=limit
        )
        
        logger.info(f"Exported memories: format={format}, length={len(exported_data)}")
        
        if format == "json":
            return JSONResponse(content=json.loads(exported_data))
        else:
            return PlainTextResponse(content=exported_data)
            
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI integration helpers
@app.get("/ai/prompt")
async def generate_ai_prompt(
    question: str,
    ai_platform: str = "generic",
    project: Optional[str] = None,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Generate AI prompt with context"""
    try:
        # Get relevant context
        context = service.get_context(
            relevant_to=question,
            project=project,
            max_tokens=3000
        )
        
        # Format for different AI platforms
        if ai_platform == "chatgpt":
            prompt = f"""I'm working on a project and have some relevant context from my previous work:

{context}

Current question: {question}"""
        
        elif ai_platform == "claude":
            prompt = f"""I'm working on a project and have some relevant context from my previous solutions:

{context}

Please help me with: {question}"""
        
        else:  # generic
            prompt = f"""Context from my previous work:

{context}

Question: {question}"""
        
        logger.info(f"Generated AI prompt: platform={ai_platform}, length={len(prompt)}")
        return PlainTextResponse(content=prompt)
        
    except Exception as e:
        logger.error(f"AI prompt generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Maintenance operations
@app.post("/api/memory/cleanup", response_model=Dict[str, Any])
async def cleanup_memories(
    remove_duplicates: bool = False,
    remove_old: bool = False,
    days_threshold: int = 365,
    remove_unused: bool = False,
    access_threshold: int = 0,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Clean up memories"""
    try:
        result = service.cleanup_memories(
            remove_duplicates=remove_duplicates,
            remove_old=remove_old,
            days_threshold=days_threshold,
            remove_unused=remove_unused,
            access_threshold=access_threshold
        )
        
        logger.info(f"Cleanup completed: {result}")
        return {
            "cleanup_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/backup", response_model=Dict[str, Any])
async def backup_database(
    destination: Optional[str] = None,
    service: UniversalMemoryService = Depends(get_memory_service_instance)
):
    """Create database backup"""
    try:
        backup_file = service.backup_database(destination)
        
        logger.info(f"Backup created: {backup_file}")
        return {
            "backup_file": backup_file,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Quick access endpoints for browser integration
@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Universal AI Memory System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/health",
            "store": "/api/memory/store",
            "search": "/api/memory/search",
            "context": "/api/memory/context"
        },
        "timestamp": datetime.now().isoformat()
    }

# Legacy endpoints for backward compatibility
@app.post("/memory/store")
async def legacy_store_memory(memory: MemoryStore, service: UniversalMemoryService = Depends(get_memory_service_instance)):
    """Legacy endpoint for memory storage"""
    return await store_memory(memory, service)

@app.get("/memory/search")
@app.post("/memory/search")
async def legacy_search_memories(request: Request, search_params: Optional[MemorySearch] = None, service: UniversalMemoryService = Depends(get_memory_service_instance)):
    """Legacy endpoint for memory search"""
    return await search_memories(request, search_params, service)

@app.post("/memory/context")
async def legacy_generate_context(context_req: ContextRequest, service: UniversalMemoryService = Depends(get_memory_service_instance)):
    """Legacy endpoint for context generation"""
    return await generate_context(context_req, service)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint {request.url.path} not found",
            "available_endpoints": [
                "/docs",
                "/api/health",
                "/api/memory/store",
                "/api/memory/search",
                "/api/memory/context"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal AI Memory API Service")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8091, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    print(f"🧠 Starting Universal AI Memory API Service")
    print(f"📊 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔍 Health Check: http://{args.host}:{args.port}/api/health")
    print(f"💾 Memory Storage: http://{args.host}:{args.port}/api/memory/store")
    print(f"🔎 Memory Search: http://{args.host}:{args.port}/api/memory/search")
    print()
    
    uvicorn.run(
        "api_service:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )
@app.get("/action-plans", response_class=HTMLResponse)

@app.get("/action_plans_viewer.html", response_class=HTMLResponse)
async def action_plans_viewer_html():
    """Serve the Action Plans Dashboard HTML file directly"""
    dashboard_file = Path(__file__).parent.parent / "action_plans_viewer.html"
    
    if dashboard_file.exists():
        with open(dashboard_file, "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        return HTMLResponse(content="<h1>Action Plans Dashboard not found</h1>")
async def action_plans_dashboard():
    """Serve the Action Plans Dashboard"""
    dashboard_file = Path(__file__).parent.parent / "action_plans_viewer.html"
    
    if dashboard_file.exists():
        with open(dashboard_file, "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        return HTMLResponse(content="<h1>Action Plans Dashboard not found</h1>")

# Article management endpoints
@app.post("/api/article/reclassify")
async def reclassify_article(request: Request):
    """Reclassify a memory item (e.g., mark as not an article)"""
    try:
        data = await request.json()
        memory_id = data.get('memory_id')
        new_classification = data.get('new_classification', 'note')
        feedback = data.get('feedback', '')
        
        # Update the memory item's classification in the database
        db_path = Path.home() / ".ai-memory" / "memories.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Update the memory's metadata to mark it as not an article
        cursor.execute("""
            UPDATE memories 
            SET metadata = json_set(
                COALESCE(metadata, '{}'),
                '$.is_article', false,
                '$.classification', ?,
                '$.user_feedback', ?,
                '$.reclassified_at', datetime('now')
            )
            WHERE id = ?
        """, (new_classification, feedback, memory_id))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Item reclassified successfully"}
    except Exception as e:
        logger.error(f"Error reclassifying article: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/article/complete")
async def mark_article_complete(request: Request):
    """Mark an article as completed"""
    try:
        data = await request.json()
        memory_id = data.get('memory_id')
        
        # Update the memory item's status in the database
        db_path = Path.home() / ".ai-memory" / "memories.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Update the memory's metadata to mark it as completed
        cursor.execute("""
            UPDATE memories 
            SET metadata = json_set(
                COALESCE(metadata, '{}'),
                '$.completed', true,
                '$.completed_at', datetime('now'),
                '$.status', 'completed'
            )
            WHERE id = ?
        """, (memory_id,))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Article marked as completed"}
    except Exception as e:
        logger.error(f"Error marking article as complete: {e}")
        return {"success": False, "error": str(e)}
