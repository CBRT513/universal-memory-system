-- Milestone D3: Firebase Domain Authorization Fix (Standalone)
-- Date: 2025-08-20
-- Creates necessary tables if they don't exist

-- ============================================
-- USER SESSIONS TABLE (CREATE IF NOT EXISTS)
-- ============================================

CREATE TABLE IF NOT EXISTS user_sessions (
  id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL,
  session_token TEXT UNIQUE NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  expires_at TEXT,
  is_active BOOLEAN DEFAULT 1,
  auth_source TEXT DEFAULT 'firebase',
  auth_domain TEXT,
  auth_metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);

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