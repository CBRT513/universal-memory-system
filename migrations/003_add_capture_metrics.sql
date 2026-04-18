-- Migration: Add capture metrics table
-- Date: 2025-08-19
-- Purpose: Track capture performance and success metrics for B2

-- Create capture_metrics table
CREATE TABLE IF NOT EXISTS capture_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date TEXT NOT NULL,  -- YYYY-MM-DD for daily aggregation
    hour INTEGER NOT NULL,  -- 0-23 for hourly stats
    
    -- Counts
    total_attempts INTEGER DEFAULT 0,
    successful_captures INTEGER DEFAULT 0,
    cached_hits INTEGER DEFAULT 0,
    failed_captures INTEGER DEFAULT 0,
    
    -- Failure breakdown
    blocked_count INTEGER DEFAULT 0,  -- 403/401/429
    not_found_count INTEGER DEFAULT 0,  -- 404
    server_error_count INTEGER DEFAULT 0,  -- 5xx
    timeout_count INTEGER DEFAULT 0,
    invalid_url_count INTEGER DEFAULT 0,
    
    -- Performance metrics (milliseconds)
    avg_fetch_time_ms REAL,
    p50_fetch_time_ms REAL,
    p95_fetch_time_ms REAL,
    p99_fetch_time_ms REAL,
    avg_total_time_ms REAL,
    p50_total_time_ms REAL,
    p95_total_time_ms REAL,
    p99_total_time_ms REAL,
    
    -- Domain stats (JSON)
    top_domains TEXT,  -- JSON array of {domain, count}
    top_failures TEXT,  -- JSON array of {domain, count, cause}
    
    -- Extraction methods used
    adapter_uses INTEGER DEFAULT 0,
    readability_uses INTEGER DEFAULT 0,
    client_captures INTEGER DEFAULT 0,
    
    UNIQUE(date, hour)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_capture_metrics_date ON capture_metrics(date);
CREATE INDEX IF NOT EXISTS idx_capture_metrics_timestamp ON capture_metrics(timestamp);

-- Create capture_events table for raw event tracking
CREATE TABLE IF NOT EXISTS capture_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    job_id TEXT NOT NULL,
    capture_id TEXT,
    url TEXT,
    domain TEXT,
    http_status INTEGER,
    cause TEXT,  -- ok, blocked, not_found, server_error, timeout, invalid
    cached BOOLEAN DEFAULT 0,
    fetch_time_ms INTEGER,
    total_time_ms INTEGER,
    extraction_method TEXT,  -- adapter name or 'readability_fallback'
    user_agent TEXT,
    project TEXT
);

-- Create index for event queries
CREATE INDEX IF NOT EXISTS idx_capture_events_timestamp ON capture_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_capture_events_domain ON capture_events(domain);
CREATE INDEX IF NOT EXISTS idx_capture_events_cause ON capture_events(cause);