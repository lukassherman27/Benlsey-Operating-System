# Architecture

**Updated:** 2025-12-26

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA INTAKE CHANNELS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EMAIL CHANNELS                        VOICE/MEETINGS                        │
│  ─────────────────                     ──────────────                        │
│  lukas@        → Proposals, BD         Voice Memos    → Auto-transcribe      │
│  projects@     → Client correspondence Browser record → Shared OneDrive      │
│  invoices@     → Payment tracking      (anyone can record)                   │
│  dailywork@    → Staff daily work                                            │
│  scheduling@   → PM scheduling         UI INPUTS (Future)                    │
│  bill@         → Bill's inbox          ──────────────                        │
│                                        Comments on daily work                │
│                                        Meeting metadata                      │
│                                        Task assignments                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CATEGORIZATION & LINKING                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LAYER 1: PRIMITIVE RULES (Auto)                                             │
│  • @bensley.com → Internal                                                   │
│  • Known contact mapping → Link to project                                   │
│  • Email from projects@ → Project-related                                    │
│                                                                              │
│  LAYER 2: AI SUGGESTIONS                                                     │
│  • Which project does this belong to?                                        │
│  • New person on thread → Suggest contact mapping                            │
│  • Sub-category within project (RFI, scheduling, etc.)                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUGGESTION → APPROVE → LEARN                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  AI creates suggestion → Logged to file/DB                                   │
│  You review (daily/weekly) → Batch approve obvious ones                      │
│  Approved → Applied to DB + added to training examples                       │
│  Rejected → AI learns what not to do                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE (SQLite ~107MB)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CORE: emails, proposals, projects, contacts, meeting_transcripts, invoices │
│  LINKS: email_proposal_links, email_project_links, contact_project_mappings │
│  AI: ai_suggestions, email_learned_patterns, category_patterns              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack

| Layer | Technology | Port/Path |
|-------|------------|-----------|
| Database | SQLite | `database/bensley_master.db` |
| Backend | FastAPI (Python) | 8000 |
| Frontend | Next.js 15 | 3002 |
| AI | OpenAI GPT-4o-mini | API |
| Transcription | OpenAI Whisper | API |

**CRITICAL - Database Path:**
```python
db_path = os.getenv("DATABASE_PATH", "database/bensley_master.db")
```
Never hardcode paths.

---

## 3. Email Pipeline

```
IMAP Server (tmail.bensley.com)
       ↓
email_importer.py
       ↓
emails table (full body, attachments, sender, receiver, thread)
       ↓
Layer 1: Primitive categorization (auto-rules)
       ↓
Layer 2: AI analysis (GPT) → Creates SUGGESTION
       ↓
suggestion_writer.py → ai_suggestions table
       ↓
You review suggestions
       ↓
✅ Approve → Handler applies change
❌ Reject → Pattern stored for learning
✏️ Correct → Updated pattern stored
```

### Key Services
| Service | Purpose |
|---------|---------|
| `email_importer.py` | IMAP email import |
| `context_bundler.py` | Build GPT context |
| `gpt_suggestion_analyzer.py` | GPT-4o-mini analysis |
| `suggestion_writer.py` | Write to ai_suggestions |
| `learning_service.py` | Pattern learning |

---

## 4. Voice/Meeting Pipeline

```
CURRENT (Your Mac):
Voice Memos folder → transcriber.py watches → Whisper → GPT summary → DB + email

PLANNED (Team-wide):
Browser app → Click record → Fill form (project, attendees) → Submit
       ↓
Audio saves to shared OneDrive
       ↓
Script on your Mac watches OneDrive folder
       ↓
Whisper API → transcript
       ↓
GPT → summary with context
       ↓
meeting_transcripts table
       ↓
Email sent to attendees

ALSO SUPPORTS:
Upload existing audio file + metadata for retrospective meetings
```

### All Linked Together
- Audio file path stored
- Transcript linked to audio
- Summary linked to transcript
- All linked to project
- Can always trace back: summary → transcript → audio

