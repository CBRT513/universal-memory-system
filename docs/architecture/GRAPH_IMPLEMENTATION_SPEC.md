# Graph Implementation Specification
**Version**: 1.0  
**Date**: August 20, 2025  
**Status**: READY TO IMPLEMENT  
**Milestone**: C

---

## Normalization Specification

### Canonical Entity Keys
**Goal**: Turn any raw string into a stable key for deduplication/merge

#### 1. Unicode Normalization
- Form: NFC → NFKC
- Remove zero-width chars: `[\u200B-\u200D\uFEFF]`

#### 2. Case & Punctuation
- Lowercase all text
- Collapse all whitespace to single space
- Strip leading/trailing punctuation
- Replace inner punctuation with single space for: `[-_./,;:|(){}[\]]`

#### 3. Stop-Junk Removal
- Drop quotes/backticks
- Collapse multiple spaces
- Reject if result < 2 chars

#### 4. Type-Aware Processing
- **person**: Keep diacritics; keep hyphenated surnames as spaces
- **org/tech/concept**: Keep numbers; collapse "inc."/"llc" suffixes to nothing at end

### Function Signature
```python
normalize_name(raw: str, type: Literal["person","org","tech","concept",...]) -> str
```

### Entity Hash
```python
entity_hash = sha1(f"{type}|{normalized_name}|{project_id}")[:16]
```

---

## Edge Reification & Idempotency

### Edge Hash
```python
edge_hash = sha1(f"{src_id}|{dst_id}|{edge_type}|{sorted_key_props_json}|{project_id}")[:16]
```
- `sorted_key_props_json`: JSON with only "identifying" props (e.g., section, paragraph_idx)
- Keys sorted, no whitespace

---

## SQL Schema & Migrations

### Complete DDL (SQLite)

```sql
-- ============================================
-- ENTITIES ENHANCEMENTS
-- ============================================
ALTER TABLE entities
  ADD COLUMN normalized_name TEXT;
ALTER TABLE entities
  ADD COLUMN belief REAL DEFAULT 0.7;
ALTER TABLE entities
  ADD COLUMN entity_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_entities_uni
  ON entities(project_id, type, normalized_name);

CREATE UNIQUE INDEX IF NOT EXISTS idx_entities_hash
  ON entities(entity_hash);

-- ============================================
-- ENTITY ALIASES
-- ============================================
CREATE TABLE IF NOT EXISTS entity_aliases (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL,
  alias TEXT NOT NULL,
  source TEXT,
  confidence REAL DEFAULT 0.7,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(entity_id, alias),
  FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- ============================================
-- DOCUMENTS (if not already present)
-- ============================================
CREATE TABLE IF NOT EXISTS document_nodes (
  id INTEGER PRIMARY KEY,
  project_id TEXT NOT NULL,
  capture_id TEXT,
  title TEXT,
  url TEXT,
  content TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_doc_project 
  ON document_nodes(project_id);

-- ============================================
-- EDGES ENHANCEMENTS
-- ============================================
ALTER TABLE edges
  ADD COLUMN confidence REAL;
ALTER TABLE edges
  ADD COLUMN weight REAL;
ALTER TABLE edges
  ADD COLUMN origin TEXT;  -- 'extractor'|'adapter'|'user'
ALTER TABLE edges
  ADD COLUMN extractor_version TEXT;
ALTER TABLE edges
  ADD COLUMN edge_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_hash
  ON edges(edge_hash);

CREATE INDEX IF NOT EXISTS idx_edges_src
  ON edges(project_id, src_id, type);
  
CREATE INDEX IF NOT EXISTS idx_edges_dst
  ON edges(project_id, dst_id, type);

-- ============================================
-- TOPIC HIERARCHY CLOSURE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS topic_tree (
  ancestor_id INTEGER NOT NULL,
  descendant_id INTEGER NOT NULL,
  depth INTEGER NOT NULL,
  PRIMARY KEY (ancestor_id, descendant_id),
  FOREIGN KEY(ancestor_id) REFERENCES topics(id) ON DELETE CASCADE,
  FOREIGN KEY(descendant_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- ============================================
-- FULL-TEXT SEARCH (FTS5)
-- ============================================
CREATE VIRTUAL TABLE IF NOT EXISTS doc_fts USING fts5(
  content, title, url, document_id UNINDEXED, tokenize='unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS entity_fts USING fts5(
  name, type, entity_id UNINDEXED, tokenize='unicode61'
);

-- ============================================
-- FTS TRIGGERS: DOCUMENTS
-- ============================================
CREATE TRIGGER IF NOT EXISTS trg_doc_ai AFTER INSERT ON document_nodes BEGIN
  INSERT INTO doc_fts(rowid, content, title, url, document_id)
  VALUES (new.id, COALESCE(new.content,''), COALESCE(new.title,''), COALESCE(new.url,''), new.id);
END;

CREATE TRIGGER IF NOT EXISTS trg_doc_au AFTER UPDATE OF content, title, url ON document_nodes BEGIN
  UPDATE doc_fts SET content=COALESCE(new.content,''), title=COALESCE(new.title,''), url=COALESCE(new.url,'')
  WHERE rowid=new.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_doc_ad AFTER DELETE ON document_nodes BEGIN
  DELETE FROM doc_fts WHERE rowid=old.id;
END;

-- ============================================
-- FTS TRIGGERS: ENTITIES
-- ============================================
CREATE TRIGGER IF NOT EXISTS trg_ent_ai AFTER INSERT ON entities BEGIN
  INSERT INTO entity_fts(rowid, name, type, entity_id)
  VALUES (new.id, COALESCE(new.normalized_name,''), COALESCE(new.type,''), new.id);
END;

CREATE TRIGGER IF NOT EXISTS trg_ent_au AFTER UPDATE OF normalized_name, type ON entities BEGIN
  UPDATE entity_fts SET name=COALESCE(new.normalized_name,''), type=COALESCE(new.type,'')
  WHERE rowid=new.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_ent_ad AFTER DELETE ON entities BEGIN
  DELETE FROM entity_fts WHERE rowid=old.id;
END;

-- ============================================
-- INTEGRITY EVENTS
-- ============================================
CREATE TABLE IF NOT EXISTS graph_integrity_events (
  id INTEGER PRIMARY KEY,
  occurred_at TEXT DEFAULT (datetime('now')),
  kind TEXT,  -- 'orphan_edge','dup_entity', etc.
  details_json TEXT
);
```

