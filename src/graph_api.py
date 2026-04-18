#!/usr/bin/env python3
"""
Graph API Module - Milestone D1
FastAPI endpoints for graph operations and search
"""

import json
import sqlite3
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

try:
    from entity_extraction import extract_entities
    from graph_operations import get_graph_operations
except ImportError:
    from .entity_extraction import extract_entities
    from .graph_operations import get_graph_operations

logger = logging.getLogger(__name__)

# API Router
graph_router = APIRouter(prefix="/api/graph", tags=["graph"])

# ============================================
# Pydantic Models
# ============================================

class EntitySearchResult(BaseModel):
    """Entity search result"""
    id: int
    type: str
    name: str
    normalized_name: Optional[str] = None
    belief: float
    match_score: Optional[float] = None
    project_id: str

class DocumentSearchResult(BaseModel):
    """Document search result"""
    id: int
    title: Optional[str]
    url: Optional[str]
    snippet: Optional[str]
    match_score: Optional[float] = None
    capture_id: Optional[str]
    project_id: str

class EntityDetail(BaseModel):
    """Detailed entity information"""
    id: int
    type: str
    name: str
    normalized_name: Optional[str]
    belief: float
    project_id: str
    created_at: str
    edges_in: List[Dict[str, Any]]
    edges_out: List[Dict[str, Any]]
    aliases: List[str]
    documents: List[Dict[str, Any]]

class ExtractRequest(BaseModel):
    """Entity extraction request"""
    text: str = Field(..., description="Text to extract entities from")
    doc_id: Optional[int] = Field(None, description="Document ID to link entities to")
    project: Optional[str] = Field("vader-lab", description="Project ID")
    persist: bool = Field(True, description="Whether to persist entities to database")

class ExtractResponse(BaseModel):
    """Entity extraction response"""
    entities: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    diagnostics: Dict[str, Any]
    persisted: bool

# ============================================
# Database Helper
# ============================================

def get_db_connection() -> sqlite3.Connection:
    """Get database connection with row factory"""
    # Use UMS database for now (should be configurable)
    db_path = Path("/usr/local/share/universal-memory-system/memories.db")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

# ============================================
# API Endpoints
# ============================================

