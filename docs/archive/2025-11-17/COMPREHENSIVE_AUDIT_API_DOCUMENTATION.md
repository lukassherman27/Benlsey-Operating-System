# Comprehensive Audit System - API Documentation for Codex

**Backend Status:** ✅ COMPLETE (Phase 2A-2D)
**Frontend Status:** ⏳ PENDING (Phase 2E - Codex to implement)

---

## 🎯 What Was Built

The Comprehensive Audit System (Phase 2) extends the basic intelligence system with:

1. **Database Schema** - 6 new tables for tracking scope, fees, timelines, contracts, learning, and rules
2. **Enhanced Audit Engine** - Detects missing scope, fee breakdowns, timelines, invoices, and contracts
3. **Continuous Learning System** - Learns from user feedback and improves accuracy over time
4. **Complete API** - 20+ new endpoints for managing all audit data

---

## 📊 Current System Status

### Audit Results (as of build):
- **153 projects audited**
- **329 suggestions generated:**
  - 153 scope issues (projects missing scope definitions)
  - 138 fee issues (projects missing fee breakdowns)
  - 0 timeline issues (no contracts to validate yet)
  - 0 invoice issues
  - 38 contract issues (active projects missing contracts)

---

## 🔌 Available API Endpoints

### **Project Scope Management**

#### `GET /api/projects/{project_code}/scope`
Get project scope (disciplines and fee breakdown per discipline)

**Response:**
```json
{
  "project_code": "24 BK-074",
  "scopes": [
    {
      "scope_id": "uuid",
      "discipline": "landscape",
      "fee_usd": 2000000,
      "percentage_of_total": 61.5,
      "scope_description": "Full landscape design",
      "confirmed_by_user": true,
      "confidence": 0.95,
      "created_at": "2025-11-15T..."
    },
    {
      "discipline": "interiors",
      "fee_usd": 1250000,
      "percentage_of_total": 38.5,
      ...
    }
  ]
}
```

#### `POST /api/projects/{project_code}/scope`
Add or update project scope

**Request Body:**
```json
{
  "disciplines": ["landscape", "interiors"],
  "fee_breakdown": {
    "landscape": 2000000,
    "interiors": 1250000
  },
  "scope_description": "Villa with landscape and interiors",
  "confirmed_by_user": true
}
```

---

### **Fee Breakdown Management**

#### `GET /api/projects/{project_code}/fee-breakdown`
Get fee breakdown by phase (mobilization, concept, schematic, dd, cd, ca)

**Response:**
```json
{
  "project_code": "24 BK-074",
  "breakdown": [
    {
      "breakdown_id": "uuid",
      "phase": "mobilization",
      "phase_fee_usd": 650000,
      "percentage_of_total": 20,
      "payment_status": "pending",
      "confirmed_by_user": true,
      "created_at": "..."
    },
    {
      "phase": "concept",
      "phase_fee_usd": 580000,
      "percentage_of_total": 17.8,
      ...
    }
  ]
}
```

#### `POST /api/projects/{project_code}/fee-breakdown`
Set fee breakdown by phase

**Request Body:**
```json
{
  "phases": {
    "mobilization": 650000,
    "concept": 580000,
    "schematic": 325000,
    "dd": 650000,
    "cd": 580000,
    "ca": 465000
  },
  "confirmed_by_user": true
}
```

**Standard Phases:**
- `mobilization` - Paid on contract signing
- `concept` - 3-4 months
- `schematic` - 1 month
- `dd` (Design Development) - 4 months
- `cd` (Construction Drawings) - 3-4 months
- `ca` (Construction Observation) - Until contract end

---

### **Timeline Management**

#### `GET /api/projects/{project_code}/timeline`
Get phase timeline

**Response:**
```json
{
  "project_code": "24 BK-074",
  "timeline": [
    {
      "timeline_id": "uuid",
      "phase": "concept",
      "expected_duration_months": 3.5,
      "start_date": "2024-03-15",
      "expected_end_date": "2024-07-01",
      "actual_end_date": null,
      "presentation_date": "2024-06-15",
      "status": "in_progress",
      "delay_days": 0,
      "notes": "Client presentation on June 15",
      "confirmed_by_user": true
    }
  ]
}
```

#### `POST /api/projects/{project_code}/timeline`
Set project timeline

**Request Body:**
```json
{
  "phases": [
    {
      "phase": "concept",
      "expected_duration_months": 3.5,
      "start_date": "2024-03-15",
      "expected_end_date": "2024-07-01",
      "presentation_date": "2024-06-15",
      "status": "in_progress"
    }
  ],
  "confirmed_by_user": true
}
```

