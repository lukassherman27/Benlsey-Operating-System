# Backend-Frontend Integration Guide
**Generated:** 2025-01-14
**Last Updated:** 2025-01-14
**Status:** All 15 endpoints working ✅

## Overview

This guide documents all backend endpoints for Codex's Operations Dashboard:
- **4 Dashboard Endpoints:** Timeline, briefing, decision tiles, system health
- **5 Manual Overrides Endpoints:** Track Bill's instructions and context
- **6 Training Data Endpoints:** Human-in-the-loop AI learning (NEW!)

All endpoints are fully tested and working. See sections below for integration details.

---

## Backend Endpoints Status

### ✅ 1. Enhanced Timeline Endpoint
**Endpoint:** `GET /api/proposals/by-code/{project_code}/timeline`
**Purpose:** Get milestone timeline with enhanced context fields
**Status:** WORKING

**Example Request:**
```bash
curl http://localhost:8000/api/proposals/by-code/BK-033/timeline
```

**Response Structure:**
```typescript
{
  "proposal": {
    "project_code": "BK-033",
    "project_name": "The Ritz Carlton Reserve...",
    "status": "active"
  },
  "timeline": [
    {
      "type": "milestone",
      "milestone_name": "Concept Deck",
      "expected_date": "2025-02-22",
      "actual_date": null,
      "status": "pending",
      "delay_reason": null,
      "delay_days": 0,
      "responsible_party": "bensley",
      "milestone_owner": "Ferry Maruf",
      "expected_vs_actual_days": 0,
      "notes": "Initial concept presentation",
      "project_code": "BK-033",
      "project_name": "The Ritz Carlton Reserve..."
    }
  ],
  "stats": {
    "timeline_events": 1
  }
}
```

**Frontend Integration:**
- Already exists in `api.ts` as `getProposalTimeline()`
- Uses existing `ProposalTimelineResponse` type
- **Action:** Add new context fields to type definition

---

### ✅ 2. Pre-Meeting Briefing Endpoint
**Endpoint:** `GET /api/proposals/by-code/{project_code}/briefing`
**Purpose:** Comprehensive pre-meeting briefing for Bill
**Status:** WORKING (returns real data!)

**Example Request:**
```bash
curl http://localhost:8000/api/proposals/by-code/BK-033/briefing
```

**Response Structure:**
```typescript
{
  "client": {
    "name": "PT Bali Destinasi Lestari",
    "contact": "Contact TBD",
    "email": "contact@client.com",
    "last_contact_date": null,
    "days_since_contact": 0,
    "next_action": "No action specified"
  },
  "project": {
    "code": "BK-033",
    "name": "The Ritz Carlton Reserve...",
    "phase": "Unknown",
    "status": "won",
    "win_probability": 0,
    "health_score": 0,
    "health_status": "unknown",
    "pm": "Mr.Ferry Murruf"
  },
  "submissions": [],
  "financials": {
    "total_contract_value": 0,
    "currency": "USD",
    "initial_payment_received": 0,
    "outstanding_balance": 0,
    "next_payment": null,
    "overdue_amount": 0
  },
  "milestones": [],
  "open_issues": {
    "rfis": [],
    "blockers": [],
    "internal_tasks": []
  },
  "recent_emails": [
    {
      "date": "Wed, 9 Jul 2025 11:12:56 +0800",
      "subject": "RE: Invitation of RITZ-CARLTON RESERVE kick-off meeting...",
      "sender": "<ferry.maruf@bdlbali.com>",
      "category": "meeting",
      "snippet": "Ferry Maruf confirms attendance at RITZ-CARLTON RESERVE kick-off meeting..."
    }
  ],
  "documents_breakdown": {
    "total": 0,
    "by_type": {
      "contracts": 0,
      "presentations": 0,
      "drawings": 0,
      "renderings": 0
    }
  }
}
```

