-- Migration 007: Context-aware proposal health tracking
-- Adds fields for intelligent health monitoring with context

-- Add timeline and context tracking
ALTER TABLE proposals ADD COLUMN expected_delay_days INTEGER;
ALTER TABLE proposals ADD COLUMN delay_reason TEXT;
ALTER TABLE proposals ADD COLUMN delay_until_date TEXT;

-- Add project phase tracking
ALTER TABLE proposals ADD COLUMN project_phase TEXT DEFAULT 'early_exploration';
-- Values: 'early_exploration', 'active_negotiation', 'contract_pending', 'on_hold'

-- Add client behavior patterns
ALTER TABLE proposals ADD COLUMN client_response_pattern TEXT DEFAULT 'unknown';
-- Values: 'fast', 'normal', 'slow', 'unknown'

-- Add urgency tracking
ALTER TABLE proposals ADD COLUMN urgency_level TEXT DEFAULT 'normal';
-- Values: 'urgent', 'normal', 'flexible'

-- Add hold status
ALTER TABLE proposals ADD COLUMN on_hold INTEGER DEFAULT 0;
ALTER TABLE proposals ADD COLUMN on_hold_reason TEXT;
ALTER TABLE proposals ADD COLUMN on_hold_until TEXT;

-- Add last contact tracking
ALTER TABLE proposals ADD COLUMN last_contact_date TEXT;
ALTER TABLE proposals ADD COLUMN days_since_contact INTEGER;

-- Add health metrics
ALTER TABLE proposals ADD COLUMN health_score REAL;
ALTER TABLE proposals ADD COLUMN win_probability REAL;
ALTER TABLE proposals ADD COLUMN last_sentiment TEXT;
-- Values: 'positive', 'neutral', 'concerned', 'negative'

-- Add notes and context
ALTER TABLE proposals ADD COLUMN internal_notes TEXT;
ALTER TABLE proposals ADD COLUMN next_action TEXT;
ALTER TABLE proposals ADD COLUMN next_action_date TEXT;
