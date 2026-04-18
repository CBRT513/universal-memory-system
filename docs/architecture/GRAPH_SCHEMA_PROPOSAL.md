# Knowledge Graph Schema Proposal
**Version**: 1.0  
**Date**: August 20, 2025  
**Status**: DRAFT  
**Milestone**: C

---

## Overview

This document proposes a hybrid storage approach using SQLite (existing) with graph-oriented tables, optimized for the capture pipeline while enabling rich relationship queries.

---

## Core Design Principles

1. **Leverage Existing Infrastructure**: Build on SQLite, avoid new dependencies
2. **Performance First**: Sub-500ms queries for common operations
3. **Extensible**: Schema can evolve without breaking changes
4. **Pipeline-Friendly**: Minimal overhead on capture flow
5. **Semantic-Rich**: Capture meaning, not just connections

---

## Node Types & Properties

### 1. Document Node
**Purpose**: Represents a captured article/page  
**Table**: `graph_documents`

```sql
CREATE TABLE graph_documents (
    id TEXT PRIMARY KEY,  -- doc_{uuid}
    capture_id TEXT UNIQUE NOT NULL,  -- Links to captures table
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    domain TEXT NOT NULL,
    author TEXT,
    published_date TEXT,
    captured_date TEXT NOT NULL,
    summary TEXT,
    extraction_method TEXT,  -- adapter used
    word_count INTEGER,
    language TEXT DEFAULT 'en',
    confidence_score REAL DEFAULT 1.0,
    metadata JSON,  -- Flexible additional properties
    embedding BLOB,  -- Vector for similarity (future)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (capture_id) REFERENCES captures(id)
);
```

### 2. Entity Node
**Purpose**: Extracted entities (people, orgs, concepts, technologies)  
**Table**: `graph_entities`

```sql
CREATE TABLE graph_entities (
    id TEXT PRIMARY KEY,  -- ent_{type}_{hash}
    type TEXT NOT NULL,  -- person|org|concept|tech|location|event
    name TEXT NOT NULL,
    canonical_name TEXT,  -- Normalized/disambiguated
    description TEXT,
    confidence_score REAL DEFAULT 0.5,
    occurrence_count INTEGER DEFAULT 1,
    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,  -- Wikipedia URL, GitHub repo, etc.
    embedding BLOB,  -- Vector for similarity
    
    UNIQUE(type, canonical_name)
);
```

### 3. Topic Node
**Purpose**: High-level topics/categories  
**Table**: `graph_topics`

```sql
CREATE TABLE graph_topics (
    id TEXT PRIMARY KEY,  -- topic_{hash}
    name TEXT UNIQUE NOT NULL,
    parent_topic_id TEXT,  -- Hierarchical topics
    description TEXT,
    document_count INTEGER DEFAULT 0,
    entity_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    
    FOREIGN KEY (parent_topic_id) REFERENCES graph_topics(id)
);
```

### 4. Project Node
**Purpose**: User-defined project contexts  
**Table**: `graph_projects`

```sql
CREATE TABLE graph_projects (
    id TEXT PRIMARY KEY,  -- proj_{name}
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    document_count INTEGER DEFAULT 0,
    metadata JSON
);
```

---

## Edge Types & Relationships

### Core Edge Table
**Table**: `graph_edges`

```sql
CREATE TABLE graph_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_node_id TEXT NOT NULL,
    from_node_type TEXT NOT NULL,  -- document|entity|topic|project
    to_node_id TEXT NOT NULL,
    to_node_type TEXT NOT NULL,
    edge_type TEXT NOT NULL,  -- See edge types below
    weight REAL DEFAULT 1.0,  -- Strength/confidence
    properties JSON,  -- Edge-specific data
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(from_node_id, to_node_id, edge_type),
    INDEX idx_from_node (from_node_id, from_node_type),
    INDEX idx_to_node (to_node_id, to_node_type),
    INDEX idx_edge_type (edge_type)
);
```

### Edge Types