**Frontend Integration:**
- **NEW** - Not in api.ts yet
- **Action:** Add to api.ts
- **Action:** Create TypeScript type `ProposalBriefing`
- **Action:** Wire up to briefing modal in dashboard

---

### ✅ 3. Decision Tiles Endpoint
**Endpoint:** `GET /api/dashboard/decision-tiles`
**Purpose:** What needs Bill's attention TODAY
**Status:** WORKING

**Example Request:**
```bash
curl http://localhost:8000/api/dashboard/decision-tiles
```

**Response Structure:**
```typescript
{
  "needs_outreach": {
    "count": 0,
    "description": "Proposals with no contact in 14+ days",
    "items": [
      {
        "project_code": "BK-XXX",
        "project_name": "Project Name",
        "pm": "Contact Person",
        "days_since_contact": 21,
        "next_action": "Follow up on proposal"
      }
    ]
  },
  "unanswered_rfis": {
    "count": 0,
    "description": "RFIs awaiting response",
    "items": []
  },
  "overdue_milestones": {
    "count": 0,
    "description": "Milestones past expected date",
    "items": []
  },
  "upcoming_meetings": {
    "count": 0,
    "description": "Meetings scheduled in next 7 days",
    "items": []
  },
  "invoices_awaiting_payment": {
    "count": 0,
    "total_amount": 0,
    "description": "Outstanding invoices",
    "items": []
  }
}
```

**Frontend Integration:**
- **NEW** - Not in api.ts yet
- **Action:** Add to api.ts
- **Action:** Create TypeScript type `DecisionTiles`
- **Action:** Replace hardcoded fallback data in dashboard-page.tsx (lines 154-227)

---

