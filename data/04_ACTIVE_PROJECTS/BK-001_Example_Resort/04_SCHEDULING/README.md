# PROJECT SCHEDULING STRUCTURE

This folder tracks both PLANNED and ACTUAL work.

---

## Two Types of Scheduling:

### 1. FORWARD SCHEDULE (Planning)
**Location:** `forward_schedule/`

**What it is:**
- What project managers ASSIGN staff to work on
- Weekly/monthly work planning
- Task allocation and priorities

**Files:**
- `weekly_plan.json` - Week-by-week assignments
- `monthly_plan.json` - Month-ahead planning
- `staff_allocation.json` - Overall team allocation %

**Created by:** Project Managers
**Updated:** Weekly (typically Monday morning)

---

### 2. DAILY WORK REPORTS (Actual Work)
**Location:** `daily_reports/`

**What it is:**
- Emails staff send to Bill & Brian EVERY DAY
- "Here's what I actually did today"
- Includes photos of work completed
- Actual hours spent tracking

**Organized two ways:**

#### By Date: `by_date/YYYY-MM-DD_daily_reports.json`
- All staff reports for a specific day
- Easy to see daily team productivity
- Quick daily summary for Bill & Brian

#### By Staff: `by_staff/[Staff_Name]/YYYY-MM-DD_report.json`
- Individual staff member's reports over time
- Track individual productivity
- Performance reviews

**Each report includes:**
- Tasks completed
- Hours spent
- Photos attached (work progress)
- Issues encountered
- Tomorrow's plan

**Sent to:** Bill & Brian (bill@bensley.com, brian@bensley.com)
**Sent when:** End of each workday (typically 5-6pm)

---

## How It Works:

### Monday Morning:
1. Project Manager creates `forward_schedule/weekly_plan.json`
2. Assigns tasks to each staff member for the week

### Every Evening:
1. Staff sends email to Bill & Brian with:
   - What they did today
   - Photos of work
   - Hours spent
   - Issues/questions
   - Tomorrow's plan

2. System processes email and creates:
   - `by_date/YYYY-MM-DD_daily_reports.json`
   - `by_staff/[Name]/YYYY-MM-DD_report.json`

3. Photos extracted to:
   - `09_PHOTOS/daily_progress/YYYY-MM-DD/`

### Weekly Review:
- Compare planned vs actual
- Identify bottlenecks
- Adjust next week's plan

---

## Database Tables:

### staff_assignments (Forward Planning)
```sql
- project_id
- staff_name
- role
- allocation_percent
- start_date, end_date
```

### daily_work_logs (Actual Work)
```sql
- project_id
- staff_name
- work_date
- tasks_completed
- hours_logged
- photos_count
- issues_noted
```

---

## AI Use Cases:

### Planned vs Actual Analysis:
- "Show me Designer 1's planned vs actual hours last week"
- "Which tasks consistently take longer than planned?"
- "Who is overallocated?"

### Productivity Tracking:
- "Total hours logged per staff member this month"
- "How many tasks completed vs assigned?"
- "Photos submitted per project phase"

### Pattern Detection:
- "Which types of tasks take longest?"
- "When do staff report most issues?"
- "Bottlenecks in the workflow?"

---

## Example Workflow:

**Monday 9am:**
```json
forward_schedule/weekly_plan.json
{
  "Designer 1": {
    "monday": "Villa south facade - 8 hours"
  }
}
```

**Monday 6pm - Designer 1 sends email:**
```
To: bill@bensley.com, brian@bensley.com
Subject: Daily Work Report - BK-001 - Nov 12

Today I completed:
- Villa south facade elevation (7.5 hours)
- Started window sections (1.5 hours)

Photos attached (3)

Issue: Need window frame material clarification

Tomorrow: Finish window sections, start north facade
```

**System creates:**
```json
daily_reports/by_date/2024-11-12_daily_reports.json
{
  "Designer 1": {
    "work_completed": ["Villa south facade"],
    "hours_spent": 9.0,
    "photos": 3,
    "issues": ["window material question"]
  }
}
```

**End of week - Analysis:**
- Planned: 40 hours
- Actual: 45 hours logged
- Tasks: 5 assigned, 4 completed
- Issue: Window details taking longer than expected

---

## Key Differences:

| Forward Schedule | Daily Reports |
|-----------------|---------------|
| **What WILL happen** | **What DID happen** |
| Created by managers | Created by staff |
| Updated weekly | Updated daily |
| Planning tool | Accountability tool |
| Estimates | Actuals |
| Task assignments | Work documentation |
| No photos | With photos |

---

## Storage:

**Forward schedules:** JSON files (small, version controlled)
**Daily reports:** JSON files + extracted photos
**Photos:** Organized by date in `09_PHOTOS/daily_progress/`

---

**This dual system provides:**
1. Clear expectations (forward schedule)
2. Accountability (daily reports)
3. Photo documentation (progress tracking)
4. Planned vs actual analysis
5. Early warning of issues
6. Data for performance reviews
