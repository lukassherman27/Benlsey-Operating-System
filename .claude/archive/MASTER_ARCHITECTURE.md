# 🏗️ BENSLEY OPERATIONS PLATFORM - MASTER ARCHITECTURE

**Last Updated:** 2025-11-26
**Status:** CANONICAL REFERENCE - ALL AGENTS MUST FOLLOW THIS

---

## ⚠️ CRITICAL RULES FOR ALL AGENTS

1. **NEVER CREATE NEW TABLES** - Use existing schema
2. **NEVER REPLACE EXISTING FILES** - Only modify or extend
3. **NEVER CREATE PARALLEL SYSTEMS** - Integrate with existing
4. **ALWAYS CHECK THIS DOCUMENT FIRST** - Before making any changes
5. **USE EXISTING SCRIPTS** - Extend, don't recreate

---

## 📊 DATABASE ARCHITECTURE

### Single Source of Truth
**Location:** `/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db`
**Size:** 81MB
**Tables:** 60+ tables (see full list below)

### Core Tables (ALREADY EXIST - USE THESE)

#### Proposals & Lifecycle
- `proposals` - Main proposal data (89 records)
  - Has: project_code, project_name, status, current_status, days_in_current_status, first_contact_date, proposal_sent_date, country, location, currency
- `proposal_status_history` - Status change audit trail ✅ EXISTS
- `proposal_timeline` - Timeline events ✅ EXISTS
- `proposal_tracker` - Tracking dashboard data ✅ EXISTS
- `proposals_audit_log` - Change log ✅ EXISTS

#### Projects & Contracts
- `projects` - Active contracts (financial data)
- `contract_phases` - Phase breakdown ✅ EXISTS
- `project_fee_breakdown` - Multi-scope support
- `contract_metadata` - Contract details ✅ EXISTS

#### Emails & Intelligence
- `emails` - Email headers (3,356 records)
- `email_content` - Email bodies **EMPTY - NEEDS POPULATION**
  - Columns: content_id, email_id, clean_body, quoted_text, category, key_points, entities, sentiment, importance_score, ai_summary, subcategory, urgency_level, action_required, human_approved
- `email_project_links` - Email-project associations (521 links)
- `email_proposal_links` - Email-proposal associations ✅ EXISTS
- `email_attachments` - Attachment tracking (1,179 records) ✅ EXISTS
- `email_tags` - Tagging system ✅ EXISTS
- `email_threads` - Thread tracking ✅ EXISTS

#### RFIs & Deliverables
- `rfis` - RFI tracking ✅ EXISTS (table ready, not populated)
- `deliverables` - Deliverable tracking ✅ EXISTS

#### Financial
- `invoices` - Invoice records with payment dates
- `invoice_aging` - Aging analysis ✅ EXISTS

#### Intelligence & Learning
- `ai_observations` - AI insights ✅ EXISTS
- `training_data` - ML training data ✅ EXISTS
- `training_data_feedback` - User feedback ✅ EXISTS
- `learned_patterns` - Pattern recognition ✅ EXISTS
- `data_quality_tracking` - Quality metrics ✅ EXISTS

---

## 🔧 EXISTING SCRIPTS (USE THESE - DON'T RECREATE)

### Email Processing
- `smart_email_system.py` (16K) - **PRIMARY EMAIL PROCESSOR** - Two-layer AI system
- `smart_email_processor_v3.py` (17K) - Latest processor version
- `smart_email_batch_processor.py` (15K) - Batch processing
- `smart_email_validator.py` (16K) - Validation system
- `ai_email_linker.py` (14K) - **WORKING** - Links emails to projects

### Proposal Import
- `import_proposal_dashboard.py` (11K) - **JUST USED** - Imports from "Proposal dashboard " sheet
- `import_proposals_v2.py` (13K) - V2 importer
- `import_comprehensive_proposal_data.py` (13K) - Comprehensive importer

### Contract/Invoice Import
- `import_contract_data.py` (23K) - Contract importer
- `import_step3_contracts.py` (14K) - Step 3 of import process
- `import_verified_invoices.py` (5.3K) - Invoice importer

