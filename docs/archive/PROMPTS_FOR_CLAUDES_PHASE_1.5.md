# 🚀 Phase 1.5 Prompts for Each Claude
**Created:** November 25, 2025
**Context:** Critical bug fixes + Phase 1 completion
**Coordinator Note:** I'm handling main.py fixes separately - you focus on your tasks

---

## 📋 CLAUDE 4 (Proposals) - URGENT BUG FIXES

```
CRITICAL FIXES NEEDED - Phase 1.5 Week 1

Read PHASE_1.5_AND_2_TECHNICAL_PLAN.md Task 1.5.1 and 1.5.2

Your Tasks:
1. Fix "no such column: updated_by" error
2. Fix project names not showing in UI

Note: Coordinator is handling backend/api/main.py infrastructure fixes separately.

---

TASK 1: Fix Proposal Status Update Error

Problem: "no such column: updated_by" when saving proposal status

Steps:
1. Find the bug location
   ```bash
   cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
   find backend -name "*.py" -exec grep -n "updated_by\|updated_BY" {} +
   ```

2. Check database schema
   ```bash
   sqlite3 database/bensley_master.db ".schema proposals"
   sqlite3 database/bensley_master.db ".schema proposal_tracker"
   # Look for column name - should be "updated_by" (lowercase)
   ```

3. Likely culprits:
   - backend/services/proposal_tracker_service.py (SQL typo: updated_BY vs updated_by)
   - backend/api/main.py (Pydantic model field name)
   - frontend/src/app/(dashboard)/tracker/page.tsx (API request payload)

4. Test in browser
   - Open http://localhost:3002/tracker
   - Open DevTools → Network tab
   - Change a proposal status, click "Save Changes"
   - Copy EXACT request payload from Network tab
   - Report what you find

Report back with:
✅ Exact file and line number where bug was found
✅ What the bug was (typo, wrong field name, etc.)
✅ Screenshot of successful status update (no error)
✅ Console showing no errors

---

TASK 2: Fix Project Names Not Showing

Problem: "Project Name" column blank everywhere

Steps:
1. Test backend API
   ```bash
   curl http://localhost:8000/api/proposals | jq '.[0] | keys' | grep -i name
   # Should see BOTH "project_code" AND "project_name"
   ```

2. If project_name missing from API response:

   File: backend/services/proposal_tracker_service.py

   Find get_all_proposals() method and add project_name to SELECT:
   ```python
   cursor.execute("""
       SELECT
           project_code,
           project_name,  -- ADD THIS if missing
           status,
           project_value,
           client_company,
           # ... rest
       FROM proposals
       ORDER BY created_at DESC
   """)
   ```

3. Check if database has project_name values
   ```bash
   sqlite3 database/bensley_master.db "SELECT project_code, project_name FROM proposals LIMIT 10"
   ```

4. If project_name is NULL, populate from projects table:
   ```bash
   sqlite3 database/bensley_master.db "
   UPDATE proposals
   SET project_name = (
       SELECT name FROM projects
       WHERE projects.code = proposals.project_code
   )
   WHERE project_name IS NULL OR project_name = ''
   "
   ```

5. Verify frontend displays it

   File: frontend/src/app/(dashboard)/tracker/page.tsx

   ```typescript
   <TableCell>{proposal.project_name || proposal.project_code}</TableCell>
   ```

Report back with:
✅ curl output showing project_name in API response
✅ Screenshot of tracker page showing project names (not blank)
✅ Database query showing project_name populated
✅ All locations showing project names (tracker, widgets, detail pages)

---

Timeline: 1-2 hours total
Priority: 🔴 CRITICAL - blocking production use
```

---

## 📧 CLAUDE 1 (Emails) - WIDGET FIX