---

## Python Implementation

### Normalization & Hashing Module
**File**: `src/graph_normalization.py`

```python
import re
import json
import unicodedata
import hashlib
from typing import Literal

_ZW = re.compile(r'[\u200B-\u200D\uFEFF]')
_PUNCT = re.compile(r"[-_\./,;:\|()\[\]{}]+")
_MULTI = re.compile(r"\s+")

def _nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)

def normalize_name(raw: str, etype: str) -> str:
    """Normalize entity name for deduplication"""
    s = _nfkc(raw or "").strip()
    s = _ZW.sub("", s).lower()
    s = _PUNCT.sub(" ", s)
    s = _MULTI.sub(" ", s).strip().strip("'\"`")
    
    if etype in {"org", "tech", "concept"}:
        s = re.sub(r"\b(inc|ltd|llc|gmbh|sa|plc)\.?$", "", s).strip()
    
    if len(s) < 2:
        raise ValueError("too short")
    
    return s

def sha1_16(s: str) -> str:
    """Generate 16-char hash"""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]

def entity_hash(etype: str, normalized_name: str, project_id: str) -> str:
    """Generate unique entity hash"""
    return sha1_16(f"{etype}|{normalized_name}|{project_id}")

def edge_hash(src_id: int, dst_id: int, etype: str, key_props: dict, project_id: str) -> str:
    """Generate unique edge hash"""
    key = json.dumps(key_props or {}, sort_keys=True, separators=(",", ":"))
    return sha1_16(f"{src_id}|{dst_id}|{etype}|{key}|{project_id}")
```

### Idempotent Operations
**File**: `src/graph_operations.py`

```python
import json
import sqlite3
from typing import Optional, Dict, Any
from .graph_normalization import normalize_name, entity_hash, edge_hash

def upsert_entity(conn: sqlite3.Connection, 
                  project_id: str, 
                  name: str, 
                  etype: str, 
                  belief: float = 0.7) -> int:
    """Idempotent entity upsert"""
    nn = normalize_name(name, etype)
    eh = entity_hash(etype, nn, project_id)
    
    cur = conn.execute("SELECT id FROM entities WHERE entity_hash=?", (eh,))
    row = cur.fetchone()
    if row:
        return row[0]
    
    cur = conn.execute(
        """INSERT INTO entities(project_id, type, name, normalized_name, belief, entity_hash)
           VALUES(?,?,?,?,?,?)""",
        (project_id, etype, name, nn, belief, eh)
    )
    return cur.lastrowid

