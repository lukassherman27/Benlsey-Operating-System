# Database Intelligence System - UNIFIED PLAN ✅

**Status:** Ready for User Approval
**Coordinated By:** Claude (Backend) + Codex (Frontend)
**Date:** 2025-11-16
**Estimated Build Time:** 6-7 hours total

---

## 🎯 VISION

Build an AI-powered system that:
1. **Audits all 153 projects** in the database and detects issues
2. **Makes smart suggestions** with confidence scores (like "13 BK = 2013 = old project")
3. **Provides approval/reject workflow** via clean UI
4. **Logs all decisions** to training_data for future local LLM fine-tuning
5. **Learns patterns** and improves over time

---

## 🏗️ ARCHITECTURE OVERVIEW

### **"Ops Inbox" Approach** (Codex's UX Design)

**Primary View:** Single-column priority feed with three auto-buckets:
- **🔴 Urgent Fixes** - Financial risks, data corruption, critical issues
- **⚠️ Needs Attention** - Missing fields, status mismatches, follow-ups needed
- **📊 FYI / Insights** - Low-priority observations, optimizations

**Key Features:**
- Collapsible groups by pattern ("Legacy 2013 projects", "Missing PM assignments")
- Batch approval controls (approve multiple identical fixes at once)
- Evidence display per suggestion (root cause, signals, confidence)
- Auto-apply thresholds (>90% acceptance on 20+ samples)
- Training data logging (every decision logged for LLM fine-tuning)

---

## 📋 TECHNICAL SPECIFICATIONS

### **Backend (Claude Builds)**

#### 1. Pattern Detection Engine
```python
# Smart pattern detection with HIGH CONFIDENCE:
- Year-based status (98% confidence)
  → "13 BK-XXX" = 2013 project = likely completed/archived

- Invoice presence = active (95% confidence)
  → Has invoices in DB = NOT a proposal = must be active

- No contact 2+ years = dead (85% confidence)
  → No emails since 2022 = probably archived

- Fee mismatch detection (90% confidence)
  → Outstanding balance vs payment status discrepancies
```

#### 2. Three-Bucket Classification
```python
if financial_risk > 1M or data_corruption:
    bucket = "urgent"
elif missing_critical_field or status_mismatch:
    bucket = "needs_attention"
else:
    bucket = "fyi"
```

#### 3. Database Schema
```sql
-- Main suggestions queue
CREATE TABLE ai_suggestions_queue (
  id TEXT PRIMARY KEY,
  project_code TEXT,
  suggestion_type TEXT,
  proposed_fix JSON,
  evidence JSON,
  confidence REAL,
  impact_type TEXT,
  impact_value_usd REAL,
  impact_summary TEXT,      -- NEW: "Project marked complete but $1.2M unpaid"
  severity TEXT,
  bucket TEXT,
  pattern_id TEXT,
  pattern_label TEXT,
  auto_apply_candidate BOOLEAN DEFAULT 0,
  status TEXT DEFAULT 'pending',
  snooze_until DATETIME,
  created_at DATETIME
);

-- Pattern metadata
CREATE TABLE suggestion_patterns (
  pattern_id TEXT PRIMARY KEY,
  label TEXT,
  detection_logic TEXT,
  confidence_threshold REAL,
  auto_apply_enabled BOOLEAN DEFAULT 0,
  approval_count INT DEFAULT 0,
  rejection_count INT DEFAULT 0,
  created_at DATETIME
);

-- Decision log (training data)
CREATE TABLE suggestion_decisions (
  decision_id TEXT PRIMARY KEY,
  suggestion_id TEXT,
  project_code TEXT,
  suggestion_type TEXT,
  proposed_payload JSON,
  evidence_snapshot JSON,
  confidence REAL,
  decision TEXT,
  decision_by TEXT,
  decision_reason TEXT,
  applied BOOLEAN,
  decided_at DATETIME
);
```

#### 4. API Endpoints

**GET /api/intel/suggestions?status=pending&group=urgent**
```json
{
  "group": "urgent",
  "items": [
    {
      "id": "sgg_123",
      "project_code": "13 BK-024",
      "project_name": "Sandstone Villas",
      "is_active_project": 0,
      "suggestion_type": "status_mismatch",
      "proposed_fix": {"is_active_project": 0, "status": "archived"},
      "impact": {
        "type": "financial_risk",
        "value_usd": 1200000,
        "summary": "$1.2M outstanding - project marked complete but unpaid",
        "severity": "high"
      },
      "confidence": 0.82,
      "evidence": {
        "year": 2013,
        "invoices": 5,
        "last_contact": "2022-08-15",
        "signals": [
          "proposal_code: BK-013 → contact_date: 2013-04-12",
          "currently marked active_project = 1"
        ],
        "supporting_files": {
          "emails": [124, 156],
          "documents": [45]
        }
      },
      "pattern_id": "pattern_17",
      "pattern_label": "Legacy 2013 projects still marked active",
      "detection_logic": "Year extracted from code < 2020",
      "auto_apply_candidate": false,
      "created_at": "2025-11-16T02:30:00Z"
    }
  ]
}
```