```
FIX RECENT EMAILS WIDGET - Phase 1.5 Week 1

Read PHASE_1.5_AND_2_TECHNICAL_PLAN.md Task 1.5.3

Your Task: Fix "Recent Emails" widget showing old emails with wrong dates

Note: Coordinator is handling backend/api/main.py infrastructure fixes separately.

---

Problem: Dashboard recent emails widget shows "super fucking old emails" from 2024

Steps:

1. Find the widget file
   ```bash
   find frontend/src/components -name "*recent*email*" -o -name "*email*widget*"
   ```

   Likely: frontend/src/components/dashboard/recent-emails-widget.tsx

2. Check if backend endpoint exists
   ```bash
   grep -n "/api/emails/recent" backend/api/main.py
   ```

3. If missing, create backend endpoint

   File: backend/api/main.py

   ```python
   @app.get("/api/emails/recent")
   def get_recent_emails(limit: int = 5):
       """Get most recent emails (last 30 days)"""
       conn = get_db_connection()
       cursor = conn.cursor()

       cursor.execute("""
           SELECT *
           FROM emails
           WHERE date_received >= date('now', '-30 days')
           ORDER BY date_received DESC
           LIMIT ?
       """, (limit,))

       columns = [desc[0] for desc in cursor.description]
       emails = []
       for row in cursor.fetchall():
           emails.append(dict(zip(columns, row)))

       conn.close()
       return emails
   ```

4. Fix frontend widget

   File: frontend/src/components/dashboard/recent-emails-widget.tsx

   ```typescript
   import { format } from 'date-fns'

   const { data: emails } = useQuery({
     queryKey: ['recent-emails'],
     queryFn: async () => {
       const response = await api.get('/api/emails/recent?limit=5')
       // Sort by date DESC (newest first)
       return response.sort((a, b) =>
         new Date(b.date_received).getTime() - new Date(a.date_received).getTime()
       ).slice(0, 5)
     },
     refetchInterval: 5 * 60 * 1000  // Refresh every 5 min
   })

   // Display with proper formatting
   {emails?.map(email => (
     <div key={email.email_id} className="flex justify-between items-start py-2 border-b">
       <div className="flex-1 min-w-0 mr-2">
         {/* Subject - truncated */}
         <p className="text-sm font-medium truncate" title={email.subject}>
           {email.subject}
         </p>
         {/* From - truncated */}
         <p className="text-xs text-muted-foreground truncate">
           {email.sender_email}
         </p>
       </div>
       {/* Date - formatted as "MMM d" */}
       <div className="text-xs text-muted-foreground whitespace-nowrap">
         {format(new Date(email.date_received), 'MMM d')}
       </div>
     </div>
   ))}
   ```

5. Test backend
   ```bash
   curl "http://localhost:8000/api/emails/recent?limit=5" | jq '.[0].date_received'
   # Should show recent date (within last 30 days)
   ```

6. Test in browser
   - Open http://localhost:3002
   - Check "Recent Emails" widget
   - Verify shows 5 most recent emails
   - Verify dates from this month (November 2025)
   - Verify subject lines don't overflow

Report back with:
✅ curl output showing recent dates (Nov 2025)
✅ Screenshot of widget with current emails
✅ Dates formatted as "Nov 25" not timestamps
✅ Subject lines truncate cleanly (no overflow)

---

Timeline: 45 minutes
Priority: 🟡 HIGH - dashboard looks unprofessional
```

---

## 🎯 CLAUDE 2 (RLHF) - FEEDBACK SYSTEM

