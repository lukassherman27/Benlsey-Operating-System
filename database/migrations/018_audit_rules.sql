-- Migration 018: Audit Rules & Continuous Learning
-- Created: 2025-11-23
-- Description: Track business rules, validation logic, and continuous learning patterns
--              Enables intelligent automation and AI model improvement

-- ============================================================================
-- Business Rules
-- Store configurable business rules for validation and automation
-- ============================================================================
CREATE TABLE IF NOT EXISTS business_rules (
    rule_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name               TEXT UNIQUE NOT NULL,
    rule_type               TEXT NOT NULL,                      -- 'validation', 'calculation', 'classification', 'workflow', 'alert', 'recommendation'
    rule_category           TEXT,                               -- 'financial', 'scheduling', 'contract', 'quality', 'risk', 'compliance'
    description             TEXT NOT NULL,
    rule_logic              TEXT NOT NULL,                      -- JSON or SQL logic defining the rule
    rule_priority           INTEGER DEFAULT 5,                  -- 1=critical, 10=informational
    applies_to_table        TEXT,                               -- Which table this rule applies to
    applies_to_field        TEXT,                               -- Which field(s) this rule applies to
    trigger_condition       TEXT,                               -- When to execute this rule
    trigger_frequency       TEXT,                               -- 'on_insert', 'on_update', 'daily', 'weekly', 'monthly', 'on_demand'
    action_on_violation     TEXT,                               -- 'block', 'warn', 'log', 'notify', 'auto_correct'
    notification_recipients TEXT,                               -- JSON array of who to notify
    is_active               INTEGER DEFAULT 1,
    auto_apply              INTEGER DEFAULT 0,                  -- Apply rule automatically or require approval?
    confidence_threshold    REAL DEFAULT 0.8,                   -- Minimum confidence to auto-apply
    created_from_learning   INTEGER DEFAULT 0,                  -- Was this rule learned from data?
    learning_event_id       INTEGER,                            -- Reference to learning event
    execution_count         INTEGER DEFAULT 0,                  -- How many times has this been executed?
    success_count           INTEGER DEFAULT 0,                  -- How many times was it successful?
    failure_count           INTEGER DEFAULT 0,                  -- How many times did it fail?
    last_executed           DATETIME,
    created_by              TEXT DEFAULT 'system',
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (learning_event_id) REFERENCES learning_events(event_id) ON DELETE SET NULL
);

-- ============================================================================
-- Rule Executions
-- Track every execution of business rules for audit and improvement
-- ============================================================================
CREATE TABLE IF NOT EXISTS rule_executions (
    execution_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id                 INTEGER NOT NULL,
    execution_context       TEXT,                               -- What triggered this execution
    context_id              TEXT,                               -- ID of entity being evaluated
    input_data              TEXT,                               -- JSON of input data
    output_data             TEXT,                               -- JSON of output/result
    execution_result        TEXT,                               -- 'pass', 'fail', 'warn', 'blocked', 'corrected'
    confidence_score        REAL,                               -- Confidence in the result (0-1)
    execution_time_ms       INTEGER,                            -- How long it took
    error_message           TEXT,                               -- If failed, why?
    action_taken            TEXT,                               -- What action was taken
    requires_review         INTEGER DEFAULT 0,                  -- Flag for human review
    reviewed_by             TEXT,
    reviewed_at             DATETIME,
    review_outcome          TEXT,                               -- 'approved', 'rejected', 'modified'
    executed_at             DATETIME NOT NULL,
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id) ON DELETE CASCADE
);

-- ============================================================================
-- Data Quality Rules
-- Specific rules for data quality validation
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_quality_rules (
    dq_rule_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name              TEXT NOT NULL,
    column_name             TEXT NOT NULL,
    quality_check_type      TEXT NOT NULL,                      -- 'not_null', 'unique', 'range', 'format', 'reference_integrity', 'completeness', 'consistency', 'timeliness'
    check_logic             TEXT NOT NULL,                      -- SQL or JSON logic for validation
    expected_value          TEXT,                               -- Expected value or range
    tolerance_percentage    REAL,                               -- Acceptable deviation percentage
    severity                TEXT DEFAULT 'medium',              -- 'critical', 'high', 'medium', 'low'
    auto_fix                INTEGER DEFAULT 0,                  -- Can this be auto-fixed?
    fix_logic               TEXT,                               -- How to fix violations
    is_active               INTEGER DEFAULT 1,
    check_frequency         TEXT DEFAULT 'daily',               -- 'real_time', 'hourly', 'daily', 'weekly'
    last_check_date         DATETIME,
    last_violation_count    INTEGER,
    total_checks            INTEGER DEFAULT 0,
    total_violations        INTEGER DEFAULT 0,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(table_name, column_name, quality_check_type)
);

