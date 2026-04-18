-- Milestone C: Knowledge Graph Implementation
-- Date: 2025-08-20

-- ============================================
-- DOCUMENT NODES (if not exists)
-- ============================================
CREATE TABLE IF NOT EXISTS document_nodes (
  id INTEGER PRIMARY KEY,
  project_id TEXT NOT NULL DEFAULT 'vader-lab',
  capture_id TEXT,
  title TEXT,
  url TEXT,
  content TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(capture_id) REFERENCES captures(id)
);

CREATE INDEX IF NOT EXISTS idx_doc_project ON document_nodes(project_id);
CREATE INDEX IF NOT EXISTS idx_doc_capture ON document_nodes(capture_id);

-- ============================================
-- ENTITIES TABLE (if not exists)
-- ============================================
CREATE TABLE IF NOT EXISTS entities (
  id INTEGER PRIMARY KEY,
  project_id TEXT NOT NULL DEFAULT 'vader-lab',
  type TEXT NOT NULL,
  name TEXT NOT NULL,
  normalized_name TEXT,
  belief REAL DEFAULT 0.7,
  entity_hash TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

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
-- EDGES TABLE (if not exists)
-- ============================================
CREATE TABLE IF NOT EXISTS edges (
  id INTEGER PRIMARY KEY,
  project_id TEXT NOT NULL DEFAULT 'vader-lab',
  src_id INTEGER NOT NULL,
  dst_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  props_json TEXT,
  confidence REAL,
  weight REAL,
  origin TEXT,  -- 'extractor'|'adapter'|'user'
  extractor_version TEXT,
  edge_hash TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_hash
  ON edges(edge_hash);

CREATE INDEX IF NOT EXISTS idx_edges_src
  ON edges(project_id, src_id, type);
  
CREATE INDEX IF NOT EXISTS idx_edges_dst
  ON edges(project_id, dst_id, type);

-- ============================================
-- TOPICS TABLE (if not exists)
-- ============================================
CREATE TABLE IF NOT EXISTS topics (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  parent_id INTEGER,
  description TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(parent_id) REFERENCES topics(id)
);

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
DROP TRIGGER IF EXISTS trg_doc_ai;
CREATE TRIGGER trg_doc_ai AFTER INSERT ON document_nodes BEGIN
  INSERT INTO doc_fts(rowid, content, title, url, document_id)
  VALUES (new.id, COALESCE(new.content,''), COALESCE(new.title,''), COALESCE(new.url,''), new.id);
END;

DROP TRIGGER IF EXISTS trg_doc_au;
CREATE TRIGGER trg_doc_au AFTER UPDATE OF content, title, url ON document_nodes BEGIN
  UPDATE doc_fts SET content=COALESCE(new.content,''), title=COALESCE(new.title,''), url=COALESCE(new.url,'')
  WHERE rowid=new.id;
END;

DROP TRIGGER IF EXISTS trg_doc_ad;
CREATE TRIGGER trg_doc_ad AFTER DELETE ON document_nodes BEGIN
  DELETE FROM doc_fts WHERE rowid=old.id;
END;

-- ============================================
-- FTS TRIGGERS: ENTITIES
-- ============================================
DROP TRIGGER IF EXISTS trg_ent_ai;
CREATE TRIGGER trg_ent_ai AFTER INSERT ON entities BEGIN
  INSERT INTO entity_fts(rowid, name, type, entity_id)
  VALUES (new.id, COALESCE(new.normalized_name, new.name, ''), COALESCE(new.type,''), new.id);
END;

DROP TRIGGER IF EXISTS trg_ent_au;
CREATE TRIGGER trg_ent_au AFTER UPDATE OF normalized_name, name, type ON entities BEGIN
  UPDATE entity_fts SET name=COALESCE(new.normalized_name, new.name, ''), type=COALESCE(new.type,'')
  WHERE rowid=new.id;
END;

DROP TRIGGER IF EXISTS trg_ent_ad;
CREATE TRIGGER trg_ent_ad AFTER DELETE ON entities BEGIN
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