```
IMPLEMENT PROPER RLHF FEEDBACK - Phase 1.5 Week 1

Read PHASE_1.5_AND_2_TECHNICAL_PLAN.md Task 1.5.4
Read FIX_RLHF_PROPERLY.md (complete implementation guide)

Your Task: Replace thumbs up/down with contextual feedback system

Note: Coordinator is handling backend/api/main.py infrastructure fixes separately.

---

Why This Matters (Stanford CS336):
- RLHF training requires RICH SIGNALS not binary feedback
- Need: issue type, explanation, expected vs actual values
- This creates training data for Phase 2 fine-tuning

Steps:

1. Update database schema
   ```bash
   sqlite3 database/bensley_master.db "
   ALTER TABLE training_data ADD COLUMN issue_type TEXT;
   ALTER TABLE training_data ADD COLUMN expected_value TEXT;
   ALTER TABLE training_data ADD COLUMN current_value TEXT;
   "

   # Verify columns added
   sqlite3 database/bensley_master.db ".schema training_data"
   ```

2. Update backend service

   File: backend/services/training_data_service.py

   Add new fields to log_feedback method (see FIX_RLHF_PROPERLY.md lines 54-104):
   ```python
   def log_feedback(
       self,
       feature_type: str,
       feature_id: str,
       helpful: bool,
       issue_type: Optional[str] = None,  # NEW
       feedback_text: str = None,         # REQUIRED for helpful=False
       expected_value: Optional[str] = None,  # NEW
       current_value: Optional[str] = None,   # NEW
       context: Optional[Dict] = None
   ):
       # CRITICAL: Require explanation for negative feedback
       if not helpful and not feedback_text:
           raise ValueError("feedback_text is REQUIRED when helpful=False")

       # ... rest of implementation from FIX_RLHF_PROPERLY.md
   ```

3. Replace frontend component

   File: frontend/src/components/ui/feedback-buttons.tsx

   REPLACE ENTIRE FILE with implementation from FIX_RLHF_PROPERLY.md (lines 120-411)

   Must include:
   - Thumbs up: simple click, logs helpful=true
   - Thumbs down: opens dialog with:
     - Issue type checkboxes (5 categories)
     - Required text explanation (textarea)
     - Optional expected value field
     - Shows current value
     - Submit disabled until text entered

4. Update API endpoint

   File: backend/api/main.py (find existing /api/feedback endpoint)

   Update Pydantic model to accept new fields:
   ```python
   class FeedbackRequest(BaseModel):
       feature_type: str
       feature_id: str
       helpful: bool
       issue_type: Optional[str] = None
       feedback_text: Optional[str] = None
       expected_value: Optional[str] = None
       current_value: Optional[str] = None
       context: Optional[Dict] = None
   ```

5. Test in browser

   Test negative feedback:
   - Open http://localhost:3002
   - Click thumbs down on any KPI widget
   - Dialog MUST appear with issue types, text area, expected value
   - Try to submit without text → should be disabled
   - Fill in text and submit → should succeed

   Verify in database:
   ```bash
   sqlite3 database/bensley_master.db "
   SELECT feature_type, issue_type, feedback_text, expected_value, current_value
   FROM training_data
   WHERE helpful = 0
   ORDER BY timestamp DESC
   LIMIT 5
   "
   ```

Report back with:
✅ Screenshot of feedback dialog (thumbs down clicked)
✅ Screenshot of filled dialog before submit
✅ Database query output showing captured context
✅ Confirmation text explanation is REQUIRED
✅ Example feedback logged with all fields

---

Timeline: 1.5 hours
Priority: 🔴 CRITICAL - needed for Phase 2 training
```

---

## 🏗️ CLAUDE 3 (Projects) - HIERARCHICAL VIEW