### Email Utilities
- `relink_all_emails.py` (3.7K) - Re-link emails to projects
- `backfill_email_folders.py` (2.2K) - Folder organization
- `view_linked_emails.py` (4.0K) - View linkages

---

## 🔌 BACKEND API (backend/api/main.py)

### Existing Endpoints (93+)
- **Proposals:** `/api/proposals`, `/api/proposals/{code}`, `/api/proposal-tracker/*`
- **Projects:** `/api/projects/active`, `/api/projects/{code}/fee-breakdown`
- **Financial:** `/api/finance/recent-payments`, `/api/invoices/aging`
- **Dashboard:** `/api/dashboard/kpis`, `/api/dashboard/top-outstanding`
- **Emails:** `/api/emails/categories`, `/api/emails/{id}`

### API Architecture
- FastAPI with auto-reload
- Port: 8000
- SQLite connection via: `database/bensley_master.db`
- All endpoints return JSON

---

## 🎨 FRONTEND STRUCTURE (frontend/src/)

### Pages (App Router)
- `app/(dashboard)/page.tsx` - Main dashboard
- `app/(dashboard)/projects/` - Projects section
- `app/(dashboard)/proposals/[projectCode]/` - Proposal details
- `app/(dashboard)/tracker/` - Proposal tracker

### Components
- `components/dashboard/` - Dashboard widgets (30+ components)
- `components/proposals/` - Proposal management
- `components/ui/` - Shared UI components

### Key Files
- `lib/api.ts` - API client functions
- `lib/types.ts` - TypeScript interfaces

---

## 📋 CURRENT STATE ASSESSMENT

### ✅ What's Working
1. **Financial tracking** - Contracts, invoices, payments (46% invoiced tracked correctly)
2. **Proposal data** - 89 proposals with status, timeline data
3. **Email import** - 3,356 emails imported with metadata
4. **Project linking** - 521 emails linked to projects via AI
5. **Attachment tracking** - 1,179 attachments stored and linked

### ❌ Critical Gaps
1. **Email content extraction** - `email_content` table is EMPTY (0 records)
   - WHY: Need to determine which script extracts body content
   - IMPACT: Can't do AI categorization, RFI detection, or show email bodies in UI
2. **Proposal status history** - Table exists but not being populated on status changes
3. **RFI system** - Table exists but no detection/population logic
4. **Frontend integration** - Many features not connected to UI

---

## 🎯 AGENT COORDINATION STRATEGY

### Principle: EXTEND, DON'T REPLACE

When agents need to make changes:

1. **Check MASTER_ARCHITECTURE.md first**
2. **Use existing tables** - Never create duplicates
3. **Extend existing scripts** - Add functions, don't rewrite
4. **Follow naming conventions** - Match existing patterns
5. **Update this document** - When adding new systems

### File Ownership (Avoid Conflicts)

| Agent | Owned Files | NEVER Touch |
|-------|-------------|-------------|
| Email Brain | `smart_email_system.py` modifications | Proposal import scripts |
| Proposal Lifecycle | `backend/api/main.py` (lines 940-1400) | Email processing scripts |
| RFI Detection | New `rfi_detector.py` | Existing smart_email_*.py |
| Deliverables | New `deliverable_extractor.py` | Core email/proposal scripts |
| Frontend | `frontend/src/` only | Backend API files |

---

## 🚀 IMMEDIATE PRIORITIES

### Priority 1: Fix Email Content Extraction
**Goal:** Populate `email_content` table with 3,356 email bodies
**Approach:** Determine which existing script does this, fix if broken, run it

### Priority 2: Proposal Status Tracking
**Goal:** Auto-populate `proposal_status_history` on every status change
**Approach:** Add trigger or API middleware to capture changes

### Priority 3: RFI Detection
**Goal:** Auto-detect RFIs from emails, populate `rfis` table
**Approach:** Add RFI detection logic to `smart_email_system.py`

---

## 📝 CHANGE LOG

When agents make changes, they MUST update this section:

### 2025-11-26 - Initial Architecture Documentation
- Created master architecture document
- Audited existing 60+ tables
- Identified critical gaps (email_content empty)
- Documented existing scripts and endpoints

### 2025-11-26 - Agent 3: RFI Detection System
**Files Modified:**
- `backend/services/rfi_service.py` - Rewrote to use correct `rfis` table
- `backend/api/main.py` - Added 7 new RFI endpoints

**Files Created:**
- `rfi_detector.py` - RFI detection from emails (designed for rfi@bensley.com)
- `database/migrations/031_project_pm_assignments.sql` - PM assignment foundation

**New Tables:**
- `project_pm_assignments` - Dynamic PM-to-project assignment
- `team_member_specialties` - Sub-specialties within disciplines

**New Views:**
- `v_current_project_pms` - Current PM for each project
- `v_pm_workload` - PM workload statistics

**New API Endpoints:**
- `GET /api/rfis/overdue` - Overdue RFIs (past 48hr SLA)
- `GET /api/rfis/stats` - Dashboard statistics
- `POST /api/rfis/{id}/respond` - Mark RFI as responded
- `POST /api/rfis/{id}/close` - Close RFI
- `POST /api/rfis/{id}/assign` - Assign PM to RFI
- `GET /api/rfis/by-project/{code}` - RFIs by project

### 2025-11-26 - Agent 4: Deliverables & PM Workload System
**Files Created:**
- `backend/services/deliverables_service.py` - Full deliverables management service
- `frontend/src/app/(dashboard)/deliverables/page.tsx` - PM Workload Dashboard

**Files Modified:**
- `backend/api/main.py` - Added 15 deliverables/workload endpoints
- `frontend/src/lib/api.ts` - Added deliverables API functions and types
- `frontend/src/components/layout/app-shell.tsx` - Added Deliverables nav item

**Key Features:**
- Project lifecycle phase templates (Mobilization -> Construction Observation)
- PM inference from emails + schedules + manual input
- Multi-tier alert system (14 days, 7 days, 1 day, day-of)
- Overdue flagging with context explanations
- Milestone-to-deliverable seeding (110 records seeded)

**New API Endpoints:**
- `GET /api/deliverables` - List with filters
- `POST /api/deliverables` - Create new
- `GET /api/deliverables/overdue` - Overdue list
- `GET /api/deliverables/upcoming` - Due within N days
- `GET /api/deliverables/alerts` - Multi-tier alerts
- `PUT /api/deliverables/{id}/status` - Update status
- `POST /api/deliverables/{id}/context` - Add overdue context
- `GET /api/pm-workload` - PM workload summary
- `GET /api/pm-list` - Available PMs
- `GET /api/projects/{code}/phase-status` - Phase status with flags
- `GET /api/projects/{code}/inferred-pm` - Infer PM for project
- `POST /api/projects/{code}/generate-milestones` - Generate lifecycle milestones
- `POST /api/deliverables/seed-from-milestones` - Seed from project_milestones
- `GET /api/lifecycle-phases` - Get lifecycle template

### [AGENTS: ADD YOUR CHANGES HERE]

---

## 🔍 HOW TO USE THIS DOCUMENT

**Before Starting Work:**
1. Read this entire document
2. Identify which tables/scripts you'll use
3. Check "File Ownership" to avoid conflicts
4. Verify table existence before creating

**While Working:**
1. Reference table schemas from this doc
2. Use existing scripts as templates
3. Follow naming conventions

**After Completing:**
1. Update CHANGE LOG section
2. Document any new tables/columns added
3. Update "Current State Assessment"

---

## ⚠️ FAILURE MODES TO AVOID

1. **Creating duplicate tables** - Check schema first
2. **Creating parallel email systems** - Extend `smart_email_system.py`
3. **Replacing working scripts** - Modify, don't recreate
4. **Breaking existing linkages** - Test before committing
5. **Ignoring existing data** - Always check what's already there

---

**END OF MASTER ARCHITECTURE DOCUMENT**

All agents must acknowledge reading this document before starting work.
