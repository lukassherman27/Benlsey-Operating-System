# BENSLEY OPERATIONS SYSTEM - ARCHITECTURE MAP

**Last Updated:** 2025-11-24
**Architect:** Master Planning Claude

---

## SYSTEM OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    BENSLEY OPERATIONS PLATFORM                   │
│                                                                  │
│  Email System → Database ← Excel Files ← PDF Contracts           │
│       ↓            ↓            ↓              ↓                 │
│   AI Processing → Master DB → Dashboards → Reports              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. DATA SOURCES (Input Layer)

### 1.1 Email Server
- **Location:** `tmail.bensley.com:993` (IMAP)
- **Current Count:** ~3,356 emails
- **Import Script:** `backend/services/email_importer.py`
- **Categories:** Proposals, Contracts, RFIs, General
- **AI Processing:** `bensley_email_intelligence.py`

### 1.2 Excel Files (OneDrive)
- **Invoice List:** `/Users/.../List of Oversea Invoice 2024-2025.xlsx`
- **Project Status:** `/Users/.../Project Status as of 17 Nov 25.xls`
  - **Key Sheet:** "Bill's Project Status-27 Oct 25"
  - **Contains:** Invoice→Project mappings (528 invoices)
- **Purpose:** Source of truth for invoice-to-project relationships

### 1.3 PDF Documents (OneDrive)
- **Proposals:** `/Users/.../Proposal 2025 (Nung)/` (139 .docx files)
- **Contracts:** Various locations (to be consolidated)
- **Processing:** `import_proposal_documents.py` uses OpenAI for extraction

### 1.4 Manual Inputs
- **Contract PDFs:** Finance team provides (currently 2+ weeks delayed)
- **Updates:** Through frontend dashboards (to be built)

---

## 2. DATABASE LAYER (Core)

### 2.1 Master Database
**CURRENT LOCATION (AFTER MIGRATION):**
`/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db`

**ARCHITECTURE:**
- **Type:** SQLite
- **Size:** ~86MB
- **Tables:** 90 tables (after consolidation)
- **Indexes:** 192 indexes
- **Schema:** Managed via migrations in `database/migrations/`

### 2.2 Core Tables

**Projects Lifecycle:**
```
proposals (87 records)           projects (138 records)
    ↓                                   ↓
  status: 'won'              status: 'Active', 'Completed'
    ↓                                   ↓
contract_signed_date          contract_phases (15 records)
    ↓                                   ↓
active_project_id ←→ proposal_id    invoices (547 records)
```

**Key Tables:**
- `proposals` - Sales pipeline (87 records)
- `projects` - Active contracts (138 records)
- `invoices` - Billing (547 records)
- `emails` - Communications (3,356 records)
- `contract_phases` - Project phases (15 records)
- `clients` - Client companies (1 record currently)

**Important Relationships:**
- `proposals.active_project_id` → `projects.project_id`
- `projects.proposal_id` → `proposals.proposal_id`
- `invoices.project_id` → `projects.project_id`
- `emails` → linked via AI to projects/proposals

### 2.3 Provenance Tracking
**Every record has:**
- `source_type` - Where data came from (email, pdf, manual, excel)
- `source_reference` - Specific source (filename, email ID)
- `created_by` - Who/what created it
- `updated_by` - Who/what last modified
- `locked_fields` - Which fields are locked from auto-update
- `locked_by` - Who locked it
- `locked_at` - When it was locked

**Purpose:** Track data lineage, prevent AI from overwriting human edits

---

## 3. PROCESSING LAYER (Scripts)

### 3.1 Import Scripts
| Script | Purpose | Inputs | Outputs |
|--------|---------|--------|---------|
| `backend/services/email_importer.py` | Import emails from server | IMAP | emails table |
| `import_proposal_documents.py` | Extract data from proposals | .docx files | proposals table |
| `parse_contracts.py` | Extract contract data | PDF files | projects, contract_phases |
| `parse_invoices_v2.py` | Extract invoice data | PDF/Excel | invoices table |

### 3.2 AI Processing Scripts
| Script | Purpose | AI Model | Cost |
|--------|---------|----------|------|
| `bensley_email_intelligence.py` | Categorize emails | GPT-4o-mini | ~$0.01/email |
| `proposal_email_intelligence.py` | Link emails to proposals | GPT-4o-mini | ~$0.02/link |
| `comprehensive_document_intelligence.py` | Extract structured data | GPT-4o | ~$0.10/doc |

### 3.3 Fix/Audit Scripts
| Script | Purpose |
|--------|---------|
| `fix_project_lifecycle_links.py` | Fix proposal↔project links |
| `audit_invoice_links.py` | Audit invoice-to-project links |
| `fix_project_classifications.py` | Fix project status/stage |
| `extract_correct_invoice_links.py` | Compare DB with Excel truth |

### 3.4 Report Generation
| Script | Purpose | Output |
|--------|---------|--------|
| `generate_weekly_proposal_report.py` | Weekly proposal status | Email/PDF |
| `monitor_ai_processing.py` | Monitor AI batch jobs | Console |

---

## 4. API LAYER (Backend)

### 4.1 FastAPI Server
- **File:** `backend/api/main.py` (original), `backend/api/main_v2.py` (newer)
- **Port:** 8000 (default)
- **Endpoints:** 93+ endpoints
- **Purpose:** Serve data to frontend, provide CRUD operations

