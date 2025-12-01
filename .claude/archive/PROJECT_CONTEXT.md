# BDS Operations Platform - Project Context

**Last Updated:** 2025-11-23
**Current Phase:** Phase 1 - Week 4 (Dashboard Build - 85% Complete)
**Status:** Operational - Both backend and frontend running

---

## 🎯 Project Mission

Build an AI-powered operations platform for Bensley Design Studios that:
- Tracks proposals (sales pipeline) and active projects (delivery)
- Provides real-time dashboards for business operations
- Enables natural language queries about projects, invoices, RFIs, schedules
- Automates data entry and categorization via AI

---

## ⚠️ CORE WORKING PRINCIPLES

### 1. **Always Question & Challenge**
- Don't blindly implement user requests
- Ask: "Does this make sense architecturally?"
- Challenge if request contradicts the master plan
- Suggest better alternatives if you see them
- Be analytical, not just a code generator

### 2. **Clean Data is Sacred**
- NO junk in the database
- NO unused files cluttering folders
- Every import script must validate data before inserting
- Remove duplicates, fix inconsistencies
- Document data quality issues, don't hide them

### 3. **Think Before You Code**
- Where does this data belong in the schema?
- Will this create technical debt?
- Does this align with the long-term architecture?
- Am I solving the real problem or a symptom?

### 4. **Always Debug & Test**
- NEVER write code and assume it works
- Test every script before marking complete
- Check edge cases (empty data, malformed input, duplicates)
- Validate database state after imports
- Log errors clearly, don't fail silently

### 5. **Balance Short-Term vs. Long-Term**
- Reference `COMPLETE_ARCHITECTURE_ASSESSMENT.md` for long-term vision
- Ask: "Is this a quick hack or a sustainable solution?"
- Prefer solutions that work now AND scale later
- Document technical debt explicitly
- Don't over-engineer for the future, but don't paint into corners

### 6. **Every Import Script Checklist:**
- [ ] Where does data go? (which table, which columns)
- [ ] Data validation (check for nulls, duplicates, malformed data)
- [ ] Provenance tracking (source_type, source_reference, created_by)
- [ ] Dry run mode (preview before committing)
- [ ] Error handling (what happens if import fails halfway?)
- [ ] Logging (record what was imported, what failed, why)
- [ ] Cleanup (remove temp files, don't leave cruft)
- [ ] Testing (run on sample data first, validate results)

---

## 📋 Master Plan Reference

**See:** `2_MONTH_MVP_PLAN.md` for complete 8-week breakdown
**See:** `COMPLETE_ARCHITECTURE_ASSESSMENT.md` for long-term vision vs. current state

### Three-Phase Rollout:

**PHASE 1 (Now - Mid-December): Dashboards + Data** - 8 weeks
- Week 1-2: Data foundation (email setup, accounting integration, historical import)
- Week 3-4: Proposal Dashboard (sales pipeline)
- Week 5-6: Active Projects Dashboard (operations)
- Week 7-8: Polish, testing, deployment

**PHASE 2 (December/January): Intelligence Layer** - 4-6 weeks
- Natural language query interface
- Vector store / RAG setup
- Local LLM (Ollama + Llama)
- Model distillation pipeline

**PHASE 3 (February+): Multi-User Frontend** - TBD
- Authentication & user management
- Role-based permissions (4 roles)
- Different UI per role

---

## 🔑 Key Architectural Decisions

### Proposals vs. Projects (CRITICAL DISTINCTION!)

| Aspect | Proposals | Active Projects |
|--------|-----------|----------------|
| **Status** | Pre-contract, sales pipeline | Won contracts, under execution |
| **Focus** | Win the work | Deliver on time & budget |
| **Tracks** | Health, follow-ups, status | Payments, schedules, RFIs |
| **Data** | proposal_health, proposal_timeline | invoices, milestones, rfis |
| **Owner** | Bill (Business Development) | Project Managers |
| **Dashboard** | /dashboard/proposals | /dashboard/projects |

### Technology Stack

**Backend (Already 90% Built!):**
- ✅ FastAPI with 93+ REST endpoints
- ✅ SQLite database (complete schema with provenance)
- ✅ Claude API integration for AI
- ✅ Email importer (IMAP)
- ✅ Autonomous email categorization

**Frontend (✅ BUILT - Operational at http://localhost:3002):**
- ✅ Next.js 15.1.3 (App Router)
- ✅ UI: shadcn/ui (40+ components)
- ✅ State: TanStack Query (React Query v5)
- ✅ Styling: Tailwind CSS
- ✅ Charts: Recharts
- ✅ TypeScript with full type safety

**Deployment (Phase 1):**
- Backend: Local Mac (port 8000)
- Frontend: Local dev (port 3002)
- Database: SQLite file-based
- Later: Production Mac Mini server

### Why SQLite Not PostgreSQL (For Now)

✅ **Keep SQLite until:**
- Database exceeds 10GB (currently <1GB)
- Multiple agents need concurrent writes
- Scaling beyond 500 projects
- Setting up production deployment

**Migration effort when needed:** 2-3 days

### Why No RAG/Local LLM Yet

✅ **Defer to Phase 2 because:**
- Claude API works fine for MVP ($50-200/month)
- RAG adds 3-4 weeks of work
- Need complete data first to generate embeddings
- Better to prove value with cloud API, then optimize

---

## 📊 Current System State

### Live Application (✅ OPERATIONAL)
- **Frontend Dashboard:** http://localhost:3002 (Next.js 15)
- **Backend API:** http://localhost:8000 (FastAPI)
- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Database:** database/bensley_master.db (SQLite)

### Real Data Metrics (As of Nov 23, 2025)
- **87 proposals** tracked in proposal_tracker
- **369 emails** AI-processed and categorized
- **852 documents** indexed
- **13 status history** entries tracking proposal changes
- **023 database migrations** applied successfully
- **74 performance indexes** optimized for queries

### Database Schema (Complete)
- ✅ **Operational schemas** (95%): projects, proposals, contracts, invoices, clients, etc.
- ✅ **Intelligence schemas** (90%): ai_suggestions, training_data, learned_patterns, etc.
- ✅ **Relationship schemas** (100%): email_project_links, project_contact_links, etc.

**Total Tables:** 56+ (see `COMPLETE_ARCHITECTURE_ASSESSMENT.md` for full breakdown)

### API Endpoints (93+ endpoints - EXCEEDS vision!)
- ✅ Proposals (16 endpoints)
- ✅ Projects (12 endpoints)
- ✅ Invoices (5 endpoints)
- ✅ RFIs (2 endpoints)
- ✅ Intelligence (10 endpoints)
- ✅ Query/Search (9 endpoints)
- ✅ Audit (6 endpoints)
- ✅ And more...

**Location:** `backend/api/main.py` (4000+ lines - VERY LARGE FILE)

### Data Import Status
- ✅ Proposals.xlsx imported (87 proposals)
- ✅ MASTER_CONTRACT_FEE_BREAKDOWN.xlsx imported
- ✅ Proposal tracking dates imported
- ✅ Contract parsing working (parse_contracts.py)
- ✅ Email history imported (369 emails AI-processed)
- ✅ Documents indexed (852 documents)
- ⏳ Accounting Excel (pending from finance team)
- ⏳ Contract/Invoice PDFs (pending - need to backfill)

---

## 🎉 Recent Progress (Nov 21-23, 2025)

### Week 3-4 Accomplishments

**✅ November 23:**
- Fixed proposal tracker dropdown bug (useEffect pattern in proposal-quick-edit-dialog.tsx)
- Created conversation export tool for LLM training (export_conversations.py)
- Exported 2,119 messages from 49 conversation files in 3 formats (ShareGPT, raw, alpaca)
- Added training/ directory to .gitignore for privacy
- Updated README.md to reflect current operational state
- Created CURRENT_STATUS.md for quick reference
- Created FRONTEND_GUIDE.md for frontend development
- Verified provenance tracking (partial implementation - status history ✅, emails ✅, proposals needs work)
- Committed and pushed all changes to GitHub

**✅ November 22:**
- Implemented proposal tracker dashboard with full CRUD operations
- Built status timeline component showing proposal history
- Created email intelligence panel showing AI categorization
- Quick edit dialog with inline proposal updates

**✅ November 21:**
- Created proposal_tracker_service.py backend service
- Added database migrations 018-023
- Integrated financial metrics APIs
- Set up proposal status history tracking

---

## 🎯 Current Focus (Week 4-5)

### Immediate Priorities:
1. [ ] Complete financial dashboard widgets
2. [ ] Add invoice aging visualization
3. [ ] Implement cash flow forecast charts
4. [ ] Test with real user workflows
5. [ ] Improve historical data quality (email categorization)

### Phase 1 Completion Goals (Next 2-3 Weeks):
1. [ ] Complete Active Projects dashboard
2. [ ] Add RFI tracking interface
3. [ ] Meeting notes integration
4. [ ] Complete provenance tracking implementation
5. [ ] Production deployment preparation

### Known Issues to Address:
- ⚠️ Provenance tracking incomplete:
  - ✅ proposal_tracker_status_history working (13 entries)
  - ✅ emails.source_type working (395 entries)
  - ❌ audit_log table empty (no triggers/writes)
  - ❌ proposal_tracker missing created_by/source_type fields
- ⚠️ Email categorization needs improvement (historical data quality)
- ⚠️ Need to backfill contract/invoice PDFs when available

---

## 📂 Key Files & Documentation

### Quick Reference (START HERE):
- `CURRENT_STATUS.md` - ⭐ **CHECK THIS FIRST** - Real-time system status, URLs, recent changes
- `README.md` - Project overview, tech stack, quick start guide
- `FRONTEND_GUIDE.md` - Complete frontend development guide (Next.js, React, TypeScript)

### Planning Documents:
- `2_MONTH_MVP_PLAN.md` - Detailed 8-week plan (current roadmap)
- `COMPLETE_ARCHITECTURE_ASSESSMENT.md` - **CRITICAL** - Architecture analysis (vision vs. reality, 815 lines)
- `ARCHITECTURE_ASSESSMENT.md` - Earlier assessment (database intelligence plan)
- `PROVENANCE_TRACKING_IMPLEMENTATION.md` - Data provenance system docs

### Database:
- `database/bensley_master.db` - SQLite database (main data store)
- `database/migrations/*.sql` - Database migrations (020 migrations exist)
- `database/schema/` - Schema documentation (if exists)

### Backend Implementation:
- `backend/api/main.py` - FastAPI with 100+ endpoints (4500+ lines - BE CAREFUL)
- `backend/services/*.py` - Service layer (15+ services including proposal_tracker_service.py)
- `parse_contracts.py` - AI contract parser (Claude-powered)
- `smart_email_matcher.py` - Email-to-project linking
- `ai_email_processor.py` - Email categorization

### LLM Training:
- `export_conversations.py` - Export Claude Code conversations for local LLM training
- `training/` - Exported conversation data (2,119 messages from 49 files)
- `training/README.md` - Guide for training local models (Llama, Mistral, etc.)

### Import Scripts (Reference These!):
- `import_proposal_tracking_dates.py` - Example with provenance ✅
- `import_contract_fee_breakdown.py` - Example with provenance ✅
- `parse_contracts.py` - Example AI import ✅

### Frontend Structure (✅ BUILT):
- `frontend/src/app/(dashboard)/page.tsx` - Main dashboard (operational)
- `frontend/src/app/(dashboard)/tracker/page.tsx` - ✅ Proposal Tracker (fully functional)
- `frontend/src/app/(dashboard)/projects/page.tsx` - Active Projects (in progress)
- `frontend/src/components/proposals/proposal-quick-edit-dialog.tsx` - ✅ Inline editing
- `frontend/src/components/proposals/proposal-table.tsx` - ✅ Proposal listing
- `frontend/src/components/proposals/status-timeline.tsx` - ✅ Status history
- `frontend/src/components/ui/*` - ✅ 40+ shadcn/ui components
- `frontend/src/lib/api.ts` - ✅ API client (100+ endpoints)
- `frontend/src/lib/types.ts` - ✅ TypeScript type definitions

---

## 🚨 Common Pitfalls to Avoid

### 1. **Don't Confuse Proposals with Projects**
- Proposals = sales pipeline (pre-contract)
- Projects = active contracts (post-win)
- Different dashboards, different data, different workflows

### 2. **React State Management - Infinite Re-render Loops**
❌ **Bad:** Setting state directly in component body
```typescript
const [formData, setFormData] = useState({...});

// This runs on EVERY render, causing infinite loop!
if (proposal) {
  setFormData({ status: proposal.status });
}
```

✅ **Good:** Use useEffect with dependency array
```typescript
const [formData, setFormData] = useState({...});

useEffect(() => {
  if (proposal) {
    setFormData({ status: proposal.status });
  }
}, [proposal?.id]); // Only update when proposal ID changes
```

**Reference:** See `frontend/src/components/proposals/proposal-quick-edit-dialog.tsx:56-67` for the fix that resolved the dropdown bug (Nov 23, 2025)

### 3. **Don't Create Data Chaos**
❌ **Bad:**
```python
# Just dump data in without validation
cursor.execute("INSERT INTO invoices VALUES (?)", (data,))
```

✅ **Good:**
```python
# Validate, check duplicates, add provenance
if not invoice_number:
    log_error("Missing invoice number")
    return False

# Check for duplicate
existing = cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,)).fetchone()
if existing:
    log_warning(f"Invoice {invoice_number} already exists, skipping")
    return False

# Insert with provenance
cursor.execute("""
    INSERT INTO invoices (invoice_number, amount, source_type, source_reference, created_by)
    VALUES (?, ?, 'import', 'accounting_excel_2025-11-19', 'accounting_import')
""", (invoice_number, amount))
```

### 4. **Don't Assume Code Works - TEST IT**
After every script:
- Run it on test data first
- Check database: `sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM table"`
- Validate data quality: Look for nulls, duplicates, malformed entries
- Check provenance: `SELECT source_type, COUNT(*) FROM table GROUP BY source_type`

### 5. **Don't Ignore the Long-Term Architecture**
Before implementing a quick fix, ask:
- Does this align with `COMPLETE_ARCHITECTURE_ASSESSMENT.md`?
- Am I creating technical debt?
- Will this need to be rewritten in Phase 2/3?
- Is there a slightly longer solution that's more sustainable?

### 6. **Don't Wait for Perfect Data**
- Ship with 80% complete data
- Backfill missing PDFs later
- Focus on dashboards showing REAL value
- Don't get bogged down in data archeology for historical edge cases

### 7. **Don't Leave Cruft Behind**
After imports:
- Delete temp files
- Remove test data from database
- Clean up unused scripts
- Document what you did in SESSION_LOGS.md or similar

---

## ✅ Success Metrics

### End of Phase 1 (8 weeks):
- ✅ Proposal Dashboard shows accurate pipeline data
- ✅ Projects Dashboard shows real-time invoice/schedule status
- ✅ Bill uses dashboards daily (replaces Excel + email search)
- ✅ Saves 5-10 hours/week in manual tracking
- ✅ <5% data quality issues (measure this!)
- ✅ <2 second page load times
- ✅ Zero critical bugs
- ✅ Database is clean (no duplicate/junk data)

### End of Phase 2 (4-6 weeks):
- ✅ Query interface works for 80% of common questions
- ✅ Local LLM running (80% of queries)
- ✅ RAG/vector search operational
- ✅ Training pipeline collecting data

### End of Phase 3 (TBD):
- ✅ Multi-user authentication working
- ✅ 4 user roles with correct permissions
- ✅ Team uses platform daily
- ✅ Production deployment on Mac Mini

---

## 🔧 Decision Framework

### When User Requests Something New:

**Step 1: Question It**
- "Does this align with the 8-week plan?"
- "Is this critical for Phase 1 or can it wait?"
- "Is this solving the real problem?"

**Step 2: Check Architecture**
- Consult `COMPLETE_ARCHITECTURE_ASSESSMENT.md`
- Does it fit the operational/intelligence/relationship schema model?
- Does it create technical debt?

**Step 3: Propose Alternatives**
- "Instead of X, what about Y because..."
- "This works for now, but in Phase 2 we should..."
- "Let me validate this idea against the master plan first"

**Step 4: If Implementing, Do It Right**
- Clean data validation
- Provenance tracking
- Error handling
- Testing
- Documentation

---

## 🔄 How to Use This File

**At the start of EVERY session:**
1. Read this file to understand current phase and goals
2. Check `2_MONTH_MVP_PLAN.md` for this week's specific tasks
3. Review `COMPLETE_ARCHITECTURE_ASSESSMENT.md` for long-term context
4. Don't ask user to repeat context - it's all documented

**When user makes a request:**
1. Question if it makes sense (see Decision Framework)
2. Check against current phase goals
3. Propose approach WITH validation/testing plan
4. Implement with clean data principles
5. TEST before marking complete

**When creating import scripts:**
1. Follow "Every Import Script Checklist" above
2. Reference existing import scripts as examples
3. Validate data before inserting
4. Add provenance tracking
5. Test on sample data first
6. Document what you did

**When stuck or uncertain:**
- Check "Common Pitfalls to Avoid"
- Review success metrics to validate approach
- Challenge the approach - is there a better way?
- Ask user for clarification, but demonstrate you've thought it through

---

## 📞 Key Contacts & Roles

- **Bill Bensley** - Owner, Business Development (primary user, decision maker)
- **Finance Team** - Provides accounting data, invoices (currently slow/blocked)
- **Project Managers** - Will use Projects Dashboard (Phase 3 users)
- **Lukas** - Developer/You (building this system)

---

## 💡 Working Philosophy

**"Measure twice, cut once"**
- Think before coding
- Validate before committing
- Test before deploying
- Question before implementing

**"Clean data is the foundation"**
- Garbage in = garbage out
- No junk in database
- No unused cruft in folders
- Data quality is everyone's job

**"Balance pragmatism with vision"**
- Don't over-engineer for Phase 3 when in Phase 1
- But don't create technical debt that blocks Phase 2/3
- Reference the long-term architecture
- Ship value incrementally

**"Be a thinking partner, not a code monkey"**
- Challenge bad ideas (respectfully)
- Suggest better alternatives
- Explain tradeoffs
- Help user make informed decisions

---

**Remember:**
- We're building for the future, not perfectly reconstructing the past
- Ship with 80% data quality, iterate based on real usage
- Question everything, validate everything, test everything
- Clean data > quick hacks