#### Document → Entity: "MENTIONS"
```json
{
    "edge_type": "MENTIONS",
    "properties": {
        "frequency": 5,
        "positions": [102, 450, 789, 1203, 1567],
        "context_snippets": ["...AI company Anthropic...", "..."],
        "sentiment": 0.7
    }
}
```

#### Document → Document: "REFERENCES"
```json
{
    "edge_type": "REFERENCES", 
    "properties": {
        "reference_type": "citation|link|quote",
        "anchor_text": "as described in...",
        "section": "introduction"
    }
}
```

#### Document → Topic: "CATEGORIZED_AS"
```json
{
    "edge_type": "CATEGORIZED_AS",
    "properties": {
        "confidence": 0.85,
        "method": "adapter|classifier|manual"
    }
}
```

#### Entity → Entity: "RELATED_TO"
```json
{
    "edge_type": "RELATED_TO",
    "properties": {
        "relationship": "works_for|competitor|subsidiary|uses",
        "source": "extracted|inferred|manual",
        "confidence": 0.9
    }
}
```

#### Document → Project: "BELONGS_TO"
```json
{
    "edge_type": "BELONGS_TO",
    "properties": {
        "added_date": "2025-08-20T10:00:00Z",
        "tags": ["research", "milestone-c"]
    }
}
```

---

## Extraction Pipeline Integration

### 1. Document Creation
```python
async def create_document_node(capture_id: str, capture_data: dict):
    """Called after successful capture"""
    doc_node = {
        "id": f"doc_{uuid.uuid4().hex[:12]}",
        "capture_id": capture_id,
        "url": capture_data["source_url"],
        "title": capture_data["source_title"],
        # ... map capture fields
    }
    return await graph_service.create_node("document", doc_node)
```

### 2. Entity Extraction
```python
async def extract_and_link_entities(doc_id: str, text: str):
    """Extract entities and create edges"""
    entities = entity_extractor.extract(text)
    
    for entity in entities:
        # Create or update entity node
        entity_id = await graph_service.upsert_entity(entity)
        
        # Create MENTIONS edge
        await graph_service.create_edge(
            from_id=doc_id,
            to_id=entity_id,
            edge_type="MENTIONS",
            properties={"frequency": entity.count}
        )
```

### 3. Topic Classification
```python
async def classify_document(doc_id: str, text: str, metadata: dict):
    """Classify into topics"""
    # Use adapter metadata if available
    if metadata.get("extraction_method") == "wikipedia_adapter":
        categories = metadata.get("categories", [])
        for cat in categories:
            topic_id = await graph_service.upsert_topic(cat)
            await graph_service.create_edge(
                from_id=doc_id,
                to_id=topic_id,
                edge_type="CATEGORIZED_AS"
            )
```

---

## Query Patterns

### 1. Find Related Documents
```sql
-- Documents that share entities with given doc
SELECT DISTINCT d2.* 
FROM graph_documents d1
JOIN graph_edges e1 ON d1.id = e1.from_node_id
JOIN graph_edges e2 ON e1.to_node_id = e2.to_node_id 
JOIN graph_documents d2 ON e2.from_node_id = d2.id
WHERE d1.id = ? 
  AND e1.edge_type = 'MENTIONS'
  AND e2.edge_type = 'MENTIONS'
  AND d2.id != d1.id
ORDER BY COUNT(*) DESC;
```

### 2. Entity Co-occurrence
```sql
-- Find entities that appear together frequently
SELECT e1.name, e2.name, COUNT(*) as co_occurrences
FROM graph_edges edge1
JOIN graph_edges edge2 ON edge1.from_node_id = edge2.from_node_id
JOIN graph_entities e1 ON edge1.to_node_id = e1.id
JOIN graph_entities e2 ON edge2.to_node_id = e2.id
WHERE edge1.edge_type = 'MENTIONS'
  AND edge2.edge_type = 'MENTIONS'
  AND e1.id < e2.id
GROUP BY e1.id, e2.id
HAVING COUNT(*) > 5
ORDER BY co_occurrences DESC;
```

