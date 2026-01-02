# PARALLEL AGENT TASKS
**4 Claude Agents Working Simultaneously**

---

## 🎯 OVERVIEW

**Goal:** Fix all critical issues to make app production-ready
**Timeline:** All agents work in parallel, sync at end for testing
**Branch Strategy:** Each agent creates their own feature branch

---

## 📋 AGENT 1: AUTHENTICATION & USER CONTEXT

**GitHub Issues:** #227, #230, #231
**Priority:** P0 - CRITICAL BLOCKER
**Estimated Time:** 3-4 hours
**Branch Name:** `fix/authentication-user-context`

### Tasks

1. **Fix NextAuth Build Error (#230)**
   - Debug why build is failing
   - Check NextAuth version matches code syntax
   - Fix route handler configuration
   - **Success:** `npm run build` completes successfully

2. **Enable Authentication Middleware (#231)**
   - Rename `src/middleware.ts.disabled` → `src/middleware.ts`
   - Test it doesn't cause 500 errors
   - Verify unauthenticated users redirect to /login
   - **Success:** Incognito window redirects to login page

3. **Remove ALL Hardcoded "Bill" References (#227)**

   **Files to Update:**
   ```
   src/app/(dashboard)/page.tsx:167
   src/app/(dashboard)/my-day/page.tsx:45
   src/app/(dashboard)/tracker/page.tsx:554,713,1025
   src/app/(dashboard)/emails/intelligence/page.tsx:39,48
   src/app/(dashboard)/emails/links/page.tsx:10
   src/components/proposal-quick-edit-dialog.tsx:35
   src/components/dashboard/daily-briefing.tsx:65
   src/components/dashboard/dashboard-page.tsx:64
   src/components/dashboard/role-switcher.tsx:22,66
   ```

   **Find ALL instances:**
   ```bash
   grep -r "\"bill\"" src/
   grep -r "'bill'" src/
   grep -r "Bill" src/ | grep -v "// Bill" | grep -v "import"
   ```

   **Replace with:**
   ```tsx
   import { useSession } from "next-auth/react"

   const { data: session } = useSession()
   const userName = session?.user?.name || "User"
   const userEmail = session?.user?.email
   const userRole = session?.user?.role
   ```

   **Success:**
   - No more hardcoded "bill" or "Bill" in codebase
   - User name displays correctly based on logged-in user
   - API calls send actual user email/ID from session

### Verification Steps

```bash
# 1. Check build works
cd frontend
npm run build
# Should succeed with no errors

# 2. Test login flow
npm run dev
# Open incognito: http://localhost:3002
# Should redirect to /login
# Login with test user
# Should redirect to /dashboard
# Should show user's actual name (not "Bill")

# 3. Check all API calls
# Open browser dev tools → Network tab
# Navigate to different pages
# Verify API calls send actual user email/ID (not "bill")

# 4. Test with different users
# Login as different users
# Verify each sees their own name
```

### Deliverables

- [ ] Build succeeds without errors
- [ ] Middleware enabled and working
- [ ] Login/logout flow works
- [ ] Session persists across page refreshes
- [ ] No hardcoded "Bill" anywhere
- [ ] User name displayed correctly for each user
- [ ] All API calls use actual user from session

### Notes

- Read `.claude/UI_DESIGN_SPECS.md` for design guidelines
- Test thoroughly with multiple users
- Don't break existing functionality
- Commit frequently with clear messages

---

## 📋 AGENT 2: ROLE-BASED ACCESS CONTROL (RBAC)

**GitHub Issues:** #228
**Priority:** P0 - CRITICAL SECURITY
**Estimated Time:** 4-5 hours
**Branch Name:** `feat/role-based-access-control`

### Tasks

1. **Backend: Add Role-Based Filtering**

   **Files to Update:**
   ```
   backend/api/routers/projects.py
   backend/api/routers/proposals.py
   backend/api/routers/invoices.py
   backend/api/routers/finance.py
   backend/api/dependencies.py (get_current_user)
   ```

   **Implementation:**
   ```python
   from api.dependencies import get_current_user

   @router.get("/projects")
   async def get_projects(current_user=Depends(get_current_user)):
       if current_user["role"] == "pm":
           # PM sees only assigned projects
           projects = get_projects_assigned_to_pm(current_user["staff_id"])
       elif current_user["role"] in ["executive", "admin"]:
           # Executives see all
           projects = get_all_projects()
       else:
           raise HTTPException(403, "Unauthorized")

       return projects
   ```

   **Apply to:**
   - Projects list (filter by PM assignment)
   - Proposals list (filter by owner)
   - Financial data (block PM role entirely)
   - Admin endpoints (block non-admin roles)

2. **Frontend: Conditional Rendering by Role**

   **Create Utility:**
   ```tsx
   // src/lib/rbac.ts
   export const canViewFinancials = (role: string) => {
     return ['executive', 'finance', 'admin'].includes(role)
   }

   export const canAccessAdmin = (role: string) => {
     return role === 'admin'
   }

   export const isExecutive = (role: string) => {
     return ['executive', 'admin'].includes(role)
   }
   ```

   **Update Components:**
   ```tsx
   import { useSession } from "next-auth/react"
   import { canViewFinancials } from "@/lib/rbac"

   const { data: session } = useSession()

   return (
     <>
       {canViewFinancials(session?.user?.role) && (
         <InvoiceAgingWidget />
       )}
     </>
   )
   ```

   **Pages to Update:**
   - Hide invoice amounts on `/projects` for PM role
   - Hide `/finance` page entirely for PM role
   - Hide `/admin/*` pages for non-admin role
   - Filter navigation based on role

3. **Middleware: Protect Admin Routes**

   **Update:** `src/middleware.ts`
   ```tsx
   export default auth((req) => {
     const isLoggedIn = !!req.auth
     const pathname = req.nextUrl.pathname
     const userRole = req.auth?.user?.role

     // Redirect to login if not authenticated
     if (!isLoggedIn && pathname !== "/login") {
       return NextResponse.redirect(new URL("/login", req.url))
     }

     // Protect admin routes
     if (pathname.startsWith("/admin") && userRole !== "admin") {
       return NextResponse.redirect(new URL("/", req.url))
     }

     // Block finance page for PMs
     if (pathname.startsWith("/finance") && userRole === "pm") {
       return NextResponse.redirect(new URL("/", req.url))
     }

     return NextResponse.next()
   })
   ```

4. **Navigation: Filter by Role**

   **Update:** `src/components/layout/app-shell.tsx`
   ```tsx
   const navItems = [
     { href: "/dashboard", icon: Home, label: "Dashboard", roles: ["all"] },
     { href: "/my-day", icon: Calendar, label: "My Day", roles: ["all"] },
     { href: "/finance", icon: DollarSign, label: "Finance", roles: ["executive", "finance", "admin"] },
     { href: "/admin", icon: Settings, label: "Admin", roles: ["admin"] },
   ]

   const filteredNav = navItems.filter(item =>
     item.roles.includes("all") || item.roles.includes(session?.user?.role)
   )
   ```

### Verification Steps

```bash
# 1. Create test users in database
sqlite3 database/bensley_master.db
UPDATE staff SET role='pm' WHERE email='pm@bensley.com';
UPDATE staff SET role='executive' WHERE email='bill@bensley.com';
UPDATE staff SET role='admin' WHERE email='admin@bensley.com';

# 2. Test as PM
# Login as pm@bensley.com
# Navigate to /finance → Should redirect to /
# Navigate to /admin → Should redirect to /
# Check /projects → Should see only assigned projects
# Check /tracker → Should see only assigned proposals
# Verify NO invoice amounts visible anywhere

# 3. Test as Executive
# Login as bill@bensley.com
# Should see everything (all pages, all data)
# Finance page should be accessible
# Should see all projects/proposals

# 4. Test as Admin
# Login as admin@bensley.com
# Should access /admin pages
# Should see all data

# 5. Check API responses
# Use browser dev tools → Network tab
# Verify API returns filtered data based on role
# PM should NOT receive financial data in API responses
```

### Deliverables

- [ ] Backend filters data by user role
- [ ] PM sees only assigned projects
- [ ] PM cannot access /finance page
- [ ] PM cannot access /admin pages
- [ ] Financial data hidden from PM in UI
- [ ] Navigation filtered by role
- [ ] Middleware protects admin routes
- [ ] All tests pass for each role

### Notes

- SECURITY CRITICAL - test thoroughly
- Don't trust client-side checks only
- Backend must enforce role restrictions
- Test with real PM user scenario

---

## 📋 AGENT 3: TASKS SYSTEM & UI IMPROVEMENTS

**GitHub Issues:** #226, #229
**Priority:** P1 - HIGH
**Estimated Time:** 6-8 hours
**Branch Name:** `feat/professional-tasks-ui`

### Tasks

1. **Create /tasks Page (#226)**

   **Create:** `src/app/(dashboard)/tasks/page.tsx`

   **Requirements:**
   - List view & Kanban view (toggle)
   - Filters: My Tasks, All Tasks, Overdue, This Week
   - Search bar
   - Bulk selection
   - Create task button
   - Export to CSV

   **Use Design Specs:** `.claude/UI_DESIGN_SPECS.md` Section 4

2. **Build Kanban Board Component**

   **Install Dependencies:**
   ```bash
   npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
   ```

   **Create:** `src/components/tasks/task-kanban-board.tsx`

   **Features:**
   - Drag & drop between columns
   - Columns: To Do, In Progress, In Review, Done
   - Visual priority indicators
   - Avatars for assignees
   - Count badges on column headers
   - Add task button in each column

   **Reference:** Monday.com Kanban board

3. **Build Professional Task Card**

   **Create:** `src/components/tasks/task-card-pro.tsx`

   **Include:**
   - Priority indicator (colored bar on left)
   - Task title (click to open detail)
   - Project badge
   - Due date with icon
   - Assignee avatar
   - Icons: comments, attachments, subtasks
   - Hover: show drag handle
   - Smooth animations

4. **Enhance Task Detail Modal**

   **Update:** `src/components/tasks/task-edit-modal.tsx`

   **Add:**
   - Rich text editor for description
   - Subtasks checklist
   - File attachments
   - Comments section
   - Activity log
   - Related tasks
   - Two-column layout (content | sidebar)

   **Reference:** Linear task detail

5. **Build List View with Inline Editing**

   **Create:** `src/components/tasks/task-list-view.tsx`

   **Features:**
   - Sortable columns
   - Bulk selection (checkboxes)
   - Inline editing (double-click)
   - Row actions menu
   - Sticky header
   - Pagination (50 tasks per page)

6. **Add Keyboard Shortcuts**

   **Install:** `npm install @mantine/hooks`

   **Implement:**
   ```tsx
   useHotkeys([
     ['c', () => openCreateTaskModal()],
     ['e', () => openEditTaskModal()],
     ['j', () => selectNextTask()],
     ['k', () => selectPreviousTask()],
   ])
   ```

7. **Connect to Backend API**

   **Update:** `src/lib/api.ts`

   **Add Methods:**
   ```tsx
   // Tasks
   getTasks(filters?: TaskFilters): Promise<Task[]>
   createTask(task: CreateTaskInput): Promise<Task>
   updateTask(id: string, updates: Partial<Task>): Promise<Task>
   deleteTask(id: string): Promise<void>
   updateTaskStatus(id: string, status: TaskStatus): Promise<Task>
   bulkUpdateTasks(ids: string[], updates: Partial<Task>): Promise<void>
   ```

8. **Add Role-Based Filtering**

   ```tsx
   // PM sees only their tasks
   if (user.role === 'pm') {
     tasks = tasks.filter(t => t.assignedTo === user.staffId)
   }

   // Executives see all tasks
   if (user.role in ['executive', 'admin']) {
     tasks = allTasks
   }
   ```

### Verification Steps

```bash
# 1. Navigate to /tasks page
npm run dev
# Click "View all overdue" from My Day
# Should go to /tasks page (not 404)

# 2. Test Kanban board
# Drag task from "To Do" to "In Progress"
# Should move smoothly with animation
# Should update in database
# Refresh page → task should still be in new column

# 3. Test List view
# Toggle to List view
# Sort by due date, priority, assignee
# Select multiple tasks (checkboxes)
# Bulk change status → Should update all selected

# 4. Test Create task
# Click "+ New Task"
# Fill out form
# Save
# Should appear in Kanban/List immediately

# 5. Test keyboard shortcuts
# Press 'c' → Should open create modal
# Select task, press 'e' → Should open edit modal
# Press 'j'/'k' → Should navigate up/down

# 6. Test as PM
# Login as PM
# Should see only tasks assigned to them
# Should NOT see other PMs' tasks

# 7. Test as Executive
# Login as Bill
# Should see ALL tasks across all PMs
```

### Deliverables

- [ ] /tasks page exists and loads
- [ ] Kanban board with drag & drop
- [ ] List view with sorting/filtering
- [ ] Task create/edit modals professional quality
- [ ] Keyboard shortcuts work
- [ ] Bulk operations work
- [ ] Role-based task filtering
- [ ] Matches design specs
- [ ] Looks like Monday.com/Trello quality

### Notes

- Prioritize UX - make it feel professional
- Smooth animations (60fps)
- Test on mobile (responsive)
- Follow design specs closely
- Get user feedback before finalizing

---

## 📋 AGENT 4: NAVIGATION & PAGE IMPROVEMENTS

**GitHub Issues:** #232, #233
**Priority:** P2 - MEDIUM
**Estimated Time:** 4-5 hours
**Branch Name:** `feat/navigation-improvements`

### Tasks

1. **Add Hidden Pages to Navigation (#232)**

   **Update:** `src/components/layout/app-shell.tsx`

   **New Navigation Structure:**
   ```tsx
   const navigation = [
     { section: "Main" },
     { href: "/", icon: Home, label: "Dashboard" },
     { href: "/my-day", icon: Calendar, label: "My Day" },

     { section: "Proposals", collapsible: true },
     { href: "/tracker", icon: Target, label: "Tracker" },
     { href: "/overview", icon: BarChart, label: "Overview" },

     { section: "Projects", collapsible: true },
     { href: "/projects", icon: Folder, label: "All Projects" },
     { href: "/deliverables", icon: CheckSquare, label: "Deliverables" },
     { href: "/rfis", icon: FileQuestion, label: "RFIs" },

     { section: "Team", collapsible: true },
     { href: "/team", icon: Users, label: "PM Workload" },
     { href: "/contacts", icon: UserCircle, label: "Contacts" },

     { href: "/meetings", icon: Video, label: "Meetings" },

     { section: "Finance", roles: ["executive", "finance", "admin"] },
     { href: "/finance", icon: DollarSign, label: "Overview" },
     { href: "/analytics", icon: TrendingUp, label: "Analytics" },

     { section: "Admin", roles: ["admin"] },
     { href: "/admin", icon: Settings, label: "Dashboard" },
     { href: "/admin/suggestions", icon: Sparkles, label: "AI Suggestions" },
     { href: "/admin/email-review", icon: Mail, label: "Email Review" },
     { href: "/admin/patterns", icon: Brain, label: "Patterns" },
     { href: "/system", icon: Activity, label: "System Status" },
   ]
   ```

2. **Build Collapsible Navigation Sections**

   **Features:**
   - Click section header to expand/collapse
   - Remember state in localStorage
   - Smooth collapse animation
   - Chevron icon rotates

3. **Fix Duplicate /suggestions Pages**

   **Decision:** Keep `/suggestions` as canonical

   **Update:** `src/app/(dashboard)/admin/suggestions/page.tsx`
   ```tsx
   // Redirect to main suggestions page
   import { redirect } from 'next/navigation'

   export default function AdminSuggestionsRedirect() {
     redirect('/suggestions')
   }
   ```

4. **Delete Obsolete /transcripts Page**

   ```bash
   rm -rf src/app/(dashboard)/transcripts
   ```

   **Verify:** All links to `/transcripts` redirect to `/meetings`

5. **Add Search/Command Palette**

   **Install:** `npm install cmdk`

   **Create:** `src/components/command-palette.tsx`

   **Features:**
   - Cmd+K to open
   - Search all pages
   - Search all projects
   - Search all tasks
   - Quick actions (+ New Project, + New Task)
   - Recent pages

6. **Improve Page Headers**

   **Create:** `src/components/layout/page-header.tsx`

   **Standard Structure:**
   ```tsx
   <PageHeader>
     <Breadcrumbs>
       <BreadcrumbItem href="/projects">Projects</BreadcrumbItem>
       <BreadcrumbItem current>25 BK-033</BreadcrumbItem>
     </Breadcrumbs>

     <div className="flex items-center justify-between">
       <div>
         <PageTitle>Ritz-Carlton Nusa Dua</PageTitle>
         <PageDescription>Luxury resort in Bali</PageDescription>
       </div>

       <div className="flex gap-2">
         <Button variant="outline">Export</Button>
         <Button>+ Add Task</Button>
       </div>
     </div>
   </PageHeader>
   ```

   **Apply to All Major Pages:**
   - /projects
   - /proposals
   - /tracker
   - /tasks
   - /deliverables
   - /rfis

7. **Add Empty States**

   **Create:** `src/components/empty-state.tsx`

   **Use Cases:**
   - No tasks yet
   - No projects found
   - No search results
   - No overdue items

   **Include:**
   - Relevant icon
   - Friendly message
   - Call-to-action button

8. **Improve Loading States**

   **Update Skeleton Screens:**
   - Match actual component layout
   - Animated pulse
   - Realistic sizing

9. **Polish Dashboard Cards**

   **Update:** `src/app/(dashboard)/page.tsx`

   **Improvements:**
   - Consistent card spacing
   - Hover effects (slight lift)
   - Better typography hierarchy
   - Loading skeletons
   - Empty states

### Verification Steps

```bash
# 1. Test new navigation
npm run dev
# Verify all pages are in sidebar:
# - Deliverables (new)
# - RFIs (new)
# - Contacts (new)
# - Analytics (new)

# 2. Test collapsible sections
# Click "Projects" section header
# Should collapse/expand children
# Refresh page → state should persist

# 3. Test command palette
# Press Cmd+K
# Should open search modal
# Type "projects" → Should show /projects page
# Type "task" → Should show tasks
# Press Esc → Should close

# 4. Test role-based navigation
# Login as PM
# Should NOT see Finance section
# Should NOT see Admin section

# 5. Test breadcrumbs
# Navigate to project detail
# Should show: Projects > 25 BK-033
# Click "Projects" → Should go back to list

# 6. Test empty states
# Navigate to page with no data
# Should show friendly empty state
# Click CTA button → Should open create modal

# 7. Check all pages load
# Go through every navigation item
# Verify no 404 errors
# Verify no console errors
```

### Deliverables

- [ ] All 4 hidden pages added to navigation
- [ ] Navigation collapsible sections work
- [ ] Duplicate /suggestions page resolved
- [ ] /transcripts page deleted
- [ ] Command palette (Cmd+K) works
- [ ] Page headers consistent across app
- [ ] Empty states implemented
- [ ] Loading states improved
- [ ] Role-based navigation filtering
- [ ] No navigation dead ends or 404s

### Notes

- Focus on discoverability
- Make navigation intuitive
- Test with real user flow
- Mobile navigation needs special attention

---

## 🔄 COORDINATION & MERGE STRATEGY

### Git Workflow

**Each Agent:**
1. Pull latest main: `git checkout main && git pull`
2. Create feature branch: `git checkout -b <branch-name>`
3. Work on tasks
4. Commit frequently with clear messages
5. Push to origin: `git push -u origin <branch-name>`
6. Create PR when done
7. **DO NOT MERGE** - wait for testing

### Merge Order

**After all agents complete:**
1. Test Agent 1 (Auth) - MUST work first
2. Test Agent 2 (RBAC) - Depends on Auth
3. Test Agent 3 (Tasks) - Independent
4. Test Agent 4 (Nav) - Independent

**Then:**
5. Merge in order: Agent 1 → Agent 2 → Agent 3 → Agent 4
6. Fix any merge conflicts
7. Test everything together
8. Deploy to staging

---

## 🧪 FINAL TESTING CHECKLIST

**After ALL agents complete, test together:**

### Authentication (Agent 1)
- [ ] Build succeeds
- [ ] Login/logout works
- [ ] Session persists
- [ ] User name shows correctly
- [ ] No hardcoded "Bill"

### RBAC (Agent 2)
- [ ] PM cannot see financials
- [ ] PM cannot access /admin
- [ ] PM sees only assigned projects
- [ ] Executives see everything
- [ ] Navigation filtered by role

### Tasks (Agent 3)
- [ ] /tasks page loads
- [ ] Kanban drag & drop works
- [ ] List view works
- [ ] Create/edit tasks work
- [ ] Keyboard shortcuts work
- [ ] Looks professional

### Navigation (Agent 4)
- [ ] All pages in navigation
- [ ] Command palette (Cmd+K) works
- [ ] No 404 errors
- [ ] Empty states work
- [ ] Loading states work

### Cross-Agent Integration
- [ ] Auth + RBAC work together
- [ ] Tasks filtered by role
- [ ] Navigation filtered by role
- [ ] All features work for each role:
  - [ ] Test as PM
  - [ ] Test as Executive
  - [ ] Test as Admin

### Production Readiness
- [ ] No console errors
- [ ] No console.log statements
- [ ] All pages responsive (mobile)
- [ ] All forms validate properly
- [ ] All data loads correctly
- [ ] Performance acceptable (< 3s load)

---

## 🚨 IF SOMETHING BREAKS

**Agent Checklist:**
1. Don't panic
2. Check if it's your change or existing issue
3. Read error message carefully
4. Check browser console
5. Check terminal logs
6. Test in incognito (clear cache)
7. Ask for help if stuck > 30 min

**Common Issues:**
- Build fails → Check dependencies (`npm install`)
- 404 errors → Check file paths
- API errors → Check backend is running
- Auth errors → Check .env.local has AUTH_SECRET
- TypeScript errors → Check types match

---

## 📞 COMMUNICATION

**Each agent should:**
- Comment on their GitHub issues with progress
- Push commits frequently (don't hoard changes)
- Note any blockers or questions
- Update if timeline changes

**Lukas will:**
- Monitor progress
- Answer questions
- Test each agent's work
- Coordinate final merge

---

**Good luck! Build something professional 🚀**