**POST /api/intel/suggestions/{id}/decision**
```json
{
  "decision": "approved",
  "reason": "client confirmed closed",
  "apply_now": true,
  "dry_run": false,
  "batch_ids": ["sgg_124", "sgg_125"]
}

Response:
{
  "would_update": 12,
  "preview": [{...}],
  "conflicts": [],
  "applied": true,
  "training_logged": true
}
```

**GET /api/intel/patterns**
```json
{
  "patterns": [
    {
      "pattern_id": "pattern_17",
      "label": "Legacy 2013 projects still marked active",
      "count": 12,
      "impact_total_usd": 6200000,
      "confidence_avg": 0.89,
      "sample_projects": ["13 BK-024", "13 BK-017", "13 BK-042"],
      "detection_logic": "Year extracted from code < 2020",
      "approval_rate": 0.95
    }
  ]
}
```

**GET /api/intel/decisions?limit=50**
```json
{
  "decisions": [
    {
      "decision_id": "dec_456",
      "suggestion_id": "sgg_123",
      "project_code": "13 BK-024",
      "decision": "approved",
      "decided_at": "2025-11-16T03:00:00Z",
      "applied": true
    }
  ],
  "export_ndjson_url": "/api/intel/training-data?format=ndjson"
}
```

---

### **Frontend (Codex Builds)**

#### 1. Ops Inbox UI
```
┌─────────────────────────────────────────────────┐
│ Database Intelligence                           │
│ 47 suggestions • $6.2M affected                 │
├─────────────────────────────────────────────────┤
│                                                  │
│ 🔴 URGENT FIXES (5)                             │
│   ▶ Legacy 2013 projects (12 items)             │
│   ▶ Financial risk - unpaid invoices (3 items)  │
│                                                  │
│ ⚠️ NEEDS ATTENTION (28)                         │
│   ▶ Missing PM assignments (15 items)           │
│   ▶ Status mismatches (13 items)                │
│                                                  │
│ 📊 FYI / INSIGHTS (14)                          │
│   ▶ Contact importance updates (8 items)        │
│   ▶ Project phase suggestions (6 items)         │
│                                                  │
└─────────────────────────────────────────────────┘
```

#### 2. Suggestion Card (Expanded)
```
┌─────────────────────────────────────────────────┐
│ 13 BK-024 • Sandstone Villas                    │
│ [PROPOSAL badge]                                 │
│                                                  │
│ Suggested Change: Mark as ARCHIVED               │
│ Confidence: 82%                                  │
│ Impact: Financial risk • $1.2M outstanding       │
│                                                  │
│ Root Cause:                                      │
│ "2013 project still marked active but no        │
│  contact since 2022"                            │
│                                                  │
│ Signals:                                         │
│   • proposal_code: BK-013 → year: 2013          │
│   • currently marked active_project = 1          │
│   • last_contact: 2022-08-15 (2+ years ago)     │
│                                                  │
│ Supporting Files:                                │
│   2 linked emails, 1 PDF                        │
│                                                  │
│ [▼ How this was detected]  (disclosure)         │
│                                                  │
│ ┌───────────────────────────────────┐           │
│ │ [✓ Accept]  [Preview]  [Snooze]  │           │
│ └───────────────────────────────────┘           │
└─────────────────────────────────────────────────┘
```

#### 3. Batch Controls
```
┌─────────────────────────────────────────────────┐
│ 12 selected                                      │
│ [Approve All]  [Reject All]  [Preview Impact]   │
└─────────────────────────────────────────────────┘
```

#### 4. Auto-Apply Toggle (Only shows when threshold met)
```
┌─────────────────────────────────────────────────┐
│ Pattern: "Legacy 2013 projects"                  │
│ Approval rate: 95% across 24 samples             │
│                                                  │
│ ☐ Always auto-apply this pattern                │
│   (Changes will be logged for audit)             │
└─────────────────────────────────────────────────┘
```

---

## 📊 KEY FEATURES AGREED UPON

### ✅ Codex's Decisions (UX)
1. **Inline Pattern Groups** - No separate "Pattern Board" tab (keeps it simple)
2. **Auto-Apply Toggle** - Only show when ≥90% accuracy + sample threshold met
3. **Snooze Behavior** - Re-run automatically next audit; re-open early if data changes
4. **Evidence Detail** - Keep simple, hide `detection_logic` behind disclosure
5. **Dry Run Mode** - Include `dry_run=1` query param for "Preview Impact" button