```
BUILD HIERARCHICAL PROJECT BREAKDOWN - Phase 1.5 Week 2

Read PHASE_1.5_AND_2_TECHNICAL_PLAN.md Task 1.5.5

Your Task: Create Project → Discipline → Phase → Invoice tree view

Note: Coordinator is handling backend/api/main.py infrastructure fixes separately.

---

User Request: "I want to see Project → Discipline → Phase → Invoices"

Data Structure:
```
Project: 25-BK-018 Mumbai Clubhouse ($2.5M)
├── Landscape ($800K)
│   ├── Mobilization ($50K)
│   │   ├── Invoice #001: $25K (Paid)
│   │   └── Invoice #002: $25K (Paid)
│   ├── Concept Design ($200K)
│   │   ├── Invoice #003: $100K (Paid 50%)
│   │   └── [Not yet invoiced]: $100K
│   ├── Design Development ($300K)
│   └── Construction Docs ($250K)
├── Interior Design ($1.2M)
└── Architecture ($500K)
```

Steps:

1. Check data availability
   ```bash
   sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM project_fee_breakdown"
   # Should show 372 rows (35 projects)

   sqlite3 database/bensley_master.db "
   SELECT discipline, phase, fee_amount
   FROM project_fee_breakdown
   WHERE project_code = '25-BK-018'
   ORDER BY discipline, phase_order
   LIMIT 10
   "
   ```

2. Create backend service method

   File: backend/services/project_service.py

   ```python
   def get_project_hierarchy(self, project_code: str):
       """Get hierarchical breakdown: Project → Discipline → Phase → Invoices"""
       conn = get_db_connection()
       cursor = conn.cursor()

       # Get fee breakdown
       cursor.execute("""
           SELECT
               discipline,
               phase,
               fee_amount,
               phase_order
           FROM project_fee_breakdown
           WHERE project_code = ?
           ORDER BY discipline, phase_order
       """, (project_code,))

       breakdown = cursor.fetchall()

       # Get invoices
       cursor.execute("""
           SELECT
               invoice_number,
               invoice_amount,
               paid_date,
               discipline,
               phase
           FROM invoices
           WHERE project_code = ?
       """, (project_code,))

       invoices = cursor.fetchall()

       # Build hierarchy tree
       hierarchy = self._build_hierarchy_tree(breakdown, invoices)

       conn.close()
       return hierarchy

   def _build_hierarchy_tree(self, breakdown, invoices):
       """Build nested tree structure"""
       tree = {}

       for row in breakdown:
           discipline = row['discipline']
           phase = row['phase']
           fee = row['fee_amount']

           if discipline not in tree:
               tree[discipline] = {'phases': {}, 'total_fee': 0}

           tree[discipline]['phases'][phase] = {
               'fee_amount': fee,
               'invoices': [],
               'invoiced': 0,
               'remaining': fee
           }
           tree[discipline]['total_fee'] += fee

       # Link invoices to phases
       for inv in invoices:
           discipline = inv['discipline']
           phase = inv['phase']
           if discipline in tree and phase in tree[discipline]['phases']:
               tree[discipline]['phases'][phase]['invoices'].append(inv)
               tree[discipline]['phases'][phase]['invoiced'] += inv['invoice_amount']
               tree[discipline]['phases'][phase]['remaining'] -= inv['invoice_amount']

       return tree
   ```

3. Create API endpoint

   File: backend/api/main.py

   ```python
   @app.get("/api/projects/{project_code}/hierarchy")
   def get_project_hierarchy(project_code: str):
       """Get hierarchical project breakdown"""
       project_service = ProjectService(DB_PATH)
       hierarchy = project_service.get_project_hierarchy(project_code)
       return hierarchy
   ```

4. Create frontend component

   File: frontend/src/components/projects/project-hierarchy-tree.tsx

   ```typescript
   export function ProjectHierarchyTree({ projectCode }: { projectCode: string }) {
     const { data: hierarchy } = useQuery({
       queryKey: ['project-hierarchy', projectCode],
       queryFn: () => api.get(`/api/projects/${projectCode}/hierarchy`)
     })

     return (
       <div className="project-hierarchy">
         {Object.entries(hierarchy || {}).map(([discipline, data]) => (
           <Collapsible key={discipline}>
             <CollapsibleTrigger>
               <h3>{discipline} - ${data.total_fee.toLocaleString()}</h3>
             </CollapsibleTrigger>

             <CollapsibleContent>
               {Object.entries(data.phases).map(([phase, phaseData]) => (
                 <div key={phase} className="phase">
                   <h4>{phase} - ${phaseData.fee_amount.toLocaleString()}</h4>

                   {/* Progress bar */}
                   <Progress value={(phaseData.invoiced / phaseData.fee_amount) * 100} />

                   {/* Invoices */}
                   <div className="invoices">
                     {phaseData.invoices.map(inv => (
                       <div key={inv.invoice_number}>
                         <Badge>{inv.invoice_number}</Badge>
                         ${inv.invoice_amount.toLocaleString()}
                         {inv.paid_date ? <Check className="text-green-600" /> : <Clock />}
                       </div>
                     ))}

                     {/* Remaining */}
                     {phaseData.remaining > 0 && (
                       <div className="text-muted-foreground">
                         Remaining: ${phaseData.remaining.toLocaleString()}
                       </div>
                     )}
                   </div>
                 </div>
               ))}
             </CollapsibleContent>
           </Collapsible>
         ))}
       </div>
     )
   }
   ```

5. Test
   ```bash
   # Test API
   curl http://localhost:8000/api/projects/25-BK-018/hierarchy | jq
   ```

   - Open http://localhost:3002/projects/25-BK-018
   - Verify hierarchy tree shows disciplines
   - Click to expand → shows phases
   - Click phase → shows invoices
   - Shows progress bars for each phase
   - Calculates remaining balance

Report back with:
✅ API response showing hierarchy structure
✅ Screenshot of collapsed view (disciplines only)
✅ Screenshot of expanded view (showing phases + invoices)
✅ Correct calculations (total fee, invoiced, remaining)
✅ All 35 projects work (not just one example)

---

Timeline: 3-4 hours
Priority: 🟡 HIGH - major user request
```

