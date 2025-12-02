# Backend Context Bundle

**Owner:** Backend Builder Agent
**Last Updated:** 2025-12-02
**Architecture:** Modular routers (28 files, 220+ endpoints)

---

## CANONICAL DATABASE (CRITICAL)

```
CANONICAL: database/bensley_master.db (OneDrive/repo)
- Size: ~103 MB
- Updated: 2025-11-28
- USE THIS ONE ONLY

DEPRECATED: ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db
- Size: ~80 MB (older)
- DO NOT USE - backup only
```

**All scripts/services MUST use:**
```python
db_path = os.getenv("DATABASE_PATH", "database/bensley_master.db")
```

**Never hardcode paths to the Desktop copy.**

---

## Quick Start

```bash
# Run backend
cd backend && uvicorn api.main:app --reload --port 8000

# Access
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## Architecture

```
backend/
├── api/
│   ├── main.py           # App init, router registration (263 lines)
│   ├── dependencies.py   # DB_PATH, shared deps
│   ├── helpers.py        # Response formatters
│   ├── models.py         # Pydantic models
│   ├── services.py       # Service initialization
│   └── routers/          # 28 modular router files
│       ├── admin.py      # /api/admin/* (includes run-pipeline)
│       ├── agent.py      # /api/agent/*
│       ├── analytics.py  # /api/analytics/*
│       ├── contacts.py   # /api/contacts/* (NEW)
│       ├── context.py    # /api/context/*
│       ├── contracts.py  # /api/contracts/*
│       ├── dashboard.py  # /api/dashboard/*
│       ├── deliverables.py
│       ├── documents.py
│       ├── email_categories.py # /api/email-categories/* (NEW)
│       ├── emails.py     # /api/emails/*
│       ├── files.py      # /api/files/*
│       ├── finance.py    # /api/finance/*
│       ├── health.py     # /api/health
│       ├── intelligence.py
│       ├── invoices.py
│       ├── learning.py   # /api/learning/*
│       ├── meetings.py
│       ├── milestones.py
│       ├── outreach.py
│       ├── projects.py
│       ├── proposals.py
│       ├── query.py      # /api/query/*
│       ├── rfis.py
│       ├── suggestions.py
│       ├── tasks.py      # /api/tasks/* (NEW)
│       ├── training.py
│       └── transcripts.py
├── services/            # Business logic (60+ files)
│   └── suggestion_handlers/  # Handler registry (8 types)
├── core/                # Utilities & one-time tools
└── utils/               # Logging, helpers
```

---

## API Endpoint Categories (220+ Total)

| Category | Router | Status | Notes |
|----------|--------|--------|-------|
| Proposals | proposals.py | ✅ | CRUD, stats, health scoring |
| Projects | projects.py | ✅ | CRUD, unified timeline |
| Emails | emails.py | ✅ | Includes scan-sent-proposals |
| Email Categories | email_categories.py | ✅ NEW | Categorization system |
| Invoices | invoices.py | ✅ | CRUD, aging |
| Intelligence | intelligence.py | ✅ | AI features |
| Query/Search | query.py | ✅ | Natural language |
| Dashboard | dashboard.py | ✅ | KPIs |
| Meetings | meetings.py | ✅ | Meeting management |
| RFIs | rfis.py | ✅ | RFI tracking |
| Contracts | contracts.py | ✅ | Contract management |
| Deliverables | deliverables.py | ✅ | PM workload |
| Training | training.py | ✅ | AI training data |
| Admin | admin.py | ✅ | Includes run-pipeline |
| Transcripts | transcripts.py | ✅ | Meeting transcripts |
| Context | context.py | ✅ | Notes, context |
| Files | files.py | ✅ | File management |
| Documents | documents.py | ✅ | Document management |
| Milestones | milestones.py | ✅ | Milestone tracking |
| Outreach | outreach.py | ✅ | Client outreach |
| Contacts | contacts.py | ✅ NEW | Contact CRUD |
| Tasks | tasks.py | ✅ NEW | Task management |
| Suggestions | suggestions.py | ✅ | AI suggestions, handlers, patterns, **full-context API, multi-link corrections, category updates, contact context learning** |
| Analytics | analytics.py | ✅ | Analytics |
| Finance | finance.py | ✅ | Financial reports |
| Learning | learning.py | ✅ | AI learning |
| Agent | agent.py | ✅ | Agent interface |
| Health | health.py | ✅ | Health checks |

---

## CLI Services (Not API Endpoints)

These services are used via CLI scripts, not API endpoints:

```python
# CLI/Batch Processing - Run via scripts/
email_importer.py            # IMAP email import (scripts/core/scheduled_email_sync.py)
email_content_processor.py   # Email content analysis
excel_importer.py            # Excel data import
schedule_pdf_parser.py       # PDF schedule parsing
schedule_pdf_generator.py    # PDF schedule generation
schedule_emailer.py          # Schedule email automation
sent_email_detector.py       # Detect sent proposals (NEW)
```

**Note:** These are intentionally CLI-only for batch processing.

---

## Adding a New Endpoint

### 1. Find or Create Service

```python
# backend/services/my_feature_service.py
class MyFeatureService:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        return self.db.execute("SELECT * FROM my_table").fetchall()
```

### 2. Add to main.py

```python
# backend/api/main.py