-- ============================================================================
-- Pattern Library
-- Store learned patterns for classification and prediction
-- ============================================================================
CREATE TABLE IF NOT EXISTS pattern_library (
    pattern_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name            TEXT UNIQUE NOT NULL,
    pattern_type            TEXT NOT NULL,                      -- 'email_classification', 'project_matching', 'fee_prediction', 'timeline_estimation', 'risk_detection'
    pattern_category        TEXT,                               -- Domain-specific category
    pattern_definition      TEXT NOT NULL,                      -- JSON defining the pattern
    pattern_indicators      TEXT,                               -- JSON array of indicators/features
    matching_logic          TEXT,                               -- How to match this pattern
    confidence_formula      TEXT,                               -- How to calculate confidence
    typical_confidence      REAL,                               -- Typical confidence score for this pattern
    application_count       INTEGER DEFAULT 0,                  -- How many times applied
    success_rate            REAL,                               -- Success rate (0-1)
    false_positive_rate     REAL,                               -- False positive rate
    last_accuracy_check     DATETIME,
    learned_from_samples    INTEGER,                            -- How many samples created this pattern
    requires_min_confidence REAL DEFAULT 0.7,                   -- Minimum confidence to use this pattern
    is_active               INTEGER DEFAULT 1,
    is_verified             INTEGER DEFAULT 0,                  -- Human-verified pattern?
    verified_by             TEXT,
    verified_at             DATETIME,
    superseded_by           INTEGER,                            -- Reference to newer pattern
    example_cases           TEXT,                               -- JSON array of example cases
    created_from_learning   INTEGER DEFAULT 0,
    learning_event_id       INTEGER,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (superseded_by) REFERENCES pattern_library(pattern_id) ON DELETE SET NULL,
    FOREIGN KEY (learning_event_id) REFERENCES learning_events(event_id) ON DELETE SET NULL
);

-- ============================================================================
-- Validation Exceptions
-- Track cases where validation rules were overridden
-- ============================================================================
CREATE TABLE IF NOT EXISTS validation_exceptions (
    exception_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id                 INTEGER,
    dq_rule_id              INTEGER,
    entity_type             TEXT NOT NULL,                      -- 'project', 'contract', 'payment', 'timeline'
    entity_id               TEXT NOT NULL,                      -- ID of the entity
    validation_failed       TEXT NOT NULL,                      -- What validation failed
    expected_value          TEXT,                               -- What was expected
    actual_value            TEXT,                               -- What was found
    exception_reason        TEXT NOT NULL,                      -- Why override was needed
    exception_type          TEXT,                               -- 'one_time', 'permanent', 'temporary', 'conditional'
    approved_by             TEXT NOT NULL,
    approved_at             DATETIME NOT NULL,
    expires_at              DATETIME,                           -- When this exception expires
    is_active               INTEGER DEFAULT 1,
    review_required         INTEGER DEFAULT 0,
    reviewed_by             TEXT,
    reviewed_at             DATETIME,
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id) ON DELETE SET NULL,
    FOREIGN KEY (dq_rule_id) REFERENCES data_quality_rules(dq_rule_id) ON DELETE SET NULL
);

