# Bensley Intelligence Platform - Dashboard Audit

## Executive Summary

**Status:** Frontend is live and styled correctly. Backend API exists but needs endpoints connected to actual database schema. We have rich data (87 proposals, 774 emails, 214 attachments) but dashboard shows zeros because API endpoints don't match database structure.

**Current State:**
- ✅ Frontend: http://localhost:3000 - Apple-style UI rendering correctly
- ✅ Backend API: http://localhost:8000 - Running but endpoints need updating
- ✅ Database: 87 proposals, 774 categorized emails, 214 attachments
- ❌ Dashboard: Showing all zeros - API/database schema mismatch

---

## Your Vision (From Previous Conversations)

### Ultimate Goal
> "An AI-powered operations system that knows everything about the business - emails, contracts, proposals, meetings, decisions. Answers questions instantly about any project or client. Generates documents intelligently based on historical context. Works locally with fine-tuned model trained on company data."

### Priority Features
1. **Proposal/Project Health Tracking** - See which deals need attention
2. **Email Intelligence** - Auto-categorize, link to projects, surface action items
3. **Document Repository** - Historical contracts (Ritz Carlton, etc.) for AI training
4. **Context-Aware Assistance** - AI that understands your business
5. **Agentic Features** (Future) - Automated follow-ups, smart routing

---

## Current Dashboard Components

### Hero Section
- **"Calm control over every proposal, email, and file"**
- Large background image (Golden Gate Bridge)
- Call-to-action buttons
- Project snapshot stats

### Metrics Cards (Currently showing 0s)
1. **Needs Reclassification** - Emails labeled "general" that need human review
2. **Training Progress** - 0/5,000 verified samples for AI
3. **Active Proposals** - Projects in motion this week
4. **Attachments Synced** - Ready for lookup

### Main Sections
1. **Top Uncategorized Emails** - Priority review queue
2. **Provide Context** - Leave guidance for Claude
3. **Proposal Tracker** - List of all proposals with search
4. **Proposal Details** - Phase, Win Probability, Last Contact, etc.

### Additional Cards
- Proposals overview
- Emails overview
- Documents overview

---

## Database Schema (Actual)

### Tables We Have:
```sql
-- proposals (87 records)
- proposal_id, project_code, project_name, client_name
- status, health_score, days_since_contact
- is_active_project, created_at, updated_at

-- emails (774 records)
- email_id, subject, sender_email, date, snippet, body_full

-- email_content (774 records)
- content_id, email_id, clean_body, category, subcategory
- importance_score, ai_summary, sentiment, entities

-- email_attachments (214 records)
- attachment_id, email_id, filename, filepath
- file_type, classification

-- email_proposal_links
- link_id, email_id, proposal_id, confidence_score

-- contracts
- contract_id, proposal_id, filename, filepath, signed_date

-- training_data
- task_type, input_data, output_data, model_used, human_verified
```

---

## What's Broken & How to Fix

### Problem 1: API Uses Wrong Table Names
**Current:** API queries `projects` table
**Actual:** Database has `proposals` table
**Fix:** Update API endpoints to use correct schema

### Problem 2: Missing API Endpoints
**Dashboard Needs:**
- `GET /api/dashboard/stats` - Overall metrics
- `GET /api/proposals` - List proposals with pagination
- `GET /api/proposals/{id}` - Single proposal details
- `GET /api/emails` - List emails with filters
- `GET /api/emails/uncategorized` - Priority review queue
- `GET /api/training/stats` - Training data progress

**Currently Have:**
- `GET /health` - Works
- `GET /metrics` - Queries wrong tables
- `GET /projects` - Should be `/proposals`
- `GET /emails` - Exists but may need updating

### Problem 3: Frontend API Calls
**Current:** Frontend calls `/api/proposals` but gets 404
**Fix:** Update backend.api.main.py to:
1. Rename `projects` → `proposals` throughout
2. Add missing endpoints for dashboard stats
3. Use ProposalService and EmailService classes

---

## Data We Can Show RIGHT NOW

### Available Metrics:
```python
# From proposals table
Total Proposals: 87
Active Projects: COUNT WHERE is_active_project=1
Health Issues: COUNT WHERE health_score < 0.5
Days Since Contact: AVG(days_since_contact)

# From emails table
Total Emails: 774
Categorized: 774 (100%)
By Category: GROUP BY category
Needing Review: COUNT WHERE category='general'
Unprocessed: 0 (all categorized!)

# From email_attachments
Total Attachments: 214
By Type: GROUP BY file_type
Contracts: COUNT WHERE classification='contract'

# From training_data
Human Verified Samples: COUNT WHERE human_verified=1
Training Progress: (verified / 5000) * 100
```

### Sample Proposal Data:
```sql
SELECT project_code, project_name, status, health_score, days_since_contact
FROM proposals
ORDER BY days_since_contact DESC
LIMIT 5
```

---

## Quick Win Action Items

### Priority 1: Connect API to Database (30 mins)
1. Update `backend/api/main.py`:
   - Change all `projects` → `proposals`
   - Import ProposalService and EmailService
   - Add dashboard stats endpoint

2. Test endpoints:
   ```bash
   curl http://localhost:8000/api/proposals
   curl http://localhost:8000/api/dashboard/stats
   ```

### Priority 2: Feed Dashboard with Real Data (15 mins)
1. Update frontend API calls to match new endpoints
2. Refresh dashboard - should show:
   - 87 proposals
   - 774 emails
   - 214 attachments
   - Real project health scores

### Priority 3: Enhanced Features (1-2 hours)
1. **Proposal Health Indicator** - Red/yellow/green based on `health_score`
2. **Email Review Queue** - Top 10 emails needing categorization
3. **Recent Activity Timeline** - Last emails, proposals updated
4. **Quick Search** - Find proposals/emails by keyword

---

## Dashboard Refinement Questions

### Data Display
1. **Should we show ALL 87 proposals or just active ones?**
2. **What date range for "Recent Activity"?** (Last 7 days? 30 days?)
3. **Health score thresholds?** (e.g., < 0.3 = Red, 0.3-0.7 = Yellow, > 0.7 = Green)
4. **Email priority sorting?** (By importance_score? By days since received?)

### Features
1. **Do you want inline editing?** (Update proposal status from dashboard)
2. **Bulk actions?** (Mark multiple emails as reviewed)
3. **Export functionality?** (Download proposal list as CSV)
4. **Notifications?** (Toast messages for new emails, proposals needing attention)

### UI Refinements
1. **Color scheme adjustment?** (Current purple primary - want to change?)
2. **More/less visual hierarchy?** (Bigger cards? More whitespace?)
3. **Mobile responsive priority?** (iPad? iPhone?)
4. **Dark mode support?** (CSS variables are ready)

---

## Historical Context Training

You mentioned having signed contracts (Ritz Carlton, etc.) on your PC. This is GOLD for AI training.

### What We Need:
1. **Contract PDFs** from accounting folder
2. **Proposal Documents** from past projects
3. **Scope of Work Documents** - Extractable patterns
4. **Fee Structures** - Training data for pricing intelligence

### How to Import:
```bash
# Run this when you're at your PC:
python3 scan_contracts_pc.py /path/to/accounting/folder
```

This will:
- Index all PDFs
- Extract text content
- Classify document types
- Store in `contracts` table
- Build training dataset for AI

---

## Next Steps

### Option A: Quick Data Connection (Recommended First)
1. I update the API endpoints to match database schema
2. Dashboard immediately shows real data
3. You review with Codex for UI refinements

### Option B: Feature Enhancement
1. Add specific features you want (which ones?)
2. Refine with Codex for perfect polish
3. Then connect data

### Option C: Historical Data Import
1. Connect to PC accounting folder
2. Import all historical contracts
3. Build AI training dataset
4. Then refine dashboard

**Which path do you want to take?**

---

## Technical Notes

### Frontend Stack
- Next.js 15.1.3 (stable, no Turbopack issues)
- React 19
- Tailwind CSS (properly configured)
- TanStack Query for data fetching
- Radix UI components

### Backend Stack
- FastAPI (Python)
- SQLite database
- Services: ProposalService, EmailService
- CORS configured for localhost:3000

### Running Services
```bash
# Frontend (already running)
cd frontend && npm run dev

# Backend API (already running)
cd .. && python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Summary

**We're 90% there!** The hard stuff (UI, styling, database, data import) is done. We just need to:

1. ✅ Fix API endpoint names (5 mins)
2. ✅ Connect frontend to backend (already done, just returns wrong data)
3. ✅ Watch dashboard light up with your 87 proposals and 774 emails

Then we can refine the UI with Codex to make it exactly what you want.

**Ready to connect the data?**