@graph_router.get("/entities", response_model=List[EntitySearchResult])
async def search_entities(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    project_id: str = Query("vader-lab", description="Project ID filter"),
    source: Optional[str] = Query(None, enum=["rule", "llm", "any"], description="Filter by extraction source")
):
    """
    Search entities using FTS
    
    Returns entities matching the search query ordered by relevance
    """
    conn = get_db_connection()
    try:
        # Build query with optional source filter
        if source and source != "any":
            query = """
                SELECT 
                    e.id, e.type, e.name, e.normalized_name, e.belief, e.project_id,
                    bm25(entity_fts) as match_score
                FROM entity_fts 
                JOIN entities e ON entity_fts.entity_id = e.id
                WHERE entity_fts MATCH ?
                  AND e.project_id = ?
                  AND e.source = ?
                ORDER BY bm25(entity_fts)
                LIMIT ? OFFSET ?
            """
            cursor = conn.execute(query, (q, project_id, source, limit, offset))
        else:
            query = """
                SELECT 
                    e.id, e.type, e.name, e.normalized_name, e.belief, e.project_id,
                    bm25(entity_fts) as match_score
                FROM entity_fts 
                JOIN entities e ON entity_fts.entity_id = e.id
                WHERE entity_fts MATCH ?
                  AND e.project_id = ?
                ORDER BY bm25(entity_fts)
                LIMIT ? OFFSET ?
            """
            cursor = conn.execute(query, (q, project_id, limit, offset))
        results = []
        
        for row in cursor:
            results.append(EntitySearchResult(
                id=row['id'],
                type=row['type'],
                name=row['name'],
                normalized_name=row['normalized_name'],
                belief=row['belief'],
                match_score=row['match_score'],
                project_id=row['project_id']
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Entity search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@graph_router.get("/documents", response_model=List[DocumentSearchResult])
async def search_documents(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    project_id: str = Query("vader-lab", description="Project ID filter")
):
    """
    Search documents using FTS
    
    Returns documents matching the search query ordered by relevance
    """
    conn = get_db_connection()
    try:
        # Search using FTS
        query = """
            SELECT 
                d.id, d.title, d.url, d.capture_id, d.project_id,
                snippet(doc_fts, 0, '<b>', '</b>', '...', 64) as snippet,
                bm25(doc_fts) as match_score
            FROM doc_fts 
            JOIN document_nodes d ON doc_fts.document_id = d.id
            WHERE doc_fts MATCH ?
              AND d.project_id = ?
            ORDER BY bm25(doc_fts)
            LIMIT ? OFFSET ?
        """
        
        cursor = conn.execute(query, (q, project_id, limit, offset))
        results = []
        
        for row in cursor:
            results.append(DocumentSearchResult(
                id=row['id'],
                title=row['title'],
                url=row['url'],
                snippet=row['snippet'],
                match_score=row['match_score'],
                capture_id=row['capture_id'],
                project_id=row['project_id']
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@graph_router.get("/entity/{entity_id}", response_model=EntityDetail)
async def get_entity_detail(entity_id: int):
    """
    Get detailed entity information including edges and documents
    
    Returns complete entity data with all relationships
    """
    conn = get_db_connection()
    try:
        # Get entity
        cursor = conn.execute(
            "SELECT * FROM entities WHERE id = ?",
            (entity_id,)
        )
        entity = cursor.fetchone()
        
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # Get incoming edges
        cursor = conn.execute("""
            SELECT e.*, src.name as src_name, src.type as src_type
            FROM edges e
            JOIN entities src ON e.src_id = src.id
            WHERE e.dst_id = ?
            ORDER BY e.created_at DESC
            LIMIT 100
        """, (entity_id,))
        
        edges_in = []
        for row in cursor:
            edges_in.append({
                "id": row['id'],
                "type": row['type'],
                "src_id": row['src_id'],
                "src_name": row['src_name'],
                "src_type": row['src_type'],
                "confidence": row['confidence'],
                "props": json.loads(row['props_json']) if row['props_json'] else {}
            })
        
        # Get outgoing edges
        cursor = conn.execute("""
            SELECT e.*, dst.name as dst_name, dst.type as dst_type
            FROM edges e
            JOIN entities dst ON e.dst_id = dst.id
            WHERE e.src_id = ?
            ORDER BY e.created_at DESC
            LIMIT 100
        """, (entity_id,))
        
        edges_out = []
        for row in cursor:
            edges_out.append({
                "id": row['id'],
                "type": row['type'],
                "dst_id": row['dst_id'],
                "dst_name": row['dst_name'],
                "dst_type": row['dst_type'],
                "confidence": row['confidence'],
                "props": json.loads(row['props_json']) if row['props_json'] else {}
            })
        
        # Get aliases
        cursor = conn.execute(
            "SELECT alias FROM entity_aliases WHERE entity_id = ?",
            (entity_id,)
        )
        aliases = [row['alias'] for row in cursor]
        
        # Get documents that mention this entity
        cursor = conn.execute("""
            SELECT DISTINCT d.id, d.title, d.url, d.capture_id
            FROM edges e
            JOIN document_nodes d ON e.src_id = d.id
            WHERE e.dst_id = ? AND e.type = 'MENTIONS'
            ORDER BY d.created_at DESC
            LIMIT 20
        """, (entity_id,))
        
        documents = []
        for row in cursor:
            documents.append({
                "id": row['id'],
                "title": row['title'],
                "url": row['url'],
                "capture_id": row['capture_id']
            })
        
        return EntityDetail(
            id=entity['id'],
            type=entity['type'],
            name=entity['name'],
            normalized_name=entity['normalized_name'],
            belief=entity['belief'],
            project_id=entity['project_id'],
            created_at=entity['created_at'],
            edges_in=edges_in,
            edges_out=edges_out,
            aliases=aliases,
            documents=documents
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get entity detail failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@graph_router.post("/extract", response_model=ExtractResponse)
async def extract_entities_endpoint(
    request: ExtractRequest,
    mode: str = Query("rule", enum=["rule", "llm", "hybrid"], description="Extraction mode"),
    min_confidence: float = Query(0.2, ge=0.0, le=1.0, description="Minimum confidence for LLM entities")
):
    """
    Extract entities from text using specified mode
    
    Modes:
    - rule: Rule-based extraction only
    - llm: LLM extraction only (requires API key)
    - hybrid: Both rule and LLM, merged
    
    Optionally persists entities and edges to the database
    """
    try:
        # Choose extraction method based on mode
        if mode == "rule":
            from entity_extraction import extract_entities
            result = extract_entities(
                text=request.text,
                doc_id=request.doc_id,
                project=request.project
            )
        elif mode == "llm":
            from llm_extraction import extract_with_llm
            result = extract_with_llm(
                text=request.text,
                context={"doc_id": request.doc_id, "project": request.project}
            )
            # Filter by confidence
            result["entities"] = [e for e in result.get("entities", []) if e.get("confidence", 0) >= min_confidence]
            result["edges"] = [e for e in result.get("edges", []) if e.get("confidence", 0) >= min_confidence]
        else:  # hybrid
            from entity_extraction import hybrid_extract
            result = hybrid_extract(
                text=request.text,
                doc_id=request.doc_id,
                project=request.project,
                min_confidence=min_confidence
            )
        
        # Persist if requested
        if request.persist and result['entities']:
            graph_ops = get_graph_operations()
            persisted_entities = []
            
            # Create entities
            for entity in result['entities']:
                entity_id = graph_ops.upsert_entity(
                    project_id=request.project or "vader-lab",
                    name=entity['name'],
                    etype=entity['type'],
                    belief=entity.get('confidence', 0.7),
                    source=entity.get('source', 'rule'),
                    confidence=entity.get('confidence', 0.7),
                    extractor_version=f"{entity.get('source', 'rule')}@D2"
                )
                entity['id'] = entity_id
                persisted_entities.append(entity)
            
            # Create edges if doc_id provided
            if request.doc_id and result['edges']:
                for edge in result['edges']:
                    if edge['type'] == 'MENTIONS':
                        # Find the entity ID
                        entity_data = edge['dst_entity']
                        entity_id = next(
                            (e['id'] for e in persisted_entities 
                             if e['name'] == entity_data['name'] and e['type'] == entity_data['type']),
                            None
                        )
                        if entity_id:
                            graph_ops.upsert_edge(
                                project_id=request.project or "vader-lab",
                                src_id=request.doc_id,
                                dst_id=entity_id,
                                etype=edge['type'],
                                key_props=edge.get('properties', {}),
                                confidence=edge.get('confidence', 0.8),
                                origin="extractor",
                                extractor_version="d1"
                            )
                    elif edge['type'] == 'RELATED_TO':
                        # Find both entity IDs
                        src_entity = edge['src_entity']
                        dst_entity = edge['dst_entity']
                        src_id = next(
                            (e['id'] for e in persisted_entities 
                             if e['name'] == src_entity['name'] and e['type'] == src_entity['type']),
                            None
                        )
                        dst_id = next(
                            (e['id'] for e in persisted_entities 
                             if e['name'] == dst_entity['name'] and e['type'] == dst_entity['type']),
                            None
                        )
                        if src_id and dst_id:
                            graph_ops.upsert_edge(
                                project_id=request.project or "vader-lab",
                                src_id=src_id,
                                dst_id=dst_id,
                                etype=edge['type'],
                                key_props=edge.get('properties', {}),
                                confidence=edge.get('confidence', 0.6),
                                origin="extractor",
                                extractor_version="d1"
                            )
            
            result['entities'] = persisted_entities
        
        return ExtractResponse(
            entities=result['entities'],
            edges=result['edges'],
            diagnostics=result['diagnostics'],
            persisted=request.persist
        )
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Additional Utility Endpoints
# ============================================

@graph_router.get("/stats")
async def get_graph_stats(project_id: str = Query("vader-lab")):
    """
    Get graph statistics for a project
    
    Returns counts of entities, edges, and documents
    """
    conn = get_db_connection()
    try:
        stats = {}
        
        # Entity counts by type
        cursor = conn.execute("""
            SELECT type, COUNT(*) as count
            FROM entities
            WHERE project_id = ?
            GROUP BY type
        """, (project_id,))
        
        entity_counts = {}
        for row in cursor:
            entity_counts[row['type']] = row['count']
        stats['entities'] = entity_counts
        
        # Entity counts by source
        cursor = conn.execute("""
            SELECT source, COUNT(*) as count
            FROM entities
            WHERE project_id = ?
            GROUP BY source
        """, (project_id,))
        
        source_counts = {}
        for row in cursor:
            source_counts[row['source'] or 'rule'] = row['count']
        stats['entities_by_source'] = source_counts
        
        # Edge counts by type
        cursor = conn.execute("""
            SELECT type, COUNT(*) as count
            FROM edges
            WHERE project_id = ?
            GROUP BY type
        """, (project_id,))
        
        edge_counts = {}
        for row in cursor:
            edge_counts[row['type']] = row['count']
        stats['edges'] = edge_counts
        
        # Document count
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM document_nodes WHERE project_id = ?",
            (project_id,)
        )
        stats['documents'] = cursor.fetchone()['count']
        
        # Total entities
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM entities WHERE project_id = ?",
            (project_id,)
        )
        stats['total_entities'] = cursor.fetchone()['count']
        
        # Total edges
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM edges WHERE project_id = ?",
            (project_id,)
        )
        stats['total_edges'] = cursor.fetchone()['count']
        
        return stats
        
    except Exception as e:
        logger.error(f"Get graph stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@graph_router.get("/recent-entities")
async def get_recent_entities(
    limit: int = Query(10, ge=1, le=50),
    project_id: str = Query("vader-lab")
):
    """
    Get recently created entities
    
    Returns the most recently added entities
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT id, type, name, normalized_name, belief, created_at
            FROM entities
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (project_id, limit))
        
        results = []
        for row in cursor:
            results.append({
                "id": row['id'],
                "type": row['type'],
                "name": row['name'],
                "normalized_name": row['normalized_name'],
                "belief": row['belief'],
                "created_at": row['created_at']
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Get recent entities failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Export router
__all__ = ['graph_router']