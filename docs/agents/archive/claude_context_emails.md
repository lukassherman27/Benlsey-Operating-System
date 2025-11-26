# CLAUDE 1: EMAILS SYSTEM CONTEXT
**Role:** Email Infrastructure Specialist
**Priority:** CRITICAL (Others depend on your API)
**Estimated Time:** 6-8 hours

---

## 🎯 YOUR MISSION

You are building the **email system** that powers the entire Bensley Operations Platform. This is the most critical component because:

1. **3,356 emails** are already in the database and need a modern UI
2. **Project managers** need to see email threads linked to their projects
3. **Proposal team** needs email intelligence for follow-ups
4. **Overview dashboard** shows recent email activity

Your success unblocks Claude 3 (Projects) and Claude 4 (Proposals). Build the API first, then the UI.

---

## 🏗️ ARCHITECTURE CONTEXT

### How You Fit In The System

```
[EMAIL SERVER] → [Database (3,356 emails)] → [YOUR API] → [Frontend UI]
                                                    ↓
                                    [Claude 3: Projects feed]
                                    [Claude 4: Proposal intel]
                                    [Claude 5: Recent activity]
```

### What Others Need From You

**Claude 3 (Projects):**
- `GET /api/emails/project/{code}` - List emails for a project
- Email count, latest email date, unread indicators

**Claude 4 (Proposals):**
- `GET /api/emails/proposal/{id}` - List emails for a proposal
- Email linking confidence scores, evidence snippets

**Claude 5 (Overview):**
- `GET /api/emails/recent` - Latest 10 emails across all projects
- Quick summary: subject, sender, date, project

---

## 📚 FILES TO READ FIRST

### Must Read (Priority Order)
1. `BENSLEY_OPERATIONS_PLATFORM_FORWARD_PLAN.md` - Full system vision
2. `COORDINATION_MASTER.md` - Your role in parallel execution
3. `backend/api/main.py` (lines 1-100) - Existing API structure
4. `backend/services/email_processor.py` - Email business logic
5. `database/bensley_master.db` - Check `emails` table schema
6. `frontend/src/lib/types.ts` - Email TypeScript types
7. `frontend/src/lib/api.ts` - How to add API functions

### Database Schema (emails table)
```sql
CREATE TABLE emails (
    email_id INTEGER PRIMARY KEY,
    message_id TEXT UNIQUE,
    subject TEXT,
    sender TEXT,
    recipient TEXT,
    date TEXT,
    date_normalized DATE,
    body TEXT,
    category TEXT,  -- 'proposal', 'contract', 'rfi', 'general'
    project_code TEXT,
    proposal_id INTEGER,
    is_read BOOLEAN DEFAULT 0,
    importance INTEGER DEFAULT 0
);

CREATE TABLE email_proposal_links (
    link_id INTEGER PRIMARY KEY,
    email_id INTEGER,
    proposal_id INTEGER,
    confidence_score REAL,
    link_type TEXT,  -- 'auto', 'manual'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🛠️ FILES TO CREATE/MODIFY

### Backend (Priority 1)

#### 1. `backend/services/email_service.py` (NEW FILE)
Create comprehensive email service with:
```python
class EmailService:
    def get_emails(self, filters: dict, limit: int, offset: int)
    def get_email_by_id(self, email_id: int)
    def get_emails_by_project(self, project_code: str)
    def get_emails_by_proposal(self, proposal_id: int)
    def mark_as_read(self, email_id: int)
    def link_to_project(self, email_id: int, project_code: str, confidence: float)
    def search_emails(self, query: str)
```

#### 2. `backend/api/main.py` (ADD ENDPOINTS)
Add after line 464 (where other endpoints are):
```python
# Email Management Endpoints
@app.get("/api/emails")
async def get_emails(
    category: Optional[str] = None,
    project_code: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
)

@app.get("/api/emails/{email_id}")
async def get_email(email_id: int)

@app.get("/api/emails/project/{project_code}")
async def get_project_emails(project_code: str, limit: int = 20)

@app.get("/api/emails/proposal/{proposal_id}")
async def get_proposal_emails(proposal_id: int)

@app.get("/api/emails/recent")
async def get_recent_emails(limit: int = 10)

@app.post("/api/emails/{email_id}/read")
async def mark_email_read(email_id: int)

@app.post("/api/emails/{email_id}/link")
async def link_email_to_project(
    email_id: int,
    project_code: str,
    confidence: float = 1.0
)
```

### Frontend (Priority 2)

#### 3. `frontend/src/lib/api.ts` (ADD FUNCTIONS)
Add email API functions:
```typescript
  // Email Management
  getEmails: (filters?: {
    category?: string,
    project_code?: string,
    limit?: number,
    offset?: number
  }) => request<EmailsResponse>(`/api/emails${buildQueryString(filters)}`),

  getEmail: (id: number) => request<Email>(`/api/emails/${id}`),

  getProjectEmails: (projectCode: string, limit = 20) =>
    request<EmailsResponse>(`/api/emails/project/${projectCode}?limit=${limit}`),

  getRecentEmails: (limit = 10) =>
    request<EmailsResponse>(`/api/emails/recent?limit=${limit}`),

  markEmailRead: (id: number) =>
    request<{success: boolean}>(`/api/emails/${id}/read`, { method: 'POST' }),
```

#### 4. `frontend/src/app/(dashboard)/emails/page.tsx` (NEW FILE)
Full email management page with:
- Email list with filters (category, project, date range)
- Search bar (subject, sender, content)
- Email detail view (modal or split pane)
- Mark as read/unread
- Link to project functionality
- Pagination (50 per page)
- Category badges (Proposal, Contract, RFI, General)

#### 5. `frontend/src/components/emails/email-list.tsx` (NEW FILE)
Reusable email list component:
```typescript
interface EmailListProps {
  emails: Email[];
  onEmailClick: (email: Email) => void;
  onMarkRead?: (emailId: number) => void;
  showProject?: boolean;  // Show project code column
  compact?: boolean;      // Compact view for widgets
}
```

#### 6. `frontend/src/components/emails/email-detail-modal.tsx` (NEW FILE)
Email detail view with:
- Full email body (formatted)
- Thread history (if available)
- Project/proposal links
- Actions: Mark read, Link to project, Archive

---

## ✅ YOUR TASKS (Checklist)

### Phase 1: Backend API (Do This First!) ⚡
- [ ] Create `backend/services/email_service.py` with 7+ methods
- [ ] Add 7 email endpoints to `backend/api/main.py`
- [ ] Test all endpoints with curl/Postman
- [ ] Verify response formats match frontend types
- [ ] Document API contracts in comments
- [ ] **Signal Claude 3 & 4:** "Email API ready at /api/emails/*"

**Acceptance Criteria:**
- ✅ `curl http://localhost:8000/api/emails` returns email list
- ✅ `curl http://localhost:8000/api/emails/recent` returns 10 latest
- ✅ `curl http://localhost:8000/api/emails/project/BK-033` returns project emails
- ✅ Response time <200ms for list queries

### Phase 2: Frontend API Integration
- [ ] Add email API functions to `frontend/src/lib/api.ts`
- [ ] Test API calls from browser console
- [ ] Verify TypeScript types match API responses

### Phase 3: Email List Component
- [ ] Create `email-list.tsx` reusable component
- [ ] Support compact and full views
- [ ] Add loading and error states
- [ ] Add empty state ("No emails found")

### Phase 4: Email Page UI
- [ ] Create `/emails` page with filters
- [ ] Category filter (Proposal, Contract, RFI, General)
- [ ] Project filter (dropdown with all projects)
- [ ] Search bar (debounced, searches subject + sender + body)
- [ ] Pagination (50 per page, infinite scroll optional)
- [ ] Mark as read on click

### Phase 5: Email Detail View
- [ ] Create email detail modal/drawer
- [ ] Show full email body (formatted, preserve line breaks)
- [ ] Show sender, recipient, date, category
- [ ] Show linked project/proposal (if any)
- [ ] Action buttons: Mark read, Link to project

### Phase 6: Integration Test
- [ ] Test email list loads 3,356 emails
- [ ] Test filtering by category
- [ ] Test filtering by project
- [ ] Test search functionality
- [ ] Test mark as read
- [ ] Test linking email to project

---

## 🔗 DEPENDENCIES

### You Depend On
**Nothing!** You're the foundation. Start immediately.

### Others Depend On You
**CRITICAL - They're waiting for your API:**
- Claude 3 needs: `/api/emails/project/{code}` for project activity feed
- Claude 4 needs: `/api/emails/proposal/{id}` for proposal follow-ups
- Claude 5 needs: `/api/emails/recent` for dashboard widget

**Signal them when your API is ready** by updating COORDINATION_MASTER.md:
```markdown
### Claude 1: Emails System
**Status:** ✅ API Complete (UI in progress)
**Ready for:** Claude 3, Claude 4, Claude 5
**API Endpoints:** 7 endpoints tested and documented
```

---

## 📊 STATUS REPORTING

### When You Start
Update `COORDINATION_MASTER.md` → Claude 1 section:
```markdown
**Status:** 🔄 In Progress
**Progress:** 10%
**Last Update:** [timestamp]
**Current Task:** Creating backend/services/email_service.py
```

### When API is Ready (CRITICAL MILESTONE)
```markdown
**Status:** 🔄 In Progress (API ✅, UI in progress)
**Progress:** 50%
**Last Update:** [timestamp]
**Deliverables:**
- ✅ Email API (7 endpoints working)
- ✅ API tested with curl
- ⏳ Frontend UI in progress

**READY FOR:** Claude 3, Claude 4, Claude 5 can now integrate!
```

### When Blocked
```markdown
**Status:** ⛔ Blocked
**Blocked:** [describe issue]
**Last Update:** [timestamp]
**Need Help:** @Master Planning Claude
```

### When Complete
```markdown
**Status:** ✅ Complete
**Progress:** 100%
**Last Update:** [timestamp]
**Deliverables:**
- ✅ Email service with 7 methods
- ✅ 7 API endpoints tested
- ✅ Email list UI with filters
- ✅ Email detail modal
- ✅ Search functionality
- ✅ Mark as read/link to project

**Integration Tests:**
- ✅ Loads 3,356 emails successfully
- ✅ Filtering works correctly
- ✅ Search returns relevant results
- ✅ Claude 3 using project email API
- ✅ Claude 4 using proposal email API
- ✅ Claude 5 using recent emails API
```

---

## 🎨 UI/UX REQUIREMENTS

### Email List View
```
┌─────────────────────────────────────────────────────────────┐
│  Emails (3,356)              [Category ▼] [Project ▼] [🔍]  │
├─────────────────────────────────────────────────────────────┤
│  ⭐ RE: Ritz Carlton Bali Kickoff              [Proposal]   │
│     Ferry Maruf • Nov 24, 2025 • BK-033                     │
│     Meeting scheduled for July 24th...                      │
├─────────────────────────────────────────────────────────────┤
│  📧 Contract Revision Request                  [Contract]   │
│     Thippawan Thaviphoke • Nov 23, 2025 • BK-033           │
│     Please review the attached revisions...                 │
├─────────────────────────────────────────────────────────────┤
│  📄 Invoice I24-017 Payment Received           [General]    │
│     Finance Team • Nov 22, 2025 • BK-074                   │
│     Payment of $250,000 received...                         │
└─────────────────────────────────────────────────────────────┘
```

### Email Detail Modal
```
┌─────────────────────────────────────────────────────┐
│  RE: Ritz Carlton Bali Kickoff          [✕ Close]  │
├─────────────────────────────────────────────────────┤
│  From: Ferry Maruf <ferry.maruf@bdlbali.com>       │
│  To: bill@bensley.com                               │
│  Date: Nov 24, 2025 3:44 PM                         │
│  Project: BK-033 (Ritz Carlton Reserve Bali)       │
│  Category: 🟢 Proposal                              │
├─────────────────────────────────────────────────────┤
│  Dear Bill,                                         │
│                                                     │
│  We are pleased to invite you to the kickoff       │
│  meeting scheduled for July 24th, 2025...         │
│                                                     │
│  [Full email body with formatting preserved]       │
├─────────────────────────────────────────────────────┤
│  [Mark as Read] [Link to Project ▼] [Archive]      │
└─────────────────────────────────────────────────────┘
```

---

## 🧪 TESTING CHECKLIST

### API Tests (curl)
```bash
# Test email list
curl http://localhost:8000/api/emails

# Test category filter
curl http://localhost:8000/api/emails?category=proposal

# Test project emails
curl http://localhost:8000/api/emails/project/BK-033

# Test recent emails
curl http://localhost:8000/api/emails/recent

# Test mark as read
curl -X POST http://localhost:8000/api/emails/2024481/read
```

### Frontend Tests
- [ ] Email list renders without errors
- [ ] Filters update URL query params
- [ ] Search debounces (doesn't fire on every keystroke)
- [ ] Pagination loads more emails
- [ ] Email detail modal opens on click
- [ ] Mark as read updates UI immediately
- [ ] Linked projects show correct project name

---

## 💡 TECHNICAL NOTES

### Performance
- Email list should load <1 second
- Use pagination (50 per page) for large datasets
- Index on `date_normalized`, `category`, `project_code` in database
- Consider virtual scrolling if >1000 emails on page

### Security
- Email content may be sensitive - no XSS vulnerabilities
- Sanitize email body HTML before rendering
- Validate project codes before linking

### Error Handling
- Show friendly error if API fails
- Handle missing email gracefully
- Show "No emails found" for empty results
- Loading states for all async operations

---

## 🎯 SUCCESS METRICS

**You're successful when:**
1. ✅ All 7 API endpoints return correct data
2. ✅ Email list loads 3,356 emails in <1 second
3. ✅ Claude 3 successfully uses your project email API
4. ✅ Claude 4 successfully uses your proposal email API
5. ✅ Claude 5 successfully uses your recent emails API
6. ✅ Users can search, filter, and view emails easily
7. ✅ No console errors or warnings

**Impact:**
- Project managers see email activity on project pages
- Proposal team tracks follow-ups automatically
- Dashboard shows real-time email intelligence

---

## 🚀 READY TO START?

1. Read the "Must Read" files above
2. Update COORDINATION_MASTER.md with "In Progress"
3. Start with backend API (Phase 1)
4. Signal other Claudes when API is ready
5. Build frontend UI (Phase 2-5)
6. Test everything (Phase 6)
7. Mark complete in COORDINATION_MASTER.md

**Questions?** Ask Master Planning Claude in COORDINATION_MASTER.md

**Good luck! You're building the foundation of the entire system.** 🏗️