---

## 5. Email Channels Design

| Channel | Content | AI Behavior |
|---------|---------|-------------|
| `lukas@` | Proposals, BD | Link to proposals |
| `projects@` | Client correspondence | Link to projects (PMs CC this) |
| `invoices@` | Payment tracking | Link to projects + invoices |
| `dailywork@` | Staff daily work | Store, extract project if mentioned |
| `scheduling@` | PM coordination | Internal category |
| `bill@` | Bill's inbox | Various categories |

### Adding New Account
1. Create email account
2. Add to `.env`:
```bash
EMAIL_USERNAME_2=projects@bensley.com
EMAIL_PASSWORD_2=xxx
```
3. Update sync script to handle multiple accounts
4. Run sync

---

## 6. Database Schema

### Core Tables
| Table | Records | Purpose |
|-------|---------|---------|
| emails | 3,879 | All imported emails |
| proposals | 108 | Pre-contract opportunities |
| projects | 67 | Active contracts |
| contacts | 467 | All contacts |
| meeting_transcripts | 12 | Voice recordings |
| invoices | 436 | Invoice tracking |
| staff | 100 | Staff directory (95 Design, 5 Leadership) |
| contract_phases | 15 | Project phases with fees |
| schedule_entries | 1,120 | Daily staff assignments |

### Link Tables
| Table | Records | Purpose |
|-------|---------|---------|
| email_proposal_links | 2,095 | Email → Proposal |
| email_project_links | 519 | Email → Project |
| contact_project_mappings | 150 | Contact → Project + Role |

### AI Tables
| Table | Purpose |
|-------|---------|
| ai_suggestions | Pending/processed suggestions |
| email_learned_patterns | Sender→project patterns (153 patterns) |
| category_patterns | Category-specific patterns |

### Project Management Tables (New - Dec 2025)
| Table | Purpose |
|-------|---------|
| project_pm_history | Track PM assignment changes on projects |
| daily_work | Staff daily work for Bill/Brian review |
| client_submissions | Track deliverables sent to clients |

```sql
-- PM assignment on projects
projects.pm_staff_id INTEGER REFERENCES staff(staff_id)

-- PM history tracking
project_pm_history (
    history_id, project_id, pm_staff_id,
    assigned_date, removed_date, notes
)

-- Daily work for Bill/Brian review
daily_work (
    staff_id, project_code, work_date,
    description, task_type, discipline, phase,
    hours_spent, attachments,
    reviewer_id, review_status, review_comments
)

-- Client submissions tracking
client_submissions (
    project_code, phase_id, discipline, phase_name,
    submission_type, title, revision_number,
    submitted_date, files, status,
    client_feedback, feedback_date,
    linked_invoice_id
)
```

---

## 7. Suggestion Handler System

Located in: `backend/services/suggestion_handlers/`

| Handler | Type | Action |
|---------|------|--------|
| `email_link_handler.py` | `email_link` | Links email to proposal |
| `link_review_handler.py` | `link_review` | Reviews AI-suggested links |
| `transcript_handler.py` | `transcript_link` | Links transcript to proposal |
| `status_handler.py` | `proposal_status_update` | Updates proposal status |
| `contact_handler.py` | `new_contact` | Creates contact record |
| `contact_link_handler.py` | `contact_link` | Links contact to project |
| `fee_handler.py` | `fee_change` | Updates proposal fee |
| `deadline_handler.py` | `deadline_detected` | Creates deadline task |
| `info_handler.py` | `info` | Non-actionable info |
| `follow_up_handler.py` | `follow_up_needed` | Creates follow-up task |

### Handler Pattern
```python
def validate(suggestion) → bool
def preview(suggestion) → dict
def apply(suggestion) → result
def rollback(suggestion) → bool
```

---

## 8. Pattern Learning System