---

## 📊 CLAUDE 5 (Dashboard) - KPI TRENDS

```
ADD TREND INDICATORS TO ALL KPIs - Phase 1.5 Week 2

Read PHASE_1.5_AND_2_TECHNICAL_PLAN.md Task 1.5.6

Your Task: Add trend indicators (+8.2% style) to all KPI cards

Note: Coordinator is handling backend/api/main.py infrastructure fixes (Pydantic validators, error handling, CORS, etc.) separately. You focus on KPI trend logic.

---

User Feedback: "I love the trend indicators (+8.2%)"

Steps:

1. Update backend KPI service

   File: backend/services/dashboard_service.py (or create if missing)

   ```python
   from datetime import date, timedelta

   class DashboardService:
       def get_kpi_with_trends(self):
           """Get all KPIs with month-over-month trends"""

           # Current period (now)
           current_active_proposals = self._get_active_proposals_count()
           current_outstanding = self._get_outstanding_invoices_total()
           current_contract_value = self._get_remaining_contract_value()

           # Previous period (30 days ago)
           prev_active_proposals = self._get_active_proposals_count(
               as_of_date=date.today() - timedelta(days=30)
           )
           prev_outstanding = self._get_outstanding_invoices_total(
               as_of_date=date.today() - timedelta(days=30)
           )
           prev_contract_value = self._get_remaining_contract_value(
               as_of_date=date.today() - timedelta(days=30)
           )

           return {
               "active_proposals": {
                   "value": current_active_proposals,
                   "trend": self._calculate_trend(current_active_proposals, prev_active_proposals)
               },
               "outstanding_invoices": {
                   "value": current_outstanding,
                   "trend": self._calculate_trend(current_outstanding, prev_outstanding)
               },
               "remaining_contract_value": {
                   "value": current_contract_value,
                   "trend": self._calculate_trend(current_contract_value, prev_contract_value)
               }
           }

       def _calculate_trend(self, current: float, previous: float) -> dict:
           """Calculate trend percentage and direction"""
           if previous == 0:
               return {"value": 0, "direction": "neutral", "label": "N/A"}

           trend_pct = ((current - previous) / previous) * 100

           return {
               "value": round(trend_pct, 1),
               "direction": "up" if trend_pct > 0 else ("down" if trend_pct < 0 else "neutral"),
               "label": f"+{trend_pct:.1f}%" if trend_pct > 0 else f"{trend_pct:.1f}%"
           }
   ```

2. Create/update API endpoint

   File: backend/api/main.py

   ```python
   @app.get("/api/dashboard/kpis-with-trends")
   def get_kpis_with_trends():
       """Get KPIs with month-over-month trend indicators"""
       dashboard_service = DashboardService(DB_PATH)
       kpis = dashboard_service.get_kpi_with_trends()
       return kpis
   ```

3. Update frontend KPI card component

   File: frontend/src/components/dashboard/kpi-card.tsx

   ```typescript
   import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
   import { cn } from '@/lib/utils'

   interface KPICardProps {
     title: string
     value: number | string
     trend?: {
       value: number
       direction: 'up' | 'down' | 'neutral'
       label: string
     }
     format?: 'number' | 'currency' | 'percentage'
   }

   export function KPICard({ title, value, trend, format = 'number' }: KPICardProps) {
     const formatValue = (val: number | string) => {
       if (typeof val === 'string') return val
       switch (format) {
         case 'currency':
           return `$${val.toLocaleString()}`
         case 'percentage':
           return `${val}%`
         default:
           return val.toLocaleString()
       }
     }

     return (
       <div className="kpi-card rounded-lg border bg-card p-6">
         <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
         <div className="mt-2 flex items-baseline justify-between">
           <p className="text-4xl font-bold">{formatValue(value)}</p>

           {trend && (
             <div className={cn(
               "flex items-center gap-1 text-sm font-medium",
               trend.direction === 'up' && "text-green-600",
               trend.direction === 'down' && "text-red-600",
               trend.direction === 'neutral' && "text-gray-500"
             )}>
               {trend.direction === 'up' && <TrendingUp className="h-4 w-4" />}
               {trend.direction === 'down' && <TrendingDown className="h-4 w-4" />}
               {trend.direction === 'neutral' && <Minus className="h-4 w-4" />}
               <span>{trend.label}</span>
             </div>
           )}
         </div>
       </div>
     )
   }
   ```

4. Update dashboard page to use trends

   File: frontend/src/app/(dashboard)/page.tsx

   ```typescript
   const { data: kpis } = useQuery({
     queryKey: ['kpis-with-trends'],
     queryFn: () => api.get('/api/dashboard/kpis-with-trends')
   })

   <KPICard
     title="Active Proposals"
     value={kpis.active_proposals.value}
     trend={kpis.active_proposals.trend}
   />

   <KPICard
     title="Outstanding Invoices"
     value={kpis.outstanding_invoices.value}
     trend={kpis.outstanding_invoices.trend}
     format="currency"
   />
   ```

5. Add tooltip explaining calculation

   ```typescript
   <Tooltip>
     <TooltipTrigger>{trend.label}</TooltipTrigger>
     <TooltipContent>
       Month-over-month change (vs. 30 days ago)
     </TooltipContent>
   </Tooltip>
   ```

6. Test
   ```bash
   curl http://localhost:8000/api/dashboard/kpis-with-trends | jq
   ```

   - Open http://localhost:3002
   - Verify all KPI cards show trend indicators
   - Verify colors: green (up), red (down), gray (neutral)
   - Hover over trend → shows tooltip
   - Trends make sense (compare to 30 days ago)

Report back with:
✅ API response showing trends for all KPIs
✅ Screenshot of dashboard with trend indicators
✅ Color coding working (green up, red down)
✅ Tooltip showing explanation
✅ Trends calculated correctly (verify with manual calculation)

---

Timeline: 2 hours
Priority: 🟡 MEDIUM - user requested feature
```

---

## 📝 SUMMARY FOR ALL CLAUDES

**Context for Everyone:**
- We're in Phase 1.5 (critical fixes + completion)
- Coordinator handling backend/api/main.py infrastructure fixes
- Focus on your specific tasks
- Test everything in browser before claiming done
- Provide proof: screenshots + command outputs

**Timeline:**
- Week 1: Critical bugs (Claude 1, 2, 4)
- Week 2: New features (Claude 3, 5)
- Week 3: Testing + production prep

**Communication:**
- Report back with exact findings (file paths, line numbers)
- Show proof (screenshots, curl outputs, database queries)
- Don't claim "done" without browser testing
- Ask if blocked or unclear

---

**Ready to send these prompts now!**