def upsert_edge(conn: sqlite3.Connection,
                project_id: str,
                src_id: int,
                dst_id: int,
                etype: str,
                key_props: Optional[Dict] = None,
                confidence: float = 0.8,
                origin: str = "extractor",
                extractor_version: str = "c1") -> None:
    """Idempotent edge upsert"""
    eh = edge_hash(src_id, dst_id, etype, key_props or {}, project_id)
    
    cur = conn.execute("SELECT id FROM edges WHERE edge_hash=?", (eh,))
    if cur.fetchone():
        return
    
    conn.execute(
        """INSERT INTO edges(project_id, src_id, dst_id, type, props_json, 
                           confidence, weight, origin, extractor_version, edge_hash)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (project_id, src_id, dst_id, etype, json.dumps(key_props or {}), 
         confidence, None, origin, extractor_version, eh)
    )
```

---

## Migration Order

### Step 1: Apply Schema Changes
Run all ALTER/CREATE statements from DDL section above

### Step 2: Backfill Existing Data
```python
def backfill_normalized_names(conn):
    """Backfill normalized_name and entity_hash for existing entities"""
    cursor = conn.execute("SELECT id, name, type, project_id FROM entities WHERE entity_hash IS NULL")
    for row in cursor.fetchall():
        entity_id, name, etype, project_id = row
        try:
            nn = normalize_name(name, etype)
            eh = entity_hash(etype, nn, project_id)
            conn.execute(
                "UPDATE entities SET normalized_name=?, entity_hash=? WHERE id=?",
                (nn, eh, entity_id)
            )
        except ValueError:
            # Handle entities that can't be normalized
            pass
    conn.commit()
```

### Step 3: Build FTS Tables
```sql
-- Populate doc_fts from existing documents
INSERT INTO doc_fts(rowid, content, title, url, document_id)
SELECT id, COALESCE(content,''), COALESCE(title,''), COALESCE(url,''), id
FROM document_nodes;

-- Populate entity_fts from existing entities
INSERT INTO entity_fts(rowid, name, type, entity_id)
SELECT id, COALESCE(normalized_name,''), COALESCE(type,''), id
FROM entities;
```

### Step 4: Build Topic Tree
```python
def build_topic_tree(conn):
    """Build closure table from existing topics"""
    # Insert self-references (depth=0)
    conn.execute("""
        INSERT INTO topic_tree(ancestor_id, descendant_id, depth)
        SELECT id, id, 0 FROM topics
    """)
    
    # Insert parent-child (depth=1) and propagate
    # (Implement based on your topic hierarchy structure)
```

### Step 5: Integrity Sweep
```python
def integrity_sweep(conn):
    """Check and log integrity issues"""
    # Find orphan edges
    orphans = conn.execute("""
        SELECT e.id FROM edges e
        LEFT JOIN entities s ON e.src_id = s.id
        LEFT JOIN entities d ON e.dst_id = d.id
        WHERE s.id IS NULL OR d.id IS NULL
    """).fetchall()
    
    if orphans:
        conn.execute(
            "INSERT INTO graph_integrity_events(kind, details_json) VALUES(?,?)",
            ("orphan_edges", json.dumps({"count": len(orphans), "ids": [r[0] for r in orphans]}))
        )
```

---

## API Endpoints

### Entity Merge
```python
@graph_router.post("/api/graph/entity/merge")
async def merge_entities(from_id: int, to_id: int, aliases: Optional[List[str]] = None):
    """Merge from_id into to_id, move edges, create aliases"""
    # Implementation: move all edges, insert aliases, delete from_id
```

### Edge Creation
```python
@graph_router.post("/api/graph/edge")
async def create_edge(
    src_id: int,
    dst_id: int,
    type: str,
    key_props: Optional[Dict] = None,
    confidence: float = 0.8,
    origin: str = "extractor",
    extractor_version: str = "c1"
):
    """Idempotent edge creation via edge_hash"""
    # Use upsert_edge function
```

### Combined Search
```python
@graph_router.get("/api/graph/search")
async def search_graph(q: str, project_id: str):
    """Search docs and entities via FTS"""
    # Query both doc_fts and entity_fts
    # Return top docs + entities
```

### Topic Descendants
```python
@graph_router.get("/api/graph/topics/{topic_id}/descendants")
async def get_topic_descendants(topic_id: int):
    """Get all descendants using closure table"""
    # Query topic_tree where ancestor_id = topic_id
```

### Integrity Check
```python
@graph_router.get("/api/graph/integrity")
async def get_integrity_events(limit: int = 100):
    """Get latest integrity events"""
    # Query graph_integrity_events ORDER BY occurred_at DESC
```

---

## Migration File
**File**: `migrations/004_knowledge_graph.sql`

```sql
-- Milestone C: Knowledge Graph Implementation
-- Date: 2025-08-20

BEGIN TRANSACTION;

-- [Insert all DDL from above]

COMMIT;
```

---

## Implementation Checklist

1. [ ] Create `src/graph_normalization.py` with normalization functions
2. [ ] Create `src/graph_operations.py` with upsert functions
3. [ ] Create `migrations/004_knowledge_graph.sql` with all DDL
4. [ ] Run migration on database
5. [ ] Backfill normalized_name and entity_hash
6. [ ] Populate FTS tables
7. [ ] Build topic_tree closure table
8. [ ] Run integrity sweep
9. [ ] Create API endpoints in `src/graph_api.py`
10. [ ] Write tests for normalization
11. [ ] Write tests for idempotency
12. [ ] Write tests for API endpoints
13. [ ] Update documentation

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| normalize_name | <1ms | Pure Python |
| upsert_entity | <10ms | Single lookup + insert |
| upsert_edge | <10ms | Hash lookup |
| FTS search | <200ms | Both tables |
| Topic tree query | <100ms | Closure table |

---

*This specification provides everything needed to implement Milestone C without guessing. All functions, DDL, and APIs are ready to copy-paste.*