**Timeline Statuses:**
- `not_started` - Phase hasn't begun
- `in_progress` - Currently working on this phase
- `completed` - Phase finished
- `delayed` - Behind schedule
- `on_hold` - Temporarily paused

---

### **Contract Terms Management**

#### `GET /api/projects/{project_code}/contract`
Get contract terms

**Response:**
```json
{
  "project_code": "24 BK-074",
  "contract": {
    "contract_id": "uuid",
    "contract_signed_date": "2024-03-01",
    "contract_start_date": "2024-03-15",
    "total_contract_term_months": 18,
    "contract_end_date": "2025-09-15",
    "total_fee_usd": 3250000,
    "contract_type": "fixed_fee",
    "payment_schedule": {
      "mobilization": {"due": "2024-03-15", "amount": 650000},
      "concept": {"due": "2024-07-01", "amount": 580000}
    },
    "confirmed_by_user": true,
    "created_at": "..."
  }
}
```

#### `POST /api/projects/{project_code}/contract`
Set contract terms

**Request Body:**
```json
{
  "contract_signed_date": "2024-03-01",
  "contract_start_date": "2024-03-15",
  "total_contract_term_months": 18,
  "contract_end_date": "2025-09-15",
  "total_fee_usd": 3250000,
  "contract_type": "fixed_fee",
  "payment_schedule": {...},
  "confirmed_by_user": true
}
```

**Contract Types:**
- `fixed_fee` - Fixed total fee
- `hourly` - Hourly billing
- `percentage` - Percentage of construction cost
- `hybrid` - Combination of above

---

### **Learning & Feedback**

#### `POST /api/audit/feedback/{project_code}`
Submit user feedback for continuous learning

**Request Body:**
```json
{
  "question_type": "scope",
  "ai_suggestion": {
    "disciplines": ["landscape"]
  },
  "user_correction": {
    "disciplines": ["landscape", "interiors"]
  },
  "context_provided": "This is a villa project which always includes both landscape and interiors",
  "confidence_before": 0.75
}
```

**Response:**
```json
{
  "success": true,
  "context_id": "uuid",
  "message": "Feedback logged and patterns extracted"
}
```

#### `GET /api/audit/learning-stats`
Get learning system statistics

**Response:**
```json
{
  "total_feedback": 42,
  "patterns_extracted": 8,
  "active_rules": 12,
  "auto_apply_rules": 3,
  "avg_accuracy": 0.87,
  "top_rules": [
    {
      "rule_label": "Villa projects include landscape + interiors",
      "accuracy_rate": 0.95,
      "times_confirmed": 19,
      "times_rejected": 1
    }
  ],
  "recent_feedback_by_type": {
    "scope": 15,
    "fee_breakdown": 12,
    "timeline": 8
  }
}
```

#### `GET /api/audit/auto-apply-candidates`
Get rules that are candidates for auto-apply

**Response:**
```json
{
  "candidates": [
    {
      "rule_id": "uuid",
      "rule_label": "Mobilization is typically 20% of total fee",
      "rule_type": "fee_validation",
      "accuracy_rate": 0.92,
      "times_suggested": 25,
      "times_confirmed": 23,
      "times_rejected": 2,
      "sample_size": 25,
      "recommendation": "Enable auto-apply"
    }
  ]
}
```

#### `POST /api/audit/enable-auto-apply/{rule_id}`
Enable auto-apply for a specific rule

**Response:**
```json
{
  "success": true,
  "rule_id": "uuid",
  "message": "Auto-apply enabled"
}
```

---

### **Re-Audit Triggers**

#### `POST /api/audit/re-audit/{project_code}`
Re-audit a specific project (useful after adding new data)

**Response:**
```json
{
  "success": true,
  "project_code": "24 BK-074",
  "suggestions_generated": 2,
  "breakdown": {
    "scope": 1,
    "fee": 1,
    "timeline": 0,
    "invoice": 0,
    "contract": 0
  }
}
```

#### `POST /api/audit/re-audit-all`
Re-audit all projects in database

**Response:**
```json
{
  "success": true,
  "projects_audited": 153,
  "total_suggestions": 329,
  "breakdown": {
    "scope": 153,
    "fee": 138,
    "timeline": 0,
    "invoice": 0,
    "contract": 38
  }
}
```

---

## 🎨 Recommended UI Design

### **1. Project Detail Page Enhancements**

When viewing a project (e.g., "24 BK-074"), add the following sections:

