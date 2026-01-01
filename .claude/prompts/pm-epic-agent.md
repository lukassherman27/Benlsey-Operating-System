# PM Epic Agent - Project Management System Build

> Epic: #309 | Sub-Issues: #310, #311, #312, #313 | Priority: P0/P1 | Branch: `feat/pm-system-309`

---

## CONTEXT

**THE BIG BUILD.** Project management is only 10% done.

From Lukas:
> "Projects, we haven't done anything yet. That's going to need a lot of work."
> "The project management is the difficult thing - actually managing the designers."

### What This Encompasses
- **#310** Task Management UI (Discipline/Phase) - Interior, Landscape, Lighting, FF&E
- **#311** Daily Work Collection & Review - What designers did today
- **#312** Weekly Scheduling UI - Who works on what, consolidated view
- **#313** Deliverables CRUD & Tracking - What's due when

---

## PHASE 1: UNDERSTAND (Research First)

### Required Research
```bash
# Check existing project structure
sqlite3 database/bensley_master.db ".schema projects"
sqlite3 database/bensley_master.db ".schema project_phases"
sqlite3 database/bensley_master.db ".schema tasks"

# Check what deliverables table exists (empty per audit)
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM deliverables;"

# Check existing project pages
find frontend/src/app -path "*project*" -name "page.tsx" | head -10

# Check existing task components
find frontend/src/components -name "*task*" -type f | head -10

# Check project routers
head -100 backend/api/routers/projects.py
head -100 backend/api/routers/tasks.py
```

### Questions to Answer
1. What project/task UI already exists?
2. What's the data model for tasks by discipline?
3. How do designers currently submit daily work? (email?)
4. What's the weekly schedule structure?

### Files to Read
- `frontend/src/app/(dashboard)/projects/[code]/page.tsx` - Project detail page
- `frontend/src/app/(dashboard)/tasks/page.tsx` - Tasks page
- `backend/api/routers/projects.py` - Project endpoints
- `backend/api/routers/tasks.py` - Task endpoints
- `backend/api/routers/deliverables.py` - Deliverables endpoints

**STOP HERE** until you understand what already exists.

---

## PHASE 2: THINK HARD (Planning)

### The Four Disciplines
Bensley projects have four main disciplines:
1. **Interior Design** - Rooms, lobbies, restaurants
2. **Landscape Architecture** - Gardens, pools, outdoor spaces
3. **Lighting Design** - Ambient, task, decorative
4. **FF&E** - Furniture, fixtures, equipment

Each discipline has its own team, tasks, and deliverables.

### Design Decisions
1. **Task structure** - Flat list vs nested by discipline/phase?
2. **Daily work input** - Form vs email parsing?
3. **Schedule view** - Calendar vs Gantt vs simple list?
4. **Deliverable tracking** - Simple checklist vs full workflow?

### Web Research
```
Search: "design agency project management workflow"
Search: "multi-discipline project task management UI"
Search: "weekly resource scheduling dashboard"
```

### Recommended Phased Approach
Since this is a big build, break into sub-issues:

**Phase A (#310)**: Task Management
- Add discipline/phase fields to tasks
- Create filtered task views by discipline
- Drag-drop assignment

**Phase B (#313)**: Deliverables
- CRUD for deliverables
- Link to project phases
- Due date tracking

**Phase C (#311)**: Daily Work
- Simple form: "What did you work on?"
- Links to project/task
- Hours logged

**Phase D (#312)**: Weekly Schedule
- Calendar view of who's on what project
- Capacity indicators

---

## PHASE 3: IMPLEMENT

### Focus on #310 First: Task Management UI

#### Database Changes
```sql
-- Add discipline to tasks if not exists
ALTER TABLE tasks ADD COLUMN discipline TEXT
  CHECK (discipline IN ('Interior', 'Landscape', 'Lighting', 'FFE', 'General'));

ALTER TABLE tasks ADD COLUMN phase TEXT; -- Design Development, Construction Docs, etc
```

#### Backend Changes
Update `backend/api/routers/tasks.py`:
```python
@router.get("/tasks/by-discipline")
async def get_tasks_by_discipline(project_id: int = None):
    """Get tasks grouped by discipline"""

@router.put("/tasks/{task_id}/assign")
async def assign_task(task_id: int, assignee_id: int, discipline: str):
    """Assign task to team member with discipline"""
```

#### Frontend Changes
Create `frontend/src/components/projects/task-discipline-view.tsx`:
- Filter tabs: All | Interior | Landscape | Lighting | FF&E
- Kanban columns: Backlog | In Progress | Review | Done
- Each card shows assignee, due date, phase

### Files to Create/Modify
| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/add_task_discipline.sql` | Create | Add discipline column |
| `backend/api/routers/tasks.py` | Modify | Add discipline endpoints |
| `frontend/src/components/projects/task-discipline-view.tsx` | Create | Filtered task view |
| `frontend/src/app/(dashboard)/projects/[code]/tasks/page.tsx` | Create | Project tasks page |

---

## PHASE 4: VERIFY

### Testing Checklist
- [ ] Tasks can have discipline assigned
- [ ] Filtering by discipline works
- [ ] Kanban drag-drop still works
- [ ] Project detail page shows discipline breakdown
- [ ] API returns tasks grouped correctly

### Verification Commands
```bash
# Test new endpoint
curl http://localhost:8000/api/tasks/by-discipline?project_id=1

# Build check
cd frontend && npm run build

# Type check
cd frontend && npx tsc --noEmit
```

### Success Criteria
- Tasks categorized by discipline
- PMs can filter and assign tasks
- Visual breakdown on project page

---

## PHASE 5: COMPLETE

### Commit Format
```bash
git commit -m "feat(tasks): add discipline-based task management (#310)

- Add discipline column to tasks table
- Create /tasks/by-discipline endpoint
- Build TaskDisciplineView component with filters
- Update project detail page

Part of Epic #309"
```

### Close Sub-Issue, Keep Epic Open
```bash
gh issue close 310 --comment "Completed in PR #XXX"
# Epic #309 stays open until all sub-issues done
```

---

## CONSTRAINTS

- **Don't break existing tasks** - Add fields, don't change existing
- **Start simple** - Kanban first, Gantt later
- **PM-focused** - This is for Astuti/Brian K, not designers yet
- **Mobile secondary** - PMs use laptops primarily

---

## RESOURCES

- `.claude/plans/system-architecture-ux.md` - Section 6: The Four Systems
- Epic issue #309 for full scope
- Existing task kanban in `/tasks` page
