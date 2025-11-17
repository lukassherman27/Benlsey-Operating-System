-- Migration 013: AI Intelligence System
-- Date: 2025-11-16
-- Purpose: Add tables for AI-powered database intelligence and suggestion system

-- Main suggestions queue
CREATE TABLE IF NOT EXISTS ai_suggestions_queue (
  id TEXT PRIMARY KEY,
  project_code TEXT NOT NULL,
  suggestion_type TEXT NOT NULL,  -- 'status_mismatch', 'missing_pm', 'financial_risk', etc.
  proposed_fix TEXT NOT NULL,     -- JSON object with proposed changes
  evidence TEXT NOT NULL,         -- JSON object with detection evidence
  confidence REAL NOT NULL,       -- 0.0 to 1.0
  impact_type TEXT,               -- 'financial_risk', 'data_quality', 'operational', etc.
  impact_value_usd REAL,          -- Monetary impact if applicable
  impact_summary TEXT,            -- Human-readable impact description
  severity TEXT NOT NULL,         -- 'high', 'medium', 'low'
  bucket TEXT NOT NULL,           -- 'urgent', 'needs_attention', 'fyi'
  pattern_id TEXT,                -- Reference to suggestion_patterns
  pattern_label TEXT,             -- Human-readable pattern name
  auto_apply_candidate INTEGER DEFAULT 0,  -- Boolean: ready for auto-apply
  status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'snoozed', 'auto_applied'
  snooze_until DATETIME,          -- When to re-show if snoozed
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME,
  FOREIGN KEY (project_code) REFERENCES proposals(project_code) ON DELETE CASCADE
);

-- Pattern metadata and learning
CREATE TABLE IF NOT EXISTS suggestion_patterns (
  pattern_id TEXT PRIMARY KEY,
  label TEXT NOT NULL,            -- Human-readable pattern name
  detection_logic TEXT NOT NULL,  -- Description of how pattern is detected
  confidence_threshold REAL DEFAULT 0.7,  -- Minimum confidence for this pattern
  auto_apply_enabled INTEGER DEFAULT 0,    -- Boolean: auto-apply when threshold met
  approval_count INTEGER DEFAULT 0,        -- How many times users approved
  rejection_count INTEGER DEFAULT 0,       -- How many times users rejected
  total_suggestions INTEGER DEFAULT 0,     -- Total suggestions generated
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME
);

-- Decision log for training data and audit trail
CREATE TABLE IF NOT EXISTS suggestion_decisions (
  decision_id TEXT PRIMARY KEY,
  suggestion_id TEXT NOT NULL,
  project_code TEXT NOT NULL,
  suggestion_type TEXT NOT NULL,
  proposed_payload TEXT NOT NULL,  -- JSON: what was proposed
  evidence_snapshot TEXT NOT NULL, -- JSON: evidence at decision time
  confidence REAL NOT NULL,
  decision TEXT NOT NULL,          -- 'approved', 'rejected', 'snoozed'
  decision_by TEXT,                -- Username/email of decision maker
  decision_reason TEXT,            -- User's reason for reject/snooze
  applied INTEGER DEFAULT 0,       -- Boolean: was change actually applied
  decided_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (suggestion_id) REFERENCES ai_suggestions_queue(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_suggestions_status ON ai_suggestions_queue(status);
CREATE INDEX IF NOT EXISTS idx_suggestions_bucket ON ai_suggestions_queue(bucket);
CREATE INDEX IF NOT EXISTS idx_suggestions_pattern ON ai_suggestions_queue(pattern_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_project ON ai_suggestions_queue(project_code);
CREATE INDEX IF NOT EXISTS idx_suggestions_severity ON ai_suggestions_queue(severity);
CREATE INDEX IF NOT EXISTS idx_decisions_suggestion ON suggestion_decisions(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_decisions_project ON suggestion_decisions(project_code);
CREATE INDEX IF NOT EXISTS idx_decisions_date ON suggestion_decisions(decided_at);
CREATE INDEX IF NOT EXISTS idx_patterns_enabled ON suggestion_patterns(auto_apply_enabled);