### Pattern Types (11)
| Type | Target |
|------|--------|
| sender_to_project | project |
| domain_to_project | project |
| keyword_to_project | project |
| sender_to_proposal | proposal |
| sender_to_internal | internal category |
| domain_to_internal | internal category |
| sender_to_skip | skip (spam) |
| domain_to_skip | skip |
| project_redirect | redirect old→new code |
| thread_to_project | entire thread |
| thread_to_proposal | entire thread |

### Confidence Scoring
| Pattern Type | Confidence |
|--------------|------------|
| Sender match | 0.75 |
| Domain match | 0.65 |
| Keyword match | 0.90 |

---

## 9. Backend Structure

```
backend/
├── api/
│   ├── main.py           # App init
│   ├── dependencies.py   # DB_PATH, shared deps
│   ├── models.py         # Pydantic models
│   └── routers/          # 28 router files
├── services/             # 60+ service files
│   └── suggestion_handlers/  # 10 handlers
├── core/                 # Utilities
└── utils/                # Logging
```

### Key Routers
| Router | Purpose |
|--------|---------|
| proposals.py | Bill's #1 priority |
| projects.py | Active contracts + phase management |
| emails.py | Search, scan, review queue |
| suggestions.py | AI suggestions |
| admin.py | Run pipelines |
| learning.py | AI learning |

### Project Management Endpoints (New)
| Endpoint | Purpose |
|----------|---------|
| `GET /projects/{code}/phases` | Phase status for progress visualization |
| `GET /proposals/{code}/conversation` | iMessage-style email thread |

### Email Review Queue (Learning Loop)
| Endpoint | Purpose |
|----------|---------|
| `GET /api/emails/review-queue` | Get emails with pending suggestions |
| `POST /api/emails/{id}/quick-approve` | Approve suggestion, learn pattern |
| `POST /api/emails/bulk-approve` | Bulk approve multiple emails |

Frontend: `/emails/review` - UI for bulk selection and approval

---

## 10. Frontend Structure

### Key Pages
| Route | Purpose |
|-------|---------|
| `/` | Dashboard |
| `/proposals` | Proposal list |
| `/projects` | Project list |
| `/projects/[code]` | Project detail |
| `/emails/review` | Email review queue (learning loop) |
| `/admin/suggestions` | Review suggestions |

### Key Components
| Location | Purpose |
|----------|---------|
| `components/dashboard/` | Dashboard widgets |
| `components/suggestions/` | Suggestion UI |
| `components/project/` | Project views |
| `components/project/phase-progress-bar.tsx` | Visual Concept→SD→DD→CD→CA pipeline |
| `components/project/project-card.tsx` | Project list card with phase progress |
| `components/proposals/conversation-view.tsx` | iMessage-style email display |

---

## 11. Environment Variables

```bash
DATABASE_PATH=database/bensley_master.db
EMAIL_USERNAME=lukas@bensley.com
EMAIL_PASSWORD=xxx
EMAIL_SERVER=tmail.bensley.com
EMAIL_PORT=993
OPENAI_API_KEY=sk-...
```

---

## 12. Run Commands

```bash
# Backend
cd backend && uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Email sync
python scripts/core/scheduled_email_sync.py

# Check health
curl http://localhost:8000/api/health
```

---

## 13. Future Architecture

### Meeting Recorder (Planned)
```
Browser App (hosted)
├── Click "Record" → browser requests mic permission
├── Recording happens in browser
├── Click "Stop"
├── Form: Project dropdown, Attendees, Notes
├── Submit → Audio POSTs to API or saves to OneDrive
└── Backend processes automatically
```

### Phase 3: Vector Store + MCP
```python
# MCP Tools (Claude queries DB directly)
@server.tool()
def search_emails(query, project_code): ...

@server.tool()
def get_project_context(project_code): ...
```

### Phase 5-6: Local AI
1. Local embeddings (stop sending to OpenAI)
2. Local LLM (Ollama) for simple tasks
3. Distillation (train on GPT outputs)
4. Bensley Model (fully local)