### 3. Topic Hierarchy
```sql
-- Recursive CTE for topic tree
WITH RECURSIVE topic_tree AS (
    SELECT * FROM graph_topics WHERE parent_topic_id IS NULL
    UNION ALL
    SELECT t.* FROM graph_topics t
    JOIN topic_tree tt ON t.parent_topic_id = tt.id
)
SELECT * FROM topic_tree;
```

---

## Performance Optimizations

### 1. Indexes
```sql
-- Critical for query performance
CREATE INDEX idx_doc_domain ON graph_documents(domain);
CREATE INDEX idx_doc_captured ON graph_documents(captured_date);
CREATE INDEX idx_entity_type ON graph_entities(type);
CREATE INDEX idx_entity_name ON graph_entities(canonical_name);
CREATE INDEX idx_edge_composite ON graph_edges(from_node_id, edge_type, to_node_id);
```

### 2. Materialized Views (Optional)
```sql
-- Pre-compute common aggregations
CREATE VIEW entity_document_counts AS
SELECT 
    e.id,
    e.name,
    e.type,
    COUNT(DISTINCT edge.from_node_id) as document_count
FROM graph_entities e
JOIN graph_edges edge ON e.id = edge.to_node_id
WHERE edge.edge_type = 'MENTIONS'
GROUP BY e.id;
```

### 3. Caching Strategy
- Cache entity lookups (high reuse)
- Cache topic hierarchies (rarely change)
- Cache document similarity scores
- Use Redis for hot paths (future)

---

## Migration Plan

### Phase 1: Schema Creation
```sql
-- migrations/004_add_graph_tables.sql
BEGIN TRANSACTION;

-- Create all tables
CREATE TABLE graph_documents ...
CREATE TABLE graph_entities ...
CREATE TABLE graph_topics ...
CREATE TABLE graph_projects ...
CREATE TABLE graph_edges ...

-- Create indexes
CREATE INDEX ...

-- Migrate existing captures
INSERT INTO graph_documents 
SELECT ... FROM captures;

COMMIT;
```

### Phase 2: Backfill Existing Data
```python
async def backfill_graph():
    """Process existing captures into graph"""
    captures = get_all_captures()
    for capture in captures:
        doc_id = await create_document_node(capture)
        await extract_and_link_entities(doc_id, capture.text)
        await classify_document(doc_id, capture.text)
```

---

## API Design

### Graph Endpoints
```python
@graph_router.get("/graph/document/{doc_id}")
async def get_document_graph(doc_id: str, depth: int = 1):
    """Get document with connected nodes"""
    
@graph_router.get("/graph/entity/{entity_id}/documents")
async def get_entity_documents(entity_id: str, limit: int = 20):
    """Get all documents mentioning entity"""
    
@graph_router.post("/graph/query")
async def execute_graph_query(query: GraphQuery):
    """Execute complex graph traversal"""
    
@graph_router.get("/graph/topics/tree")
async def get_topic_tree():
    """Get hierarchical topic structure"""
    
@graph_router.get("/graph/statistics")
async def get_graph_stats():
    """Node counts, edge counts, density, etc."""
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Node creation | <100ms | Time from capture to node |
| Entity extraction | <1s per doc | Processing time |
| Simple query | <200ms | API response time |
| Complex traversal | <2s | 3-hop queries |
| Storage overhead | <2x capture | Graph vs raw data |

---

## Open Questions

1. **Vector Embeddings**: Store in SQLite BLOB or separate vector DB?
2. **Entity Resolution**: How aggressive should deduplication be?
3. **Confidence Thresholds**: What minimum confidence for entity extraction?
4. **Graph Algorithms**: Implement PageRank, community detection?
5. **Real-time Updates**: Stream graph changes via WebSocket?

---

## Next Steps

1. [ ] Review and approve schema
2. [ ] Write migration SQL
3. [ ] Implement GraphService class
4. [ ] Build entity extractor
5. [ ] Create API endpoints
6. [ ] Write comprehensive tests
7. [ ] Document query patterns

---

*This proposal provides a concrete, implementable foundation for Milestone C's knowledge graph, building directly on B2's infrastructure.*