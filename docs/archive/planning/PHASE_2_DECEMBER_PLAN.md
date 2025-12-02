# BDS Phase 2: December Plan - Data Foundation & Intelligence

**Created:** November 27, 2025
**Goal:** Build rock-solid data foundation before January deployment
**Philosophy:** "Clean data in, smart insights out"

---

## Current State Audit (Nov 27, 2025) - CORRECTED

### Database
| Table | Records | Status | Priority to Fix |
|-------|---------|--------|-----------------|
| proposals | 87 | Good | - |
| projects | 54 | Good | - |
| emails | 3,356 | **68% linked** (2,290) | MEDIUM |
| contacts | 468 | Good | - |
| invoices | 253 | Needs audit | MEDIUM |
| rfis | **3** | Missing data | **HIGH** |
| milestones | 110 | Needs dates | MEDIUM |
| meeting_transcripts | 15 | Growing | - |
| meetings | 2 | Needs population | MEDIUM |
| staff | **3** | Missing data | **HIGH** |
| fee_breakdowns | 279 | Good | - |

### Agent Work Completed (Nov 26-27)
- [x] Query system regex bug fixed
- [x] Progress bar calculations fixed
- [x] Calendar service + NLP meeting creation
- [x] Phase normalization migration
- [x] AI suggestions queue cleaned (3,450 → 801)
- [x] Duplicate suggestions removed (87% → 7%)
- [x] Email linking improved (52% → 68%, +536 emails)
- [x] Follow-up agent (tracks $235M)
- [x] Unified timeline API
- [x] Meeting transcript endpoints
- [x] RFI/Milestone widgets
- [x] **Wynn Marjan multi-scope project structure** - Template for complex projects
- [x] **Project status report API** - `/api/query/project-status/{search}`
- [x] Invoice payment updates (I25-107, I25-108 marked paid)
- [x] Fee breakdown linkage fixes

### Additional Completed Work (Nov 27)

**A. Email Processing → Learning System**
- Connected `smart_email_brain.py` to `AILearningService`
- Fixed schema mismatch in `learned_patterns` table
- Email processing now generates AI suggestions automatically

**B. Rule Generation Engine**
- Added `generate_rules_from_feedback()` to AILearningService
- Analyzes rejection patterns, corrections, category fixes
- 4 new API endpoints: `/api/learning/generate-rules`, `/validate-patterns`, `/decay-patterns`, `/check-suppression`

**C. Proposal Follow-up Agent**
- Created `backend/services/follow_up_agent.py` (637 lines)
- Priority scoring 0-100 with urgency categories (critical → low)
- Shows 81 active proposals, $235M at risk
- 4 API endpoints: `/api/agent/follow-up/proposals`, `/summary`, `/draft/{id}`, `/run-daily`

**D. Suggestion Review UI**
- Created `frontend/src/app/(dashboard)/admin/intelligence/page.tsx`
- Stats dashboard, suggestion review with approve/reject
- Learned patterns display with generate rules button

**E. Query Brain with Patterns**
- Enhanced `backend/services/query_service.py` with:
  - `query_with_patterns()` - Pattern-enhanced SQL generation
  - `record_query_feedback()` - Learning from corrections
  - `get_intelligent_suggestions()` - Smart query suggestions
  - `get_project_status_report()` - Comprehensive project financial reports
- New API endpoints: `/api/query/ask-enhanced`, `/feedback`, `/intelligent-suggestions`, `/stats`, `/project-status/{search}`

### Remaining Issues
1. **Feedback Loop Broken:** 0 training feedback records, 0 human-approved emails
2. **Staff Data Missing:** Only 3 records (should be 50+)
3. **RFI Data Sparse:** Only 3 RFIs (should be 100s)
4. **1,066 Unlinked Emails:** 32% still need linking
5. **Finance Integration:** No accounting email monitoring

---

## Priority Stack (Your Requested Order)

### PRIORITY 1: Email Intelligence System 🔴
**Goal:** Make emails so well-organized that AI can answer any question about project history

**1A. Fix Human Feedback Loop (Days 1-2) - CRITICAL**
- [ ] When user approves → record in `training_data_feedback`
- [ ] When user rejects → don't suggest again
- [ ] Build `learned_patterns` from approvals
- [ ] Tiered auto-processing (high confidence = auto-apply)

**1B. Link the 1,066 Remaining Unlinked Emails (Days 3-4)**
- [ ] Sender matching (contact email → their project)
- [ ] Subject code extraction (find "BK-XXX" in subjects)
- [ ] Thread linking (if one email linked, link all in thread)
- Target: 68% → 90% linked

**1C. Process the 801 Suggestions Queue (Day 5)**
- [x] ~~Duplicates already fixed (now only 7%)~~
- [ ] Review/approve the 248 new_contact suggestions
- [ ] Review/approve the 553 project_alias suggestions
- [ ] Auto-approve high confidence items

**1D. Email Account Integrations (Week 2)**
- [ ] **Finance/Accounting email** → Parse invoices & payment slips
- [ ] **RFI email** → Auto-create RFIs with deadlines
- [ ] **Meetings folder** → Import meeting transcripts

**Success Metrics:**
| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Emails linked | 68% (2,290) | 90%+ | Link 740 more |
| Unlinked emails | 1,066 | <350 | - |
| Duplicate suggestions | 7% | <5% | Minor cleanup |
| Feedback records | 0 | 500+ | Critical gap |
| Learned patterns | 1 | 50+ | Critical gap |

---

### PRIORITY 2: Historical Data Backfill 🔵
**Goal:** Every project has complete info (staff, contracts, scope, history)

**2A. Staff Information (Week 2)**
- [ ] Create staff import from HR records
- [ ] Fields: name, email, discipline (landscape/architecture/interior), role
- [ ] Link staff → projects (who worked on what)
- Target: 3 → 50+ staff records

**2B. Contract Files (Week 2-3)**
- [ ] Scan contract folder for PDFs
- [ ] Extract: client name, fee, scope, dates, payment schedule
- [ ] Link to proposals/projects
- [ ] Parse fee breakdown by phase

**2C. Discipline & Scope (Week 2-3)**
- [ ] For each project: landscape / architecture / interior / combined
- [ ] Scope of work summary
- [ ] Manual entry UI for missing data

**2D. Project History Reconstruction (Week 3)**
- [ ] Timeline of: first contact → proposal → contract → phases → completion
- [ ] Link all emails/meetings/RFIs to timeline
- [ ] Generate "project story" summaries

---

### PRIORITY 3: Query System Enhancement 🟢
**Goal:** Ask "What happened at the last meeting?" and get accurate answers

**3A. Context Aggregation (Week 3)**
- [ ] For each project: combine emails + meetings + RFIs + invoices
- [ ] Generate AI summaries of key events
- [ ] Store in searchable format

**3B. Meeting Intelligence (Week 3)**
- [ ] Auto-extract action items from transcripts
- [ ] Track: who said what, decisions made, next steps
- [ ] Pre-meeting briefings with full context

**3C. Improved Query Interface (Week 4)**
- [ ] "What did [client] say about [topic]?" → Search emails + meetings
- [ ] "Timeline of [project]" → All events chronologically
- [ ] "Outstanding items for [project]" → RFIs + action items + unpaid invoices

---

### PRIORITY 4: Scheduled Data Collection 🟡
**Goal:** System automatically captures and organizes new information

**4A. Email Monitoring Crons (Week 4)**
- [ ] Check finance@bensley.com every hour → Import invoices/payments
- [ ] Check rfi@bensley.com every hour → Create RFI records
- [ ] Check main inbox daily → Categorize & link emails

**4B. Meeting Transcript Pipeline**
- [ ] Transcriber watches folder → Auto-imports
- [ ] AI extracts: project, attendees, decisions, action items
- [ ] Links to calendar meeting record

**4C. Document Watchers (Future)**
- [ ] Contract folder → Auto-import signed contracts
- [ ] Invoice folder → Match payments to invoices

---

### FUTURE PRIORITIES (January+)

**5. Automatic Scheduling System**
- Staff availability tracking
- Project phase deadlines
- Resource allocation optimization

**6. RFI Tracking System**
- Full RFI lifecycle (received → responded → closed)
- Deadline alerts
- PM assignment

**7. Project Management Integration**
- Deliverables tracking
- Phase completion %
- Budget vs actual

---

## Revised Agent Structure

### Agent A: Email Intelligence (CRITICAL)
```
Owns: scripts/core/smart_email_brain.py, backend/services/email_*.py
Tasks:
1. Fix duplicates
2. Link unlinked emails
3. Build feedback loop
4. Finance/RFI email integration
```

### Agent B: Data Backfill
```
Owns: scripts/core/import_*.py, backend/services/project_creator.py
Tasks:
1. Staff import
2. Contract parsing
3. Scope/discipline tagging
4. Historical timeline reconstruction
```

### Agent C: Query & Intelligence
```
Owns: scripts/core/query_brain.py, backend/services/query_service.py
Tasks:
1. Context aggregation
2. Meeting intelligence
3. Improved query prompts
```

### Agent D: Automation & Crons
```
Owns: scripts/core/continuous_*.py, cron configs
Tasks:
1. Email monitoring jobs
2. Transcript pipeline
3. Document watchers
```

---

## Weekly Schedule

### Week 1 (Nov 27 - Dec 3): Email Intelligence
- Mon-Tue: Fix duplicates, add dedup check
- Wed-Thu: Link emails (sender, subject, thread)
- Fri: Fix feedback loop

