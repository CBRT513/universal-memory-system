-- Milestone D3: Firebase Domain Authorization Fix
-- Date: 2025-08-20
-- Adds auth_source tracking to user sessions

-- ============================================
-- USER SESSIONS TABLE ENHANCEMENT
-- ============================================

-- Add auth_source column to track authentication method
ALTER TABLE user_sessions ADD COLUMN auth_source TEXT DEFAULT 'firebase';

-- Add domain column to track which domain was used for auth
ALTER TABLE user_sessions ADD COLUMN auth_domain TEXT;

-- Add auth metadata column for additional auth info
ALTER TABLE user_sessions ADD COLUMN auth_metadata TEXT;

-- ============================================
-- AUTH EVENTS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS auth_events (
  id INTEGER PRIMARY KEY,
  occurred_at TEXT DEFAULT (datetime('now')),
  event_type TEXT NOT NULL, -- 'login', 'logout', 'domain_blocked', 'auth_error'
  user_id TEXT,
  domain TEXT,
  auth_source TEXT, -- 'firebase', 'sso', 'local'
  success BOOLEAN,
  error_code TEXT,
  error_message TEXT,
  ip_address TEXT,
  user_agent TEXT,
  metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_auth_events_user ON auth_events(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_events_domain ON auth_events(domain);
CREATE INDEX IF NOT EXISTS idx_auth_events_type ON auth_events(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_events_occurred ON auth_events(occurred_at);

-- ============================================
-- AUTHORIZED DOMAINS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS authorized_domains (
  id INTEGER PRIMARY KEY,
  domain TEXT UNIQUE NOT NULL,
  added_at TEXT DEFAULT (datetime('now')),
  added_by TEXT,
  is_active BOOLEAN DEFAULT 1,
  environment TEXT DEFAULT 'all', -- 'dev', 'staging', 'prod', 'all'
  notes TEXT
);

-- Insert default authorized domains
INSERT OR IGNORE INTO authorized_domains (domain, added_by, notes) VALUES
  ('sso.test', 'system', 'SSO test domain'),
  ('cbrt-ui.test', 'system', 'CBRT UI test domain'),
  ('localhost', 'system', 'Local development'),
  ('127.0.0.1', 'system', 'Local development IP'),
  ('barge2rail.com', 'system', 'Production domain'),
  ('cbrt.com', 'system', 'CBRT production domain');

-- ============================================
-- AUTH METRICS VIEW
-- ============================================

CREATE VIEW IF NOT EXISTS auth_metrics AS
SELECT 
  domain,
  auth_source,
  COUNT(*) as total_attempts,
  SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_logins,
  SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_attempts,
  COUNT(DISTINCT user_id) as unique_users,
  MAX(occurred_at) as last_activity
FROM auth_events
WHERE event_type IN ('login', 'domain_blocked')
GROUP BY domain, auth_source;

-- ============================================
-- UPDATE EXISTING DATA
-- ============================================

-- Set auth_source for existing sessions
UPDATE user_sessions 
SET auth_source = 'firebase' 
WHERE auth_source IS NULL;

-- ============================================
-- TRIGGERS FOR AUDIT
-- ============================================

-- Trigger to log domain authorization checks
CREATE TRIGGER IF NOT EXISTS trg_log_auth_domain_check
AFTER INSERT ON auth_events
WHEN NEW.event_type = 'domain_blocked'
BEGIN
  INSERT INTO graph_integrity_events (kind, details_json)
  VALUES (
    'unauthorized_domain_attempt',
    json_object(
      'domain', NEW.domain,
      'timestamp', NEW.occurred_at,
      'error_code', NEW.error_code
    )
  );
END;