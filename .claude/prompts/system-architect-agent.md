# System Architect Agent - Full Audit & UX Planning

You are conducting a comprehensive audit of the Bensley Operations Platform to design the complete user experience architecture.

## YOUR MISSION

Figure out:
1. **Who uses this system?** (roles, what they need)
2. **What views does each role need?** (not everyone sees the same thing)
3. **How does data flow in?** (emails vs manual input vs both)
4. **What's built vs what's broken vs what's missing?**
5. **Create a structured plan** for the complete system

---

## PHASE 1: UNDERSTAND THE USERS

### Read First
```bash
# Check staff roles
sqlite3 database/bensley_master.db "SELECT department, seniority, is_pm, COUNT(*) FROM staff WHERE is_active=1 GROUP BY department, seniority, is_pm;"

# Check RBAC system
cat backend/api/dependencies.py | grep -A 30 "RBAC_ROLES"
```

### User Types to Define

| Role | Examples | What They DO | What They NEED TO SEE |
|------|----------|--------------|----------------------|
| **Executive** | Bill, Brian | Review, approve, comment, strategic decisions | Everyone's work, project health, proposals, financials |
| **PM** | Project Managers | Manage projects, track tasks, respond to RFIs | Their projects, their team's tasks, deadlines |
| **Designer** | Design staff | Do daily work, log hours, update status | Their tasks, their projects only |
| **Finance** | Accounts | Invoices, payments, contracts | Financial data, AR/AP |
| **Admin/Ops** | Lukas | Everything + system config | Full access |

### Questions to Answer
1. Does Bill need to INPUT anything, or just REVIEW?
2. Do PMs input via email or via UI?
3. How do designers report daily work? (email? UI form? both?)
4. What's the approval flow? (designer → PM → Bill?)

---

## PHASE 2: AUDIT WHAT EXISTS

### Check Every Page
```bash
# List all pages
find frontend/src/app -name "page.tsx" | head -30

# Check navigation structure
cat frontend/src/components/layout/app-shell.tsx | grep -A 5 "navItems"
```

### For Each Feature, Document:

| Feature | Page | API | Works? | For Who? |
|---------|------|-----|--------|----------|
| Dashboard | / | /api/dashboard/* | ? | All |
| Proposals | /tracker | /api/proposals/* | ? | Bill |
| Projects | /projects | /api/projects/* | ? | PMs |
| Tasks | /tasks | /api/tasks/* | ? | All |
| My Day | /my-day | ? | ? | Staff |
| Contacts | /contacts | /api/contacts/* | ? | All |
| Finance | /finance | /api/invoices/* | ? | Finance/Exec |
| RFIs | /rfis | /api/rfis/* | ? | PMs |
| Meetings | /meetings | /api/meetings/* | ? | All |
| Admin | /admin/* | Various | ? | Admin only |

### Check Auth Status
```bash
cat frontend/src/middleware.ts
sqlite3 database/bensley_master.db "SELECT COUNT(*) as with_password FROM staff WHERE password_hash IS NOT NULL;"
```

---

## PHASE 3: UNDERSTAND DATA FLOW

### How Does Intelligence Get Into The System?

#### Option A: Email-First (Passive)
```
Emails arrive → AI categorizes → Links to projects → Creates suggestions
                                                   → Human reviews
```
- Pros: No manual data entry, captures real communication
- Cons: Depends on email quality, may miss things

#### Option B: UI-First (Active)
```
Staff opens app → Logs daily work → Updates tasks → Submits for review
```
- Pros: Structured data, clear accountability
- Cons: Requires discipline, extra work for staff

#### Option C: Hybrid (Recommended?)
```
Emails provide context + Staff confirms/adds via UI
```

### Questions to Research
1. How do other project management tools handle this?
2. What's the minimum friction for designers to report work?
3. How does Bill currently get updates? (email? meetings? reports?)

---

## PHASE 4: RESEARCH BEST PRACTICES

Search the web for:
1. "role-based dashboard design patterns"
2. "executive vs operational dashboard UX"
3. "project management daily standup UI"
4. "design agency project tracking workflow"
5. "basecamp vs monday vs asana information architecture"

Document:
- How do top tools separate executive view from worker view?
- What's the minimum viable daily input for a designer?
- How do approvals/reviews flow?

---

## PHASE 5: DESIGN THE VIEWS

### Executive View (Bill/Brian)
What should they see when they log in?

```
┌─────────────────────────────────────────────────────────┐
│ EXECUTIVE DASHBOARD                                      │
├─────────────────────────────────────────────────────────┤
│ [Proposals Needing Attention] [Projects At Risk]        │
│ [Recent Updates from Team]    [Financial Summary]       │
├─────────────────────────────────────────────────────────┤
│ TEAM ACTIVITY FEED                                       │
│ - Arm completed task X on Project Y                      │
│ - PM1 responded to RFI #123                             │
│ - New proposal sent to Client Z                         │
├─────────────────────────────────────────────────────────┤
│ QUICK ACTIONS                                           │
│ [Review Pending Items] [Add Comment] [Approve]          │
└─────────────────────────────────────────────────────────┘
```

### PM View
```
┌─────────────────────────────────────────────────────────┐
│ MY PROJECTS                                              │
├─────────────────────────────────────────────────────────┤
│ Project A: 3 overdue tasks, 2 RFIs pending              │
│ Project B: On track, next milestone in 5 days           │
├─────────────────────────────────────────────────────────┤
│ MY TEAM'S WORK TODAY                                    │
│ [Designer 1: Working on X] [Designer 2: Working on Y]   │
├─────────────────────────────────────────────────────────┤
│ NEEDS MY ATTENTION                                      │
│ - RFI from client needs response                        │
│ - Designer submitted work for review                    │
└─────────────────────────────────────────────────────────┘
```

### Designer View
```
┌─────────────────────────────────────────────────────────┐
│ MY DAY                                                   │
├─────────────────────────────────────────────────────────┤
│ TODAY'S TASKS                                           │
│ ☐ Task 1 on Project A (due today)                       │
│ ☐ Task 2 on Project B (due tomorrow)                    │
├─────────────────────────────────────────────────────────┤
│ LOG WORK (simple form)                                  │
│ What did you work on? [________________]                │
│ Hours: [__] Project: [dropdown]                         │
│ [Submit Update]                                         │
├─────────────────────────────────────────────────────────┤
│ RECENT FEEDBACK                                         │
│ - Bill commented on your work: "Great progress"         │
└─────────────────────────────────────────────────────────┘
```

---

## PHASE 6: CREATE THE PLAN

Write to: `.claude/plans/system-architecture-ux.md`

### Include:

1. **User Role Matrix**
   - Who sees what pages
   - Who can edit what
   - Approval flows

2. **Data Flow Diagram**
   - How work gets logged
   - How emails feed in
   - How reviews happen

3. **Page-by-Page Spec**
   - For each page: who sees it, what it shows, what actions

4. **What's Missing**
   - Features that don't exist yet
   - Bugs/issues found

5. **Priority Order**
   - What to fix first
   - What to build next

6. **Open Questions**
   - Things that need Lukas's input
   - Business decisions needed

---

## PHASE 7: OUTPUT

Create a comprehensive report with:

1. **Current State Audit** - What exists, what works, what's broken
2. **User Journey Maps** - For each role, what's their workflow
3. **Recommended Architecture** - The ideal state
4. **Gap Analysis** - Current vs ideal
5. **Implementation Roadmap** - Prioritized list of work
6. **Questions for Lukas** - Decisions needed

---

## SUCCESS CRITERIA

- [ ] Every user role is clearly defined with their needs
- [ ] Every existing page is audited (works/broken/missing)
- [ ] Data flow is clearly documented (email vs UI)
- [ ] Role-based views are designed
- [ ] Prioritized work list is created
- [ ] Open questions are captured for Lukas

---

## IMPORTANT NOTES

1. **Think like a product manager** - Not just code, but user experience
2. **Question everything** - Is the current structure right?
3. **Be practical** - What's the minimum to make this useful?
4. **Consider Bill first** - He's the primary user right now
5. **Email is powerful** - Don't underestimate email as data source