### Week 2 (Dec 4 - Dec 10): Data Backfill
- Mon-Tue: Staff import, contact cleanup
- Wed-Thu: Contract parsing
- Fri: Discipline/scope tagging

### Week 3 (Dec 11 - Dec 17): Query System
- Mon-Tue: Context aggregation
- Wed-Thu: Meeting intelligence
- Fri: Query improvements

### Week 4 (Dec 18 - Dec 24): Automation
- Mon-Tue: Email monitoring crons
- Wed-Thu: Transcript pipeline
- Fri: Testing & documentation

### Week 5-6 (Dec 25 - Jan 7): Polish
- Bug fixes
- Performance optimization
- User testing with Bill

### Week 7 (Jan 8 - Jan 15): Launch
- Final testing
- Bill training
- Go Live!

---

## Data Cleaning Strategy (For Future LLM Distillation)

### What Big Tech Does:
1. **Data Labeling:** Human reviewers label examples as correct/incorrect
2. **Feedback Collection:** Every user interaction is logged
3. **Pattern Extraction:** Common patterns become rules
4. **Model Refinement:** Feedback trains next model version

### Our Approach:
1. **Suggestion Queue:** AI suggests, human approves/rejects
2. **Feedback Storage:** `training_data_feedback` table captures decisions
3. **Pattern Learning:** `learned_patterns` table stores rules
4. **Confidence Thresholds:** High confidence = auto-apply, low = human review

### Future Local LLM:
1. Collect 10,000+ training examples from feedback
2. Fine-tune small model (Llama/Mistral) on BDS-specific data
3. Run locally for instant categorization
4. Claude/GPT for complex reasoning only

---

## Multi-Scope Project Template (Wynn Marjan Pattern)

For complex projects with multiple scopes under one contract:

**Database Structure:**
```
projects (1 record):
  - project_code: "22 BK-095"
  - project_title: "Wynn Al Marjan Island Project"
  - total_fee_usd: $4,025,000

project_fee_breakdown (multiple records per scope/phase):
  - scope: "indian-brasserie" / "mediterranean-restaurant" / "day-club" / "night-club" / "additional-services"
  - phase: "Mobilization" / "Concept Design" / "Design Development" / "Construction Documents" / "Construction Observation"
  - phase_fee_usd: Contract amount for that phase
  - total_invoiced / total_paid: Calculated from linked invoices

invoices (linked via breakdown_id):
  - breakdown_id: Links invoice to specific scope/phase
  - One invoice can appear multiple times if it covers multiple scopes (e.g., I23-018 covers 3 scopes)
```

**API Endpoint:**
```
GET /api/query/project-status/Wynn%20Marjan
Returns: summary, scopes[], phases_by_scope{}, invoices[]
```

**Example Query:**
```python
from backend.services.query_service import QueryService
qs = QueryService()
report = qs.get_project_status_report('Wynn Marjan')
# Returns structured financial data matching accountant's spreadsheet
```

---

## Files to Focus On

### Email Intelligence
- `scripts/core/smart_email_brain.py` - Main processor
- `backend/services/ai_learning_service.py` - Feedback loop
- `backend/services/email_intelligence_service.py` - Validation
- `.claude/agents/agent-email-intelligence-FULL.md` - Full guide

### Data Import
- `scripts/core/import_step1_proposals.py` - Example pattern
- `backend/services/project_creator.py` - Project creation
- `backend/services/excel_importer.py` - Excel parsing

### Query System
- `scripts/core/query_brain.py` - Query processing
- `backend/services/query_service.py` - SQL generation
- `backend/core/bensley_brain.py` - Context provider

---

## Success Criteria for December

### By Dec 15:
- [ ] 90%+ emails linked to projects
- [ ] 0% duplicate suggestions
- [ ] 500+ feedback records
- [ ] Staff data imported (50+ records)
- [ ] Contract data imported

### By Jan 1:
- [ ] Finance email auto-importing
- [ ] RFI email auto-creating
- [ ] Query system returns accurate answers
- [ ] Meeting transcripts auto-extracting action items

### By Jan 15:
- [ ] Bill using daily without issues
- [ ] Can answer "What happened with [project]?" accurately
- [ ] System runs reliably 24/7

---

## Immediate Next Steps

1. **Start fresh Claude session with:**
   ```
   Read .claude/agents/agent-email-intelligence-FULL.md and implement Phase 1
   ```

2. **Run cleanup SQL:**
   ```sql
   DELETE FROM ai_suggestions_queue
   WHERE suggestion_id NOT IN (
       SELECT MIN(suggestion_id) FROM ai_suggestions_queue
       WHERE field_name = 'new_contact' GROUP BY json_extract(suggested_value, '$.email')
   ) AND field_name = 'new_contact';
   ```

3. **Restart frontend:**
   ```bash
   cd frontend && PORT=3002 npm run dev
   ```