### ✅ Claude's Technical Additions
1. **Impact Summary** - Human-readable context per suggestion
2. **Severity Levels** - high/medium/low for better prioritization
3. **Pattern Samples** - Show 3-5 example projects per pattern
4. **Training Export** - ndjson format for LLM fine-tuning
5. **Conflict Detection** - Warn about issues before applying

---

## 🚀 BUILD PHASES

### **Phase 1: Backend Foundation (2-3 hours) - Claude**
- Build `ai_database_auditor.py` with pattern detection
- Create database tables (ai_suggestions_queue, suggestion_patterns, suggestion_decisions)
- Populate suggestions queue from 153 projects audit
- Implement confidence scoring system
- Test pattern detection accuracy

**Deliverable:** 150+ suggestions generated with evidence and confidence scores

---

### **Phase 2: API Endpoints (1-2 hours) - Claude**
- Build GET /api/intel/suggestions (with bucket filtering)
- Build POST /api/intel/suggestions/{id}/decision (with dry_run support)
- Build GET /api/intel/patterns
- Build GET /api/intel/decisions
- Test all endpoints with real data

**Deliverable:** 4 API endpoints live and documented

---

### **Phase 3: Frontend UI (2-3 hours) - Codex**
- Build Ops Inbox layout with three-bucket grouping
- Create suggestion cards with evidence display
- Implement batch controls and multi-select
- Wire to Claude's API endpoints
- Add "Preview Impact" (dry_run mode)
- Build auto-apply toggle UI

**Deliverable:** Full suggestion review interface

---

### **Phase 4: Integration & Testing (1 hour) - Both**
- Test end-to-end approval workflow
- Verify training data logging to ndjson
- Test batch operations
- Verify auto-apply thresholds
- Fix any issues
- Document system

**Deliverable:** Complete working system ready for production use

---

## 📈 EXPECTED OUTCOMES

### Immediate Benefits:
- **Database cleanup in 10-15 minutes** (not hours of manual review)
- **High-confidence suggestions** (90%+ accuracy on year-based, invoice detection)
- **Batch operations** reduce 150 suggestions to ~10-15 pattern decisions
- **Training data collection** starts immediately (every decision logged)

### Long-term Benefits:
- **Auto-apply patterns** once threshold met (reduces future manual work)
- **Local LLM training dataset** builds up over time
- **Pattern learning** improves confidence scores
- **Audit trail** for all database changes

---

## 🔒 SAFETY FEATURES

1. **Dry Run Mode** - Preview changes before applying
2. **Batch Preview** - See how many records affected
3. **Conflict Detection** - Warn about issues before committing
4. **Audit Trail** - Every change logged with reasoning
5. **Snooze Option** - Delay suggestions without rejecting
6. **Manual Override** - User can reject high-confidence suggestions

---

## 📦 TRAINING DATA EXPORT

**Format:** Newline-delimited JSON (ndjson)

**Sample Export:**
```json
{"task_type":"status_classification","input":{"project_code":"13 BK-024","evidence":{"year":2013,"invoices":5}},"output":{"status":"archived"},"confidence":0.82,"human_verified":1,"decision":"approved","decided_at":"2025-11-16T03:00:00Z"}
{"task_type":"status_classification","input":{"project_code":"25 BK-099","evidence":{"year":2025,"invoices":0}},"output":{"status":"proposal"},"confidence":0.95,"human_verified":1,"decision":"approved","decided_at":"2025-11-16T03:05:00Z"}
```

**Use Cases:**
- Fine-tune local LLM (Llama, Mistral, etc.)
- Improve confidence scoring
- Detect user preferences and patterns
- Export for analysis/reporting

---

## 🎯 SUCCESS CRITERIA

**This system is successful if:**
- ✅ User reviews 150+ suggestions in 10-15 minutes
- ✅ AI confidence >90% on year-based and invoice detection
- ✅ Batch operations reduce clicks by 80%+
- ✅ Training data collection produces 500+ labeled examples
- ✅ Auto-apply works safely without errors
- ✅ Database accuracy improves from ~60% to 95%+

---

## 📝 NEXT STEPS

1. **User approval** of this plan
2. **Claude starts Phase 1** (backend foundation)
3. **Codex starts Phase 3** (can start with mock data in parallel)
4. **Integration** once both ready
5. **User testing** and iteration

---

## ⏱️ TIMELINE ESTIMATE

**Total Build Time:** 6-7 hours
- Claude: 4-5 hours (backend + APIs)
- Codex: 2-3 hours (frontend UI)
- Integration: 1 hour (together)

**Can complete in 1-2 days** depending on availability.

---

## ✅ APPROVAL NEEDED

**User (Lukas/Bill):** Please approve this plan so we can start building!

**Questions before we start?**
- Any concerns about the approach?
- Want to adjust any features?
- Different priorities?

**Once approved, we'll start building immediately!** 🚀