#### **A. Scope Section**
```
┌─────────────────────────────────────────────┐
│ 📋 Project Scope                     [Edit] │
├─────────────────────────────────────────────┤
│ Landscape          $2,000,000 (61.5%)       │
│ Interiors          $1,250,000 (38.5%)       │
│                                             │
│ Total              $3,250,000               │
│                                             │
│ ✅ Confirmed by user                        │
└─────────────────────────────────────────────┘
```

**Edit Modal:**
- Checkboxes for: [ ] Landscape [ ] Interiors [ ] Architecture
- If checked, show fee input for each discipline
- Auto-calculate percentages
- "Confirm" button to save

#### **B. Fee Breakdown Section**
```
┌─────────────────────────────────────────────────────────────┐
│ 💰 Fee Breakdown by Phase                           [Edit]  │
├─────────────────────────────────────────────────────────────┤
│ Mobilization       $650,000 (20.0%)  ⏺️ Pending            │
│ Concept            $580,000 (17.8%)  ⏺️ Pending            │
│ Schematic          $325,000 (10.0%)  ⏺️ Pending            │
│ Design Development $650,000 (20.0%)  ⏺️ Pending            │
│ Construction Dwgs  $580,000 (17.8%)  ⏺️ Pending            │
│ Const. Observation $465,000 (14.3%)  ⏺️ Pending            │
├─────────────────────────────────────────────────────────────┤
│ Total              $3,250,000                               │
│                                                             │
│ ✅ Confirmed by user                                        │
└─────────────────────────────────────────────────────────────┘
```

**Payment Status Colors:**
- ⏺️ Pending (gray)
- 📄 Invoiced (blue)
- ✅ Paid (green)
- ❌ Waived (red)

**Edit Modal:**
- Input for each phase fee
- Auto-calculate percentages
- Dropdown for payment status
- "Confirm" button

#### **C. Timeline Section**
```
┌─────────────────────────────────────────────────────────────┐
│ 📅 Project Timeline                                  [Edit]  │
├─────────────────────────────────────────────────────────────┤
│ Contract Start: Mar 15, 2024  │  Contract End: Sep 15, 2025  │
│ Total Term: 18 months                                        │
├─────────────────────────────────────────────────────────────┤
│ Phase              Duration  Start      End         Status   │
│ ─────────────────────────────────────────────────────────── │
│ Mobilization       0mo       Mar 15     Mar 15      ✅ Done  │
│ Concept            3.5mo     Mar 15     Jul 1       🔄 In Progress │
│   └─ Presentation: Jun 15, 2024                             │
│ Schematic          1mo       Jul 1      Aug 1       ⏳ Pending │
│ Design Dev         4mo       Aug 1      Dec 1       ⏳ Pending │
│ Const. Drawings    3.5mo     Dec 1      Mar 15 '25  ⏳ Pending │
│ Const. Observation 6mo       Mar 15     Sep 15 '25  ⏳ Pending │
│                                                             │
│ ✅ Confirmed by user                                        │
└─────────────────────────────────────────────────────────────┘
```

**Status Icons:**
- ⏳ Not Started (gray)
- 🔄 In Progress (blue)
- ✅ Completed (green)
- ⚠️ Delayed (red)
- ⏸️ On Hold (yellow)

**Edit Modal:**
- For each phase:
  - Expected duration (months)
  - Start/end dates
  - Presentation date (optional)
  - Status dropdown
  - Notes field
- Timeline visualization (Gantt-style)

#### **D. Contract Section**
```
┌─────────────────────────────────────────────┐
│ 📋 Contract Terms                    [Edit] │
├─────────────────────────────────────────────┤
│ Signed: Mar 1, 2024                         │
│ Start: Mar 15, 2024                         │
│ End: Sep 15, 2025 (18 months)              │
│                                             │
│ Total Fee: $3,250,000                       │
│ Type: Fixed Fee                             │
│                                             │
│ ✅ Confirmed by user                        │
└─────────────────────────────────────────────┘
```

---

### **2. New "Audit Dashboard" Page**

Create a new page: `/audit-dashboard`