# At top - import service
from services.my_feature_service import MyFeatureService

# Add endpoint
@app.get("/api/my-feature")
async def get_my_feature():
    service = MyFeatureService(get_db())
    return {"data": service.get_all()}
```

### 3. Test

```bash
curl http://localhost:8000/api/my-feature
```

---

## Database Connection

```python
# Pattern used throughout main.py
def get_db():
    db_path = os.getenv("DATABASE_PATH", "database/bensley_master.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
```

---

## Key Services (Used Daily)

| Service | Purpose | Endpoints |
|---------|---------|-----------|
| `proposal_tracker_service.py` | Proposal CRUD, health scoring | 16 |
| `email_service.py` | Email listing, categorization | 8 |
| `query_service.py` | Natural language queries | 9 |
| `invoice_service.py` | Invoice tracking | 5 |
| `intelligence_service.py` | AI suggestions | 10 |
| `suggestions.py` router | Patterns, enhanced feedback | 15+ |

---

## Enhanced Feedback System (NEW Dec 2025)

The suggestions router now includes enhanced feedback endpoints for learning from user corrections:

### Pattern Management
```
GET  /api/patterns          # List learned patterns (filter by type/project/active)
GET  /api/patterns/stats    # Pattern statistics and performance
GET  /api/patterns/{id}     # Get pattern with usage history
POST /api/patterns          # Manually create a pattern
PUT  /api/patterns/{id}     # Update pattern (notes, confidence, active)
DELETE /api/patterns/{id}   # Delete a pattern
```

### Enhanced Feedback
```
POST /api/suggestions/{id}/reject-with-correction
  - rejection_reason: string (required)
  - correct_project_code: string (optional - backward compat, single project link)
  - linked_items: array (optional - multi-link support)
    - type: 'project' | 'proposal' | 'category'
    - code: string (project/proposal code)
    - name: string (optional display name)
  - category: string (optional - email category: internal, external, spam, etc.)
  - subcategory: string (optional - hr, it, admin, etc.)
  - create_pattern: bool (optional - learns from correction)
  - pattern_notes: string (optional)

POST /api/suggestions/{id}/approve-with-context
  - create_sender_pattern: bool (optional)
  - create_domain_pattern: bool (optional)
  - contact_role: string (optional)
  - pattern_notes: string (optional)
```

### Pattern Types
- `sender_to_project` - Links emails from specific sender to project
- `domain_to_project` - Links emails from domain to project
- `sender_to_proposal` - Links emails to proposals
- `domain_to_proposal` - Links domain emails to proposals
- `keyword_to_project` - Links by keyword matching
- `contact_to_project` - Links contacts to projects

---

## Contact Context Learning System (NEW Dec 2025)

The system now learns rich context about contacts from user feedback. When a user rejects a suggestion with notes like "Suresh is a kitchen consultant who works on many projects", the system:

1. **Extracts structured context** using OpenAI (role, relationship, is_client, is_multi_project)
2. **Stores in contact_context table** for future use
3. **Uses context in email suggestions** - skips project linking for multi-project contacts

### Contact Context Endpoints
```
GET  /api/contact-context/{email}    # Get context for a contact
GET  /api/contact-context            # List all contexts (with filters)
GET  /api/contact-context-stats      # Statistics
GET  /api/multi-project-contacts     # Contacts who work across projects
POST /api/contact-context/{email}/update  # Manually update context
```

### Contact Context Fields
- `role` - Job role (e.g., "kitchen consultant", "project manager")
- `relationship_type` - One of: client, client_team, vendor, contractor, internal, external
- `is_client` - Boolean: is this a client contact?
- `is_multi_project` - Boolean: works across multiple projects?
- `email_handling_preference` - How to handle their emails:
  - `link_to_project` - Always suggest project links
  - `categorize_only` - Just categorize, don't suggest links
  - `suggest_multiple` - May relate to multiple projects
  - `default` - Normal handling
- `default_category` / `default_subcategory` - Auto-categorization

### Service: contact_context_service.py
```python
from backend.services.contact_context_service import get_contact_context_service

service = get_contact_context_service()

# Extract context from user notes
context = service.extract_context_from_notes("John is our internal IT guy")
# Returns: {"role": "IT support", "relationship_type": "internal", "is_client": false}

# Check if we should skip project linking
if service.should_skip_project_linking(sender_email):
    # Don't suggest project links for this contact
    pass

# Get display info for UI
display = service.get_display_info_for_contact(email)
# Returns: {"role": "Kitchen Consultant", "badge": "Multi-Project"}
```

---

## Common Patterns

### Return Format
```python
# Always return JSON with consistent structure
return {"data": [...], "total": 100, "page": 1}

# Or for single items
return {"item": {...}, "success": True}
```

### Error Handling
```python
from fastapi import HTTPException

if not item:
    raise HTTPException(status_code=404, detail="Item not found")
```

### Query Parameters
```python
@app.get("/api/items")
async def get_items(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    ...
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_services.py -v

# With coverage
pytest tests/ --cov=backend
```

---

## Environment Variables

```bash
DATABASE_PATH=database/bensley_master.db
ANTHROPIC_API_KEY=sk-ant-...
LOG_LEVEL=INFO
```

---

## Files Changed Frequently

| File | Purpose | Watch For |
|------|---------|-----------|
| `main.py` | All endpoints | New routes, imports |
| `query_service.py` | AI queries | Query logic changes |
| `email_service.py` | Email ops | Linking, categorization |
| `proposal_tracker_service.py` | Proposals | Status, health |

---

---

## CLI-Only Scripts (Need API Wrappers)

These scripts work but are ONLY callable from command line - need API endpoints:

| Script | Purpose | Priority |
|--------|---------|----------|
| `scripts/core/smart_email_brain.py` | Main email AI processor | P0 |
| `scripts/core/email_linker.py` | Email-to-project linking | P0 |
| `scripts/core/suggestion_processor.py` | Process AI suggestions | P0 |
| `backend/services/email_importer.py` | Import emails from IMAP | P1 |
| `backend/services/email_content_processor*.py` | Process email content | P1 |
| `scripts/core/generate_weekly_proposal_report.py` | Weekly reports | P2 |
| `backend/services/project_creator.py` | Create new projects | P1 |

**Email flow broken:** import → content → AI → link all CLI-only

---

## APIs WITH NO FRONTEND (Need Pages)

**UPDATE:** Most of these now have pages:

| API | Endpoints | Page | Status |
|-----|-----------|------|--------|
| Calendar/Meetings | `/api/meetings` | `/meetings` | Working |
| Transcripts | `/api/meeting-transcripts/*` | `/transcripts` | Working |
| Contracts | `/api/contracts/*` | `/contracts` | Working |
| RFI Dashboard | `/api/rfis/*` | `/rfis` | Working |
| Audit System | `/api/audit/*` | `/admin/audit` | Working |
| Analytics | Multiple | `/analytics` | Working |

**All major APIs now have frontend pages.**

---

## DUPLICATE ENDPOINTS (Standardize)

| Pattern A | Pattern B | Keep | Deprecate |
|-----------|-----------|------|-----------|
| `/api/proposals/by-code/{code}` | `/api/proposals/{id}` | by-code | id-based |
| `/api/training/stats` | `/api/learning/stats` | training | learning |
| `/api/projects/{code}/fee-breakdown` | `/api/phase-fees` | projects path | phase-fees |

**Standard response envelope:**
```json
{
  "data": [...],
  "meta": { "total": 100, "page": 1, "per_page": 50 }
}
```

---

## Queries This Context Answers

- "How do I add an API endpoint?"
- "Where is [feature] implemented?"
- "What services are orphaned?"
- "How do I run the backend?"
- "What's the API structure?"
- "What CLI scripts need API wrappers?"
- "What APIs have no frontend?"