-- ============================================================================
-- AI Model Performance
-- Track performance metrics of AI models and predictions
-- ============================================================================
CREATE TABLE IF NOT EXISTS ai_model_performance (
    performance_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name              TEXT NOT NULL,                      -- 'email_categorizer', 'project_matcher', 'scope_extractor', 'fee_predictor'
    model_version           TEXT,
    evaluation_type         TEXT NOT NULL,                      -- 'accuracy', 'precision', 'recall', 'f1_score', 'confidence_calibration'
    evaluation_metric       REAL NOT NULL,                      -- The actual metric value
    evaluation_date         DATE NOT NULL,
    sample_size             INTEGER,                            -- How many samples evaluated
    true_positives          INTEGER,
    true_negatives          INTEGER,
    false_positives         INTEGER,
    false_negatives         INTEGER,
    avg_confidence_correct  REAL,                               -- Average confidence when correct
    avg_confidence_incorrect REAL,                              -- Average confidence when incorrect
    confusion_matrix        TEXT,                               -- JSON of full confusion matrix
    performance_by_category TEXT,                               -- JSON breakdown by category
    compared_to_baseline    REAL,                               -- Improvement vs baseline
    dataset_description     TEXT,                               -- What dataset was used
    notes                   TEXT,
    evaluated_by            TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_business_rules_type
    ON business_rules(rule_type, is_active);

CREATE INDEX IF NOT EXISTS idx_business_rules_category
    ON business_rules(rule_category);

CREATE INDEX IF NOT EXISTS idx_business_rules_table
    ON business_rules(applies_to_table);

CREATE INDEX IF NOT EXISTS idx_rule_executions_rule
    ON rule_executions(rule_id, executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_rule_executions_result
    ON rule_executions(execution_result, requires_review);

CREATE INDEX IF NOT EXISTS idx_data_quality_rules_table
    ON data_quality_rules(table_name, is_active);

CREATE INDEX IF NOT EXISTS idx_data_quality_rules_severity
    ON data_quality_rules(severity, last_violation_count);

CREATE INDEX IF NOT EXISTS idx_pattern_library_type
    ON pattern_library(pattern_type, is_active);

CREATE INDEX IF NOT EXISTS idx_pattern_library_success
    ON pattern_library(success_rate DESC, application_count);

CREATE INDEX IF NOT EXISTS idx_validation_exceptions_entity
    ON validation_exceptions(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_validation_exceptions_active
    ON validation_exceptions(is_active, expires_at);

CREATE INDEX IF NOT EXISTS idx_ai_model_performance_model
    ON ai_model_performance(model_name, evaluation_date DESC);

-- ============================================================================
-- Triggers for auto-updating timestamps and counters
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_business_rules_timestamp
    AFTER UPDATE ON business_rules
BEGIN
    UPDATE business_rules SET updated_at = CURRENT_TIMESTAMP
    WHERE rule_id = NEW.rule_id;
END;

CREATE TRIGGER IF NOT EXISTS update_data_quality_rules_timestamp
    AFTER UPDATE ON data_quality_rules
BEGIN
    UPDATE data_quality_rules SET updated_at = CURRENT_TIMESTAMP
    WHERE dq_rule_id = NEW.dq_rule_id;
END;

CREATE TRIGGER IF NOT EXISTS update_pattern_library_timestamp
    AFTER UPDATE ON pattern_library
BEGIN
    UPDATE pattern_library SET updated_at = CURRENT_TIMESTAMP
    WHERE pattern_id = NEW.pattern_id;
END;

-- ============================================================================
-- Trigger to update rule execution counters
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_rule_execution_counters
    AFTER INSERT ON rule_executions
BEGIN
    UPDATE business_rules
    SET
        execution_count = execution_count + 1,
        success_count = success_count + CASE WHEN NEW.execution_result IN ('pass', 'corrected') THEN 1 ELSE 0 END,
        failure_count = failure_count + CASE WHEN NEW.execution_result IN ('fail', 'blocked') THEN 1 ELSE 0 END,
        last_executed = NEW.executed_at
    WHERE rule_id = NEW.rule_id;
END;

-- ============================================================================
-- Trigger to calculate pattern success rate
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS calculate_pattern_success_rate
    AFTER UPDATE ON pattern_library
    WHEN NEW.application_count > 0
BEGIN
    UPDATE pattern_library
    SET success_rate = CAST((NEW.application_count - (NEW.false_positive_rate * NEW.application_count)) AS REAL) / NEW.application_count
    WHERE pattern_id = NEW.pattern_id;
END;

-- ============================================================================
-- Trigger to expire validation exceptions
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS expire_validation_exceptions
    AFTER UPDATE ON validation_exceptions
    WHEN NEW.expires_at IS NOT NULL AND NEW.expires_at < datetime('now')
BEGIN
    UPDATE validation_exceptions
    SET is_active = 0
    WHERE exception_id = NEW.exception_id;
END;
