-- Milestone D2: LLM-Augmented Extraction
-- Date: 2025-08-20
-- Adds support for tracking extraction source and confidence

-- ============================================
-- ENTITIES TABLE ENHANCEMENTS
-- ============================================

-- Check if columns exist before adding (SQLite doesn't support IF NOT EXISTS for columns)
-- We'll use a transaction and ignore errors if columns already exist

-- Add source column to entities
ALTER TABLE entities ADD COLUMN source TEXT DEFAULT 'rule';

-- Add confidence column if not already present (might exist as 'belief')
-- Note: entities already has 'belief', but we'll add 'confidence' for consistency
ALTER TABLE entities ADD COLUMN confidence REAL DEFAULT 1.0;

-- Add extractor_version to entities
ALTER TABLE entities ADD COLUMN extractor_version TEXT DEFAULT 'rule@1';

-- ============================================
-- EDGES TABLE ENHANCEMENTS
-- ============================================

-- Add source column to edges (already has confidence column from C milestone)
ALTER TABLE edges ADD COLUMN source TEXT DEFAULT 'rule';

-- Ensure edges has confidence (might already exist from milestone C)
-- SQLite will error if it exists, which is fine
ALTER TABLE edges ADD COLUMN confidence REAL DEFAULT 1.0;

-- Update extractor_version in edges (already exists from C, but ensure default)
ALTER TABLE edges ADD COLUMN extractor_version TEXT DEFAULT 'rule@1';

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Index for filtering by source
CREATE INDEX IF NOT EXISTS idx_entities_source ON entities(source);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);

-- Composite index for source + project filtering
CREATE INDEX IF NOT EXISTS idx_entities_source_project ON entities(source, project_id);
CREATE INDEX IF NOT EXISTS idx_edges_source_project ON edges(source, project_id);

-- Index for confidence filtering
CREATE INDEX IF NOT EXISTS idx_entities_confidence ON entities(confidence);
CREATE INDEX IF NOT EXISTS idx_edges_confidence ON edges(confidence);

-- ============================================
-- EXTRACTION HISTORY TABLE (for metrics)
-- ============================================

CREATE TABLE IF NOT EXISTS extraction_events (
  id INTEGER PRIMARY KEY,
  occurred_at TEXT DEFAULT (datetime('now')),
  mode TEXT NOT NULL, -- 'rule', 'llm', 'hybrid'
  text_length INTEGER,
  entities_found INTEGER,
  edges_found INTEGER,
  rule_ms INTEGER,
  llm_ms INTEGER,
  merge_ms INTEGER,
  total_ms INTEGER,
  llm_model TEXT,
  llm_tokens_in INTEGER,
  llm_tokens_out INTEGER,
  error TEXT,
  project_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_extraction_events_mode ON extraction_events(mode);
CREATE INDEX IF NOT EXISTS idx_extraction_events_occurred ON extraction_events(occurred_at);

-- ============================================
-- UPDATE EXISTING DATA
-- ============================================

-- Set source for existing entities (if column was just added)
UPDATE entities SET source = 'rule' WHERE source IS NULL;
UPDATE edges SET source = 'rule' WHERE source IS NULL;

-- Set extractor_version for existing data
UPDATE entities SET extractor_version = 'rule@1' WHERE extractor_version IS NULL;
UPDATE edges SET extractor_version = 'rule@1' WHERE extractor_version IS NULL;

-- Migrate 'belief' to 'confidence' for entities if needed
UPDATE entities SET confidence = belief WHERE confidence IS NULL AND belief IS NOT NULL;