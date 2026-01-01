# Monday.com & Trello API Study - PM Tools Comparison

**Date:** 2025-12-30
**Researcher:** Agent 5 (Research Agent)
**Issue:** #205 (Ongoing Research)

---

## Summary

Studied Monday.com and Trello to identify features and UX patterns Bensley could adopt. Both are mature project management tools with robust APIs. Key takeaways: **WIP limits**, **swimlanes**, **workload views**, and **automated status notifications** are features worth considering for Bensley's project management. We already have a Kanban board - the opportunity is enhancing it.

**TL;DR:** Bensley has the foundation (Kanban, project dashboard, timeline). Focus on adding WIP limits, swimlanes, and workload capacity views for PM testing in February.

---

## Key Findings

### 1. Monday.com Overview

**What It Is:**
- Enterprise work management platform
- GraphQL API for full CRUD operations
- 100+ automation templates
- Used by large teams for complex projects

**Pricing:**
- Free: 2 users max, no dashboards
- Basic: $13/seat/month
- Pro: $26/seat/month
- Enterprise: Custom pricing

**Notable 2025 Features:**
- Capacity Planner (workload, velocity, availability)
- GitLab/GitHub integrations
- VS Code extension for devs
- Cross-project dependency visualization
- Portfolio-level dashboards

### 2. Trello Overview

**What It Is:**
- Kanban-focused project management
- REST API with webhooks
- Butler automation (no-code)
- Best for smaller teams, simpler projects

**Pricing:**
- Free: 10 boards, unlimited cards, 250 automations/month
- Standard: $5/user/month
- Premium: $10/user/month
- Enterprise: $17.50/user/month

**Notable Features:**
- Best-in-class Kanban experience
- 300+ power-ups (integrations)
- Customizable card fields
- Swimlanes for multi-project views

### 3. Bensley's Current State

We already have several PM components:

| Component | File |
|-----------|------|
| Kanban Board | `task-kanban-board.tsx` |
| Mini Kanban | `task-mini-kanban.tsx` |
| Project Health | `project-health-dashboard.tsx` |
| Project Timeline | `projects-timeline.tsx` |
| Project Cards | `project-card.tsx` |
| Active Projects | `active-projects-tab.tsx` |
| Task Edit Modal | `task-edit-modal.tsx` |

**What We Have:**
- Basic Kanban columns (likely To Do, In Progress, Done)
- Project health indicators
- Timeline visualization
- Task management with editing

**What We're Missing (vs Monday/Trello):**
- WIP limits per column
- Swimlanes for multi-project views
- Workload/capacity planning
- Automated status notifications
- Cross-project dependency views
- Custom fields on task cards

---

## Features Worth Stealing

### Priority 1: WIP Limits (High Value, Low Effort)

**What It Is:**
Limit how many tasks can be "In Progress" at once. Prevents team overload.

**Why It Matters:**
- Prevents context-switching burnout
- Forces completion before starting new work
- Visual indicator when a column is "full"

**Implementation:**
```typescript
// Add to Kanban column
const WIP_LIMITS = {
  'in_progress': 5,  // Max 5 tasks in progress
  'review': 3        // Max 3 tasks in review
};
```

### Priority 2: Swimlanes (Medium Value, Medium Effort)

**What It Is:**
Horizontal lanes that separate work by project, team, or priority.

**Why It Matters:**
- PMs can see all their projects in one Kanban view
- Filter by project without switching contexts
- Better for portfolio-level visibility

**Implementation:**
Add groupBy option to Kanban that creates horizontal sections per project.

### Priority 3: Workload View (High Value, Medium Effort)

**What It Is:**
View that shows team capacity vs. assigned work.

**Why It Matters:**
- Prevents overassignment
- Identifies underutilized team members
- Essential for resource planning

**From Monday.com:**
- Daily/Weekly/Monthly views
- Velocity tracking
- Sprint scope visualization

### Priority 4: Task Card Enhancements (Low Value, Low Effort)

**What It Is:**
Richer task cards with visible metadata.

**From Trello/Monday:**
- Due date badges
- Assignee avatars
- Time estimate/actual
- Priority indicators (colored dots)
- Attachment indicators

---

## API Comparison

### Monday.com GraphQL API

```graphql
# Example: Get board items
query {
  boards(ids: [123]) {
    items {
      id
      name
      column_values {
        id
        value
      }
    }
  }
}
```

**Pros:**
- Flexible queries (only get what you need)
- Full CRUD on all entities
- Webhook support for real-time updates

**Cons:**
- GraphQL learning curve
- Rate limits on queries

### Trello REST API

```bash
# Example: Get board cards
GET /1/boards/{boardId}/cards
Authorization: OAuth 1.0a
```

**Pros:**
- Simple REST interface
- Excellent webhook support
- Well-documented

**Cons:**
- Multiple calls for related data
- Authentication complexity

### Bensley API Pattern

Our FastAPI backend already follows REST patterns similar to Trello:

```python
# backend/api/routers/tasks.py
@router.get("/tasks")
@router.post("/tasks")
@router.patch("/tasks/{task_id}")
```

**No major API changes needed** - our pattern is already industry-standard.

---

## Pros of Monday.com/Trello Approach

1. **Visual Clarity** - Everything important visible on cards
2. **Automation Built-in** - Status changes trigger notifications
3. **Flexible Views** - Same data, multiple visualizations
4. **Workload Management** - Capacity planning prevents overload
5. **Cross-Project Visibility** - Portfolio dashboards

---

## Cons / Not Applicable to Bensley

1. **Pricing** - We're building our own, no SaaS costs
2. **Generic Features** - They serve all industries, we're focused on architecture firms
3. **Overkill** - 100+ automation templates when we need 5-10
4. **No Email Integration** - Our proposal/email linking is unique

---

## Recommendation

**ADOPT SELECT PATTERNS** - Don't copy everything, pick high-value features

### Recommended for Phase 2 (PM Testing)

| Feature | Effort | Value | Priority |
|---------|--------|-------|----------|
| WIP Limits | Low | High | 1 |
| Task Card Enhancements | Low | Medium | 2 |
| Swimlanes | Medium | Medium | 3 |
| Workload View | Medium | High | 4 |

### Not Recommended

- Full Monday.com-style automations (overkill)
- Multiple board views (we have enough views)
- GraphQL API switch (REST is fine)

---

## Implementation Suggestions

### 1. Add WIP Limits to Kanban

```typescript
// In task-kanban-board.tsx
interface KanbanColumn {
  id: string;
  title: string;
  wipLimit?: number;  // Add this
}

// Visual indicator when over limit
{column.wipLimit && tasks.length > column.wipLimit && (
  <Badge variant="destructive">Over WIP Limit</Badge>
)}
```

### 2. Add Swimlanes Toggle

```typescript
// Group tasks by project
const groupedByProject = useMemo(() => {
  return tasks.reduce((acc, task) => {
    const projectId = task.project_id || 'unassigned';
    if (!acc[projectId]) acc[projectId] = [];
    acc[projectId].push(task);
    return acc;
  }, {});
}, [tasks]);
```

### 3. Enhance Task Cards

Add visible badges for:
- Due date (with overdue highlighting)
- Assignee avatar
- Priority indicator
- Time remaining estimate

---

## References

- [Monday.com Platform API](https://developer.monday.com/api-reference/)
- [Monday.com GraphQL Basics](https://developer.monday.com/api-reference/docs/basics)
- [Trello API Introduction](https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/)
- [Monday.com vs Trello Comparison - Cloudwards](https://www.cloudwards.net/monday-com-vs-trello/)
- [Kanban Best Practices - IxDF](https://www.interaction-design.org/literature/topics/kanban-boards)
- [Kanban Project Management - Productive.io](https://productive.io/blog/kanban-project-management/)
- [Monday.com 2025 Features - Advaiya](https://advaiya.com/monday-com-project-management-features/)

---

## Appendix: Full Feature Comparison

| Feature | Monday.com | Trello | Bensley (Current) | Bensley (Recommended) |
|---------|------------|--------|-------------------|----------------------|
| Kanban Board | ✅ | ✅ | ✅ | ✅ |
| WIP Limits | ✅ | ✅ (Power-Up) | ❌ | ✅ Add |
| Swimlanes | ✅ | ✅ | ❌ | ✅ Add |
| Timeline View | ✅ | ✅ (Power-Up) | ✅ | ✅ |
| Workload View | ✅ | ❌ | ❌ | ✅ Add |
| Custom Fields | ✅ | ✅ | Partial | ✅ Enhance |
| Automations | 100+ | 250+/month | Custom | Custom |
| Email Integration | Limited | Limited | ✅ Deep | ✅ Unique |
| Proposal Tracking | ❌ | ❌ | ✅ | ✅ Unique |
| GraphQL API | ✅ | ❌ | ❌ | Not needed |
| REST API | ✅ | ✅ | ✅ | ✅ |