#### **A. Summary Cards**
```
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ 🔍 Scope Issues  │ │ 💰 Fee Issues    │ │ 📋 Contract Gaps │
│                  │ │                  │ │                  │
│       153        │ │       138        │ │        38        │
│   projects       │ │   projects       │ │   projects       │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

#### **B. Suggestions List (Interactive)**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📊 AI Suggestions                               [Re-Audit All]  │
├─────────────────────────────────────────────────────────────────┤
│ Filters: [All] [Urgent] [Needs Attention] [FYI]                │
│          [Scope] [Fee] [Timeline] [Invoice] [Contract]         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 🔴 URGENT                                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 24 BK-074 - The Residences                                 │ │
│ │ Missing Contract                                            │ │
│ │                                                             │ │
│ │ 💥 Impact: Active project with no contract data            │ │
│ │ 📊 Evidence: Project marked active, $1M outstanding balance │ │
│ │ ✨ Proposed Fix: Add contract terms                        │ │
│ │                                                             │ │
│ │ Confidence: 85%                                             │ │
│ │                                                             │ │
│ │ [Accept] [Preview] [Reject] [Snooze] [View Project]       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ⚠️ NEEDS ATTENTION                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 19 BK-012 - Garden Plaza                                   │ │
│ │ Missing Scope Definition                                    │ │
│ │                                                             │ │
│ │ 💥 Impact: No scope defined for landscape project          │ │
│ │ 📊 Evidence: Name contains "garden", no scope in DB        │ │
│ │ ✨ Proposed Fix: Add landscape scope                       │ │
│ │                                                             │ │
│ │ Confidence: 80%                                             │ │
│ │                                                             │ │
│ │ [Accept] [Preview] [Reject] [Snooze] [View Project]       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Actions:**
- **Accept** - Apply the suggestion and mark as approved
- **Preview** - Show what would change (dry-run)
- **Reject** - Reject with reason (improves AI learning)
- **Snooze** - Remind in 7 days
- **View Project** - Navigate to project detail page

#### **C. Learning Dashboard**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🧠 Learning System Statistics                                   │
├─────────────────────────────────────────────────────────────────┤
│ Total Feedback: 42  │  Patterns Extracted: 8  │  Avg Accuracy: 87% │
│ Active Rules: 12    │  Auto-Apply Enabled: 3                     │
├─────────────────────────────────────────────────────────────────┤
│ 🏆 Top Performing Rules:                                        │
│                                                                 │
│ 1. Villa projects include landscape + interiors                │
│    Accuracy: 95% (19 confirmed, 1 rejected)                    │
│                                                                 │
│ 2. Mobilization is typically 20% of total fee                  │
│    Accuracy: 92% (23 confirmed, 2 rejected)                    │
│    [Enable Auto-Apply]                                         │
│                                                                 │
│ 3. Contract term matches phase durations                       │
│    Accuracy: 88% (15 confirmed, 2 rejected)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Typical User Workflow

1. **User imports new contract data** (PDF upload or manual entry)
   - Frontend: Call `POST /api/projects/{code}/contract`

2. **System auto-triggers re-audit**
   - Frontend: Call `POST /api/audit/re-audit/{code}`
   - Backend: Generates suggestions based on new data

3. **User reviews suggestions**
   - Frontend: Display suggestions on audit dashboard
   - User clicks "Accept" on a suggestion

4. **User provides context (optional but encouraged)**
   - Modal: "Why is this correct?" input field
   - Frontend: Call `POST /api/audit/feedback/{code}` with context

5. **System learns from feedback**
   - Backend: Extracts patterns from user's explanation
   - Updates confidence scores
   - Suggests auto-apply if accuracy > 90% over 20+ samples

6. **Next import triggers smarter suggestions**
   - System applies learned patterns
   - Higher confidence scores
   - Eventually auto-applies high-accuracy rules

---

## 🚀 Implementation Priority for Codex

### Phase 2E - Part 1: Core UI (High Priority)
1. Add scope, fee breakdown, timeline, and contract sections to project detail page
2. Build "Edit" modals for each section
3. Wire up to API endpoints

### Phase 2E - Part 2: Audit Dashboard (High Priority)
1. Create `/audit-dashboard` page
2. Display suggestions list with filters
3. Implement Accept/Reject/Snooze actions
4. Add feedback modal for learning

### Phase 2E - Part 3: Learning Dashboard (Medium Priority)
1. Add learning stats section to audit dashboard
2. Display top performing rules
3. Enable auto-apply button

### Phase 2E - Part 4: Auto-Triggers (Low Priority)
1. Auto re-audit when contract/invoice data added
2. Show notification when new suggestions available
3. Batch operations (accept all by pattern)

---

## 📝 Notes for Codex

- All backend endpoints are **tested and working**
- Database schema is **complete**
- Audit engine is **running and generating suggestions**
- Currently 329 suggestions pending review
- Learning system is ready but needs user feedback to start improving
- All APIs return proper JSON and handle errors

**Start with Part 1** (adding sections to project detail page) as this provides immediate value and allows users to start entering the missing data that the audit system is detecting.

---

**Questions or Issues?** Ask Claude (me) - I built the entire backend and can clarify any details!