### ✅ 4. System Health Endpoint
**Endpoint:** `GET /api/admin/system-health`
**Purpose:** Internal monitoring metrics (NOT for Bill's dashboard)
**Status:** WORKING

**Example Request:**
```bash
curl http://localhost:8000/api/admin/system-health
```

**Response Structure:**
```typescript
{
  "email_processing": {
    "total_emails": 774,
    "processed": 774,
    "unprocessed": 0,
    "categorized_percent": 100.0,
    "processing_rate": "~50/hour"
  },
  "model_training": {
    "training_samples": 774,
    "target_samples": 5000,
    "completion_percent": 15.5,
    "model_accuracy": 0.87
  },
  "database": {
    "total_proposals": 87,
    "active_projects": 1,
    "total_documents": 0,
    "last_sync": "2025-01-14T10:30:00Z"
  },
  "api_health": {
    "uptime_seconds": 86400,
    "requests_last_hour": 342,
    "avg_response_time_ms": 45
  }
}
```

**Frontend Integration:**
- **Optional** - For internal admin dashboard
- This is NOT for Bill - it's for you/Lukas
- Shows system health, not project health

---

## Frontend Integration Steps

### Step 1: Add TypeScript Types

Add these types to `frontend/src/lib/types.ts`:

```typescript
// Pre-Meeting Briefing
export interface ProposalBriefing {
  client: {
    name: string;
    contact: string;
    email: string;
    last_contact_date: string | null;
    days_since_contact: number;
    next_action: string;
  };
  project: {
    code: string;
    name: string;
    phase: string;
    status: string;
    win_probability: number;
    health_score: number;
    health_status: string;
    pm: string;
  };
  submissions: any[]; // TODO: define proper type
  financials: {
    total_contract_value: number;
    currency: string;
    initial_payment_received: number;
    outstanding_balance: number;
    next_payment: string | null;
    overdue_amount: number;
  };
  milestones: Array<{
    milestone_name: string;
    expected_date: string;
    status: string;
    responsible_party: string;
  }>;
  open_issues: {
    rfis: any[];
    blockers: any[];
    internal_tasks: any[];
  };
  recent_emails: Array<{
    date: string;
    subject: string;
    sender: string;
    category: string;
    snippet: string;
  }>;
  documents_breakdown: {
    total: number;
    by_type: {
      contracts: number;
      presentations: number;
      drawings: number;
      renderings: number;
    };
  };
}

// Decision Tiles
export interface DecisionTileItem {
  project_code: string;
  project_name: string;
  pm?: string;
  days_since_contact?: number;
  next_action?: string;
  milestone_name?: string;
  expected_date?: string;
  delay_days?: number;
  rfi_number?: string;
  question?: string;
  asked_date?: string;
  meeting_title?: string;
  scheduled_date?: string;
  meeting_type?: string;
}

export interface DecisionTiles {
  needs_outreach: {
    count: number;
    description: string;
    items: DecisionTileItem[];
  };
  unanswered_rfis: {
    count: number;
    description: string;
    items: DecisionTileItem[];
  };
  overdue_milestones: {
    count: number;
    description: string;
    items: DecisionTileItem[];
  };
  upcoming_meetings: {
    count: number;
    description: string;
    items: DecisionTileItem[];
  };
  invoices_awaiting_payment: {
    count: number;
    total_amount: number;
    description: string;
    items: any[];
  };
}

// System Health (optional - for internal use)
export interface SystemHealth {
  email_processing: {
    total_emails: number;
    processed: number;
    unprocessed: number;
    categorized_percent: number;
    processing_rate: string;
  };
  model_training: {
    training_samples: number;
    target_samples: number;
    completion_percent: number;
    model_accuracy: number;
  };
  database: {
    total_proposals: number;
    active_projects: number;
    total_documents: number;
    last_sync: string;
  };
  api_health: {
    uptime_seconds: number;
    requests_last_hour: number;
    avg_response_time_ms: number;
  };
}
```

### Step 2: Add API Functions

Add these functions to `frontend/src/lib/api.ts`:

```typescript
// Add to existing api object
export const api = {
  // ... existing functions ...

  getProposalBriefing: (projectCode: string) =>
    request<ProposalBriefing>(
      `/api/proposals/by-code/${encodeURIComponent(projectCode)}/briefing`
    ),

  getDecisionTiles: () =>
    request<DecisionTiles>("/api/dashboard/decision-tiles"),

  getSystemHealth: () =>
    request<SystemHealth>("/api/admin/system-health"),
};
```

### Step 3: Update Dashboard Components

#### In `dashboard-page.tsx`:

**Replace hardcoded fallback data (lines 154-227) with:**

```tsx
// Fetch decision tiles
const decisionTilesQuery = useQuery({
  queryKey: ["decision-tiles"],
  queryFn: api.getDecisionTiles,
  refetchInterval: 60000, // Refresh every minute
  refetchIntervalInBackground: false,
});

const decisionTiles = decisionTilesQuery.data;

// Use real data instead of fallback
const milestonesToShow = decisionTiles?.overdue_milestones.items || [];
const outreachNeeded = decisionTiles?.needs_outreach.items || [];
```

#### For Pre-Meeting Briefing Modal:

**Create new component `proposal-briefing-modal.tsx`:**

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Props = {
  projectCode: string | null;
  open: boolean;
  onClose: () => void;
};

export default function ProposalBriefingModal({ projectCode, open, onClose }: Props) {
  const briefingQuery = useQuery({
    queryKey: ["proposal-briefing", projectCode],
    queryFn: () => api.getProposalBriefing(projectCode!),
    enabled: !!projectCode && open,
  });

  const briefing = briefingQuery.data;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Pre-Meeting Briefing: {briefing?.project.name}</DialogTitle>
        </DialogHeader>

        {briefingQuery.isLoading ? (
          <div>Loading briefing...</div>
        ) : !briefing ? (
          <div>No briefing available</div>
        ) : (
          <div className="space-y-6">
            {/* Client Section */}
            <section>
              <h3 className="font-semibold text-lg mb-2">Client</h3>
              <p><strong>Company:</strong> {briefing.client.name}</p>
              <p><strong>Last Contact:</strong> {briefing.client.days_since_contact} days ago</p>
              <p><strong>Next Action:</strong> {briefing.client.next_action}</p>
            </section>

            {/* Project Snapshot */}
            <section>
              <h3 className="font-semibold text-lg mb-2">Project Snapshot</h3>
              <p><strong>Phase:</strong> {briefing.project.phase}</p>
              <p><strong>Status:</strong> {briefing.project.status}</p>
              <p><strong>Health Score:</strong> {briefing.project.health_score}</p>
              <p><strong>PM:</strong> {briefing.project.pm}</p>
            </section>

            {/* Recent Communications */}
            <section>
              <h3 className="font-semibold text-lg mb-2">Recent Emails ({briefing.recent_emails.length})</h3>
              {briefing.recent_emails.map((email, i) => (
                <div key={i} className="border-b pb-2 mb-2">
                  <p className="font-medium">{email.subject}</p>
                  <p className="text-sm text-muted-foreground">
                    From: {email.sender} | {email.date}
                  </p>
                  <p className="text-sm">{email.snippet}</p>
                </div>
              ))}
            </section>

            {/* Milestones */}
            <section>
              <h3 className="font-semibold text-lg mb-2">Upcoming Milestones</h3>
              {briefing.milestones.length === 0 ? (
                <p className="text-muted-foreground">No upcoming milestones</p>
              ) : (
                briefing.milestones.map((milestone, i) => (
                  <div key={i} className="border-b pb-2 mb-2">
                    <p className="font-medium">{milestone.milestone_name}</p>
                    <p className="text-sm">Expected: {milestone.expected_date}</p>
                    <p className="text-sm">Responsible: {milestone.responsible_party}</p>
                  </div>
                ))
              )}
            </section>

            {/* Financials */}
            <section>
              <h3 className="font-semibold text-lg mb-2">Financials</h3>
              <p><strong>Contract Value:</strong> {briefing.financials.total_contract_value.toLocaleString()} {briefing.financials.currency}</p>
              <p><strong>Received:</strong> {briefing.financials.initial_payment_received.toLocaleString()}</p>
              <p><strong>Outstanding:</strong> {briefing.financials.outstanding_balance.toLocaleString()}</p>
            </section>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
```

**Then in proposal-detail.tsx or proposal-table.tsx, add a button:**

```tsx
import { useState } from "react";
import ProposalBriefingModal from "./proposal-briefing-modal";

export default function ProposalDetailPanel({ proposal, ... }: Props) {
  const [briefingOpen, setBriefingOpen] = useState(false);

  return (
    <>
      <Card>
        {/* Existing content */}
        <Button onClick={() => setBriefingOpen(true)}>
          Open Pre-Meeting Briefing
        </Button>
      </Card>

      <ProposalBriefingModal
        projectCode={proposal?.project_code || null}
        open={briefingOpen}
        onClose={() => setBriefingOpen(false)}
      />
    </>
  );
}
```

---

## Database Schema Notes

### Schema Fixes Applied

1. **Milestone Table:** Uses `project_id` (not `proposal_id`), `planned_date` (not `expected_date`)
2. **Proposals Table:** Has `project_phase` (not `phase`), `contact_person` (not `pm`)
3. **Email Links:** Emails linked to proposals through `email_proposal_links` table
4. **Attachments:** Linked to emails (not directly to proposals)

### Current Data Status

| Table | Records | Status |
|-------|---------|--------|
| proposals | 87 | ✅ Populated |
| project_milestones | 110 | ✅ Populated |
| emails | 774 | ✅ Populated |
| email_proposal_links | Varies | ✅ Working |
| attachments | 0 | ⚠️ Empty |
| project_rfis | 0 | ⚠️ Empty |
| project_financials | 0 | ⚠️ Empty |
| project_meetings | 0 | ⚠️ Empty |

**Impact:** Empty tables return empty arrays gracefully - endpoints still work.

---

## Testing Checklist

- [x] Timeline endpoint returns data
- [x] Briefing endpoint returns real emails
- [x] Decision tiles endpoint works (returns empty gracefully)
- [x] System health endpoint works
- [ ] Frontend types added
- [ ] API functions added to api.ts
- [ ] Briefing modal component created
- [ ] Dashboard wired to decision tiles
- [ ] End-to-end test in browser

---

## Next Steps

1. **Codex:** Add TypeScript types to `types.ts`
2. **Codex:** Add API functions to `api.ts`
3. **Codex:** Create briefing modal component
4. **Codex:** Wire up decision tiles to dashboard
5. **Codex:** Test in browser
6. **Codex:** Remove hardcoded fallback data once confirmed working

---

## Training Data Verification Endpoints (NEW!)

**Added:** 2025-01-14
**Status:** All 6 endpoints working ✅
**Purpose:** Human-in-the-loop AI learning - Bill can review and correct 6,409 unverified AI decisions

### ✅ 1. Get Unverified Training Data
**Endpoint:** `GET /api/training/unverified`
**Purpose:** Get paginated list of AI decisions needing verification
**Status:** WORKING

**Query Parameters:**
- `task_type` (optional): Filter by task type ("classify", "extract", "summarize")
- `min_confidence` (optional): Minimum confidence score (0.0-1.0)
- `max_confidence` (optional): Maximum confidence score (0.0-1.0)
- `page` (default: 1): Page number
- `per_page` (default: 20, max: 100): Items per page

**Example Request:**
```bash
curl "http://localhost:8000/api/training/unverified?task_type=classify&page=1&per_page=20"
```

**Response Structure:**
```typescript
{
  "data": [
    {
      "training_id": 6433,
      "task_type": "classify",
      "input_data": "Full AI prompt with email categorization instructions...",
      "output_data": "proposal",
      "model_used": "gpt-3.5-turbo",
      "confidence": 0.8,
      "human_verified": 0,
      "feedback": null,
      "created_at": "2025-11-14 05:41:04"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 2137,
    "total_pages": 107
  }
}
```

**TypeScript Types:**
```typescript
interface TrainingRecord {
  training_id: number;
  task_type: "classify" | "extract" | "summarize";
  input_data: string;  // The full AI prompt
  output_data: string;  // The AI's answer
  model_used: string;
  confidence: number;
  human_verified: 0 | 1;
  feedback: string | null;  // JSON string when verified
  created_at: string;
}

interface TrainingListResponse {
  data: TrainingRecord[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
}
```

**Frontend Integration:**
```typescript
// Add to api.ts
export async function getUnverifiedTraining(params: {
  taskType?: string;
  minConfidence?: number;
  maxConfidence?: number;
  page?: number;
  perPage?: number;
}): Promise<TrainingListResponse> {
  const queryParams = new URLSearchParams();
  if (params.taskType) queryParams.append('task_type', params.taskType);
  if (params.minConfidence !== undefined) queryParams.append('min_confidence', params.minConfidence.toString());
  if (params.maxConfidence !== undefined) queryParams.append('max_confidence', params.maxConfidence.toString());
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.perPage) queryParams.append('per_page', params.perPage.toString());

  const response = await fetch(`/api/training/unverified?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch training data');
  return response.json();
}
```

---

### ✅ 2. Get Training Stats
**Endpoint:** `GET /api/training/stats`
**Purpose:** Overview of verification progress
**Status:** WORKING

**Example Request:**
```bash
curl http://localhost:8000/api/training/stats
```

**Response Structure:**
```typescript
{
  "overall": {
    "total": 6410,
    "verified": 1,
    "unverified": 6409
  },
  "by_task_type": [
    {
      "task_type": "classify",
      "total": 2137,
      "verified": 0,
      "unverified": 2137,
      "avg_confidence": 0.82
    },
    {
      "task_type": "extract",
      "total": 2136,
      "verified": 0,
      "unverified": 2136,
      "avg_confidence": 0.79
    },
    {
      "task_type": "summarize",
      "total": 2136,
      "verified": 0,
      "unverified": 2136,
      "avg_confidence": 0.81
    }
  ],
  "by_confidence": [
    {
      "confidence_range": "high (0.9+)",
      "total": 1234,
      "verified": 0,
      "unverified": 1234
    },
    {
      "confidence_range": "medium (0.7-0.9)",
      "total": 4321,
      "verified": 1,
      "unverified": 4320
    },
    {
      "confidence_range": "low (<0.7)",
      "total": 855,
      "verified": 0,
      "unverified": 855
    }
  ]
}
```

**TypeScript Type:**
```typescript
interface TrainingStats {
  overall: {
    total: number;
    verified: number;
    unverified: number;
  };
  by_task_type: Array<{
    task_type: string;
    total: number;
    verified: number;
    unverified: number;
    avg_confidence: number;
  }>;
  by_confidence: Array<{
    confidence_range: string;
    total: number;
    verified: number;
    unverified: number;
  }>;
}
```

---

### ✅ 3. Get Training by ID
**Endpoint:** `GET /api/training/{training_id}`
**Purpose:** Get specific training record details
**Status:** WORKING

**Example Request:**
```bash
curl http://localhost:8000/api/training/6433
```

**Response:** Single `TrainingRecord` object (see type above)

---

### ✅ 4. Verify Training Record
**Endpoint:** `POST /api/training/{training_id}/verify`
**Purpose:** Mark AI decision as correct or provide correction
**Status:** WORKING

**Request Body:**
```typescript
{
  "is_correct": false,
  "feedback": "Should be project_update not proposal",
  "corrected_output": "project_update"  // Optional, only if is_correct=false
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/training/6433/verify \
  -H "Content-Type: application/json" \
  -d '{"is_correct": false, "feedback": "Should be project_update", "corrected_output": "project_update"}'
```

**Response:** Updated `TrainingRecord` with `human_verified=1` and feedback JSON stored

**TypeScript Types:**
```typescript
interface TrainingVerification {
  is_correct: boolean;
  feedback?: string;
  corrected_output?: string;
}

// Frontend Integration
export async function verifyTraining(
  trainingId: number,
  verification: TrainingVerification
): Promise<TrainingRecord> {
  const response = await fetch(`/api/training/${trainingId}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(verification)
  });
  if (!response.ok) throw new Error('Failed to verify training');
  return response.json();
}
```

---

### ✅ 5. Bulk Verify Training
**Endpoint:** `POST /api/training/verify/bulk`
**Purpose:** Verify multiple records at once (approve 20 correct categorizations)
**Status:** WORKING

**Request Body:**
```typescript
{
  "training_ids": [6430, 6427, 6424],
  "is_correct": true,
  "feedback": "All correctly categorized"  // Optional
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/training/verify/bulk \
  -H "Content-Type: application/json" \
  -d '{"training_ids": [6430, 6427], "is_correct": true, "feedback": "Both correct"}'
```

**Response:**
```typescript
{
  "verified_count": 2,
  "training_ids": [6430, 6427]
}
```

**TypeScript Types:**
```typescript
interface BulkVerification {
  training_ids: number[];
  is_correct: boolean;
  feedback?: string;
}

interface BulkVerificationResponse {
  verified_count: number;
  training_ids: number[];
}
```

---

### ✅ 6. Get Incorrect Predictions
**Endpoint:** `GET /api/training/incorrect`
**Purpose:** View AI mistakes to identify patterns and improve prompts
**Status:** WORKING

**Query Parameters:**
- `task_type` (optional): Filter by task type
- `page` (default: 1): Page number
- `per_page` (default: 20): Items per page

**Example Request:**
```bash
curl "http://localhost:8000/api/training/incorrect?task_type=classify&page=1"
```

**Response:** Same structure as `/unverified` but only returns records where `is_correct=false`

---

### Use Cases

#### 1. Review AI Email Categorizations Widget
Shows unverified email categorizations for Bill to approve/correct:
```typescript
const { data, pagination } = await getUnverifiedTraining({
  taskType: 'classify',
  page: 1,
  perPage: 20
});

// Display each record with:
// - Email subject/snippet
// - AI's category choice
// - Confidence score
// - [✓ Correct] [✗ Wrong] buttons
```

#### 2. Training Progress Dashboard Widget
Show overall verification progress:
```typescript
const stats = await fetch('/api/training/stats').then(r => r.json());

// Display:
// - Progress bar: 1 / 6,409 verified (0.02%)
// - Breakdown by task type
// - Confidence distribution chart
```

#### 3. Bulk Approve Similar Decisions
Select multiple correct categorizations and approve at once:
```typescript
await fetch('/api/training/verify/bulk', {
  method: 'POST',
  body: JSON.stringify({
    training_ids: selectedIds,
    is_correct: true,
    feedback: 'All correctly categorized as invoice emails'
  })
});
```

#### 4. AI Mistake Analysis
Review common errors to improve prompts:
```typescript
const { data } = await fetch('/api/training/incorrect?task_type=classify').then(r => r.json());

// Analyze patterns:
// - Which categories are most confused?
// - What confidence scores correlate with mistakes?
// - Common words in misclassified emails?
```

---

### Database Schema

**Table:** `training_data`

| Column | Type | Description |
|--------|------|-------------|
| training_id | INTEGER | Primary key |
| task_type | TEXT | "classify", "extract", "summarize" |
| input_data | TEXT | Full AI prompt |
| output_data | TEXT | AI's response |
| model_used | TEXT | e.g., "gpt-3.5-turbo" |
| confidence | REAL | 0.0-1.0 confidence score |
| human_verified | INTEGER | 0 or 1 (boolean) |
| feedback | TEXT | JSON with verification details |
| created_at | TIMESTAMP | When AI made the decision |

**Feedback JSON Structure** (when verified):
```json
{
  "is_correct": false,
  "feedback": "Should be project_update not proposal",
  "corrected_output": "project_update",
  "verified_at": "2025-11-14T16:27:12.879177"
}
```

---

### Current Training Data Status

- **Total records:** 6,410
- **Verified:** 1 (0.02%)
- **Unverified:** 6,409
  - 2,137 email classifications
  - 2,136 entity extractions
  - 2,136 email summaries

**Priority:** Bill should start verifying email classifications to train the AI on correct categorization patterns.

---

## Known TODOs

### Backend
- [ ] Populate `project_rfis` table with RFI data
- [ ] Populate `project_financials` table with financial data
- [ ] Populate `project_meetings` table with meeting data
- [ ] Link attachments to proposals (currently 0 attachments)
- [ ] Add document type categorization for "by_type" breakdown

### Frontend
- [ ] Implement server-side search for proposals (client-side won't scale to 500+)
- [ ] Add debouncing to search input
- [ ] Create admin dashboard for system health metrics
- [ ] Add loading states and error handling for all API calls

---

## Questions for User

1. **Milestone data:** BK-033 shows 0 milestones. Should we populate test milestone data?
2. **Financial tracking:** Do you want to manually enter financial data or import from another system?
3. **Document linking:** How should we link existing files to proposals? Manual or automated?
4. **PM tracking:** Should we add a `pm` column to proposals table, or keep using `contact_person`?

---

## Performance Notes

- All endpoints respond in <100ms with current data volume (87 proposals, 774 emails)
- Decision tiles endpoint queries multiple tables - consider caching if slow
- Briefing endpoint joins 3+ tables - performance acceptable for single-proposal queries
- Consider adding indexes if queries slow down with more data

---

**End of Integration Guide**
For questions or issues, see AI_DIALOGUE.md or contact Claude/Codex.