**Key Services:**
- `backend/services/email_processor.py` - Email operations
- `backend/services/proposal_service.py` - Proposal CRUD
- `backend/services/contract_service.py` - Contract operations
- `backend/services/financial_service.py` - Financial queries
- `backend/services/proposal_tracker_service.py` - Proposal tracking
- `backend/services/invoice_service.py` - Invoice operations

### 4.2 API Structure
```
/api/
  /proposals/
    GET /  - List all proposals
    GET /{id}  - Get proposal details
    POST /  - Create proposal
    PUT /{id}  - Update proposal
  /projects/
    GET /  - List all projects
    GET /{id}  - Get project details
  /invoices/
    GET /  - List all invoices
    GET /project/{id}  - Get project invoices
  /emails/
    GET /  - List emails
    GET /categorized/{category}  - Get by category
```

---

## 5. FRONTEND LAYER (To Be Built)

### 5.1 Next.js Application
- **Location:** `frontend/`
- **Framework:** Next.js 14, React, TypeScript
- **UI Library:** shadcn/ui, Tailwind CSS
- **State:** React Query

### 5.2 Dashboard Pages
| Page | Route | Purpose | Status |
|------|-------|---------|--------|
| Overview | `/` | High-level metrics | In progress |
| Proposals | `/proposals` | Proposal pipeline | In progress |
| Projects | `/projects` | Active projects | Planned |
| Tracker | `/tracker` | Proposal tracker widget | Built |
| Financials | `/financials` | Revenue/invoicing | Planned |

### 5.3 Key Components
- `dashboard-page.tsx` - Main dashboard
- `proposals-manager.tsx` - Proposal CRUD
- `proposal-tracker-widget.tsx` - Quick view of proposals
- `active-projects-tab.tsx` - Active projects view
- `financial-dashboard.tsx` - Financial metrics

---

## 6. DATA FLOW

### 6.1 Email Processing Flow
```
1. Email arrives at tmail.bensley.com
2. email_importer.py pulls via IMAP
3. Stored in emails table (raw)
4. bensley_email_intelligence.py categorizes
5. proposal_email_intelligence.py links to projects
6. Available via API /emails/
7. Displayed in frontend dashboard
```

### 6.2 Invoice Import Flow
```
1. Finance sends PDFs (or Excel)
2. parse_invoices_v2.py extracts data via AI
3. Matches invoice number to project (via Excel mapping)
4. Stores in invoices table with provenance
5. Links to projects.project_id
6. Available via API /invoices/
7. Displayed in financial dashboard
```

### 6.3 Proposal → Project Lifecycle
```
1. Proposal sent (proposals table, status='sent')
2. Follow-up emails tracked
3. Status updates: won/lost/active
4. If won → contract_signed_date set
5. Creates record in projects table
6. Bidirectional link: proposal ↔ project
7. Contract phases created
8. Invoices linked to project
9. Project moves through phases
10. Completed/Archived
```

---

## 7. CONFIGURATION

### 7.1 Environment Variables (.env)
```
DATABASE_PATH=database/bensley_master.db
OPENAI_API_KEY=sk-...
EMAIL_SERVER=tmail.bensley.com
EMAIL_PORT=993
EMAIL_USERNAME=bill@bensley.com
EMAIL_PASSWORD=***
```

### 7.2 Key Paths
```
Working Directory:
/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/

Database:
./database/bensley_master.db

Migrations:
./database/migrations/*.sql

Scripts:
./*.py (root level)
./backend/services/*.py

Frontend:
./frontend/src/

Docs:
./*.md
```

---

## 8. MIGRATION STATUS

### Current Databases
1. **Desktop** (80MB, 547 invoices) - TO BE MIGRATED FROM
2. **OneDrive** (86MB, 253 invoices) - CURRENT WORK LOCATION
3. **After Migration:** Single consolidated database at OneDrive location

### Migration Plan
See `MASTER_MIGRATION_PLAN.md` for 8-phase consolidation plan.

---

## 9. CRITICAL ISSUES (Active)

### Issue 1: Dual Databases
- **Status:** Identified, plan created
- **Impact:** HIGH - Working on wrong database
- **Solution:** Execute MASTER_MIGRATION_PLAN.md

### Issue 2: Invoice Links
- **Status:** Partially audited
- **Impact:** MEDIUM - 36 invoices mislinked
- **Solution:** Phase 7 validation in migration plan

### Issue 3: Missing Invoices
- **Status:** Identified (298 in Excel, not in DB)
- **Impact:** MEDIUM - Incomplete financial data
- **Solution:** Import after migration complete

---

## 10. DEPENDENCIES

### Python Packages
- `fastapi` - API framework
- `sqlite3` - Database
- `openai` - AI processing
- `pandas` - Data manipulation
- `python-docx` - Document parsing
- `PyPDF2` - PDF parsing
- `imaplib` - Email import

### External Services
- **OpenAI API** - Document/email AI processing
- **Email Server** - tmail.bensley.com IMAP
- **OneDrive** - File storage

---

## 11. COORDINATION PROTOCOL

**When executing any task:**

1. Read `MASTER_MIGRATION_PLAN.md` for current phase
2. Check `SYSTEM_ARCHITECTURE_MAP.md` (this file) for context
3. Execute assigned phase tasks
4. Report back with outputs
5. Wait for validation before next phase

**Never:**
- Modify database without backup
- Skip validation steps
- Assume paths without checking
- Execute multiple phases without approval

---

## NEXT ACTIONS

1. **Review** this architecture map
2. **Approve** MASTER_MIGRATION_PLAN.md
3. **Execute** Phase 1 (Backups)
4. **Proceed** through phases sequentially

**Ready to coordinate Implementation Claudes when you give the signal.**
