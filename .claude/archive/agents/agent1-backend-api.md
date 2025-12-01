# Agent 1: Backend API Development

**Role:** Build missing API endpoints for the BDS Operations Platform
**Owner:** All files in `backend/`
**Do NOT touch:** `frontend/`, `voice_transcriber/`, deployment configs

---

## Context

You are building REST API endpoints for a FastAPI backend. The database is SQLite at `database/bensley_master.db`. There are 93+ existing endpoints in `backend/api/main.py`.

**Read these files FIRST:**
1. `CLAUDE.md` - Project context
2. `.claude/CODEBASE_INDEX.md` - Where things live
3. `backend/api/main.py` - Existing endpoints (skim for patterns)

---

## Your Tasks (Priority Order)

### P0: Meeting Transcripts API (Do First)

**File to edit:** `backend/api/main.py`

Create these endpoints:

```python
@app.get("/api/meeting-transcripts")
async def list_meeting_transcripts(
    project_code: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List meeting transcripts, optionally filtered by project.

    Database table: meeting_transcripts
    Columns: id, audio_filename, transcript, summary, key_points, action_items,
             detected_project_code, match_confidence, meeting_type, participants,
             sentiment, duration_seconds, recorded_date, processed_date, created_at
    """
    pass

@app.get("/api/meeting-transcripts/{transcript_id}")
async def get_transcript(transcript_id: int):
    """
    Get full transcript details including action items.
    Returns all columns from meeting_transcripts table.
    """
    pass

@app.get("/api/meeting-transcripts/{transcript_id}/action-items")
async def get_transcript_action_items(transcript_id: int):
    """
    Get just the action items from a transcript.
    The action_items column is JSON: [{"task": "...", "owner": "...", "deadline": "..."}]
    """
    pass
```

**Test queries to verify data exists:**
```sql
SELECT COUNT(*) FROM meeting_transcripts;  -- Should be 10
SELECT id, audio_filename, detected_project_code, summary FROM meeting_transcripts LIMIT 3;
```

---

### P0: Unified Timeline API (Do Second)

**File to edit:** `backend/api/main.py`

This is THE most important endpoint - combines all communications for a project.

```python
@app.get("/api/projects/{project_code}/unified-timeline")
async def get_unified_timeline(
    project_code: str,
    types: Optional[str] = None,  # Comma-separated: "email,meeting,rfi,invoice"
    limit: int = 50,
    offset: int = 0
):
    """
    Get ALL communications for a project in chronological order.

    Combines data from:
    1. emails (via email_project_links) - type: "email"
    2. meeting_transcripts - type: "meeting"
    3. rfis - type: "rfi"
    4. invoices - type: "invoice"
    5. project_milestones - type: "milestone"

    Returns:
    {
        "project_code": "22 BK-095",
        "total_events": 45,
        "events": [
            {
                "type": "meeting",
                "date": "2025-11-26T14:30:00",
                "title": "Client Call - Stone Architrave Discussion",
                "summary": "Discussed stone architrave changes...",
                "data": { /* full meeting_transcript record */ },
                "id": 10
            },
            {
                "type": "email",
                "date": "2025-11-22T18:24:54",
                "title": "RE: Stone Architrave Setting-Out Plan",
                "summary": "Client requesting clarification...",
                "data": { /* email record */ },
                "id": 40966
            },
            // ... more events
        ]
    }

    ORDER BY date DESC (most recent first)
    """
    pass
```

**Implementation hints:**
```python
# Query emails linked to project
cursor.execute("""
    SELECT e.*, 'email' as event_type
    FROM emails e
    JOIN email_project_links epl ON e.email_id = epl.email_id
    JOIN projects p ON epl.project_id = p.project_id
    WHERE p.project_code = ?
""", (project_code,))

# Query meeting transcripts
cursor.execute("""
    SELECT *, 'meeting' as event_type
    FROM meeting_transcripts
    WHERE detected_project_code = ? OR detected_project_code LIKE ?
""", (project_code, f"%{project_code}%"))

# Query RFIs
cursor.execute("""
    SELECT *, 'rfi' as event_type
    FROM rfis
    WHERE project_code = ?
""", (project_code,))

# Combine and sort by date
```

---

### P1: RFI Endpoint Improvements

**File to edit:** `backend/api/main.py`

Find the existing `/api/rfis` endpoint and enhance it:

```python
@app.get("/api/rfis")
async def list_rfis(
    project_code: Optional[str] = None,
    status: Optional[str] = None,  # "open", "answered", "overdue"
    overdue_only: bool = False,
    limit: int = 50
):
    """
    Enhanced RFI listing with filters.

    Database table: rfis
    Key columns: rfi_id, project_code, subject, date_sent, date_due,
                 date_responded, status, priority

    An RFI is "overdue" if: status = 'open' AND date_due < today
    """
    pass
```

---

### P1: Milestones Endpoint Improvements

**File to edit:** `backend/api/main.py`

```python
@app.get("/api/milestones")
async def list_milestones(
    project_code: Optional[str] = None,
    upcoming_days: Optional[int] = None,  # e.g., 14 for next 2 weeks
    status: Optional[str] = None,  # "pending", "complete", "overdue"
    limit: int = 50
):
    """
    Enhanced milestone listing with date filters.

    Database table: project_milestones
    Key columns: milestone_id, project_code, phase, milestone_name,
                 planned_date, actual_date, status

    NOTE: Most milestones have NULL planned_date currently.
    Return milestones even if planned_date is NULL (show all).
    """
    pass
```

---

### P2: Finance KPIs Endpoint

**File to edit:** `backend/api/main.py`

```python
@app.get("/api/finance/kpis")
async def get_finance_kpis():
    """
    Calculate live finance KPIs for dashboard.

    Returns:
    {
        "total_outstanding": 4870000.00,  # Sum of unpaid invoices
        "avg_days_to_pay": 42,            # Average days from issue to payment
        "critical_count": 15,             # Invoices > 90 days overdue
        "collection_rate": 0.94,          # Paid / Total issued this year
        "as_of": "2025-11-26T14:30:00"
    }

    Use invoices table. Outstanding = where paid = 0 or paid IS NULL.
    """
    pass
```

---

## Code Patterns to Follow

Look at existing endpoints in `main.py` for patterns. Example:

```python
@app.get("/api/invoices")
async def list_invoices(
    project_code: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM invoices WHERE 1=1"
        params = []

        if project_code:
            query += " AND project_code = ?"
            params.append(project_code)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY invoice_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = [dict(row) for row in rows]
        conn.close()

        return {"total": len(results), "invoices": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Testing Your Endpoints

After adding each endpoint, test with curl:

```bash
# Test meeting transcripts
curl http://localhost:8000/api/meeting-transcripts
curl http://localhost:8000/api/meeting-transcripts?project_code=22%20BK-095

# Test unified timeline
curl http://localhost:8000/api/projects/22%20BK-095/unified-timeline

# Test RFIs
curl http://localhost:8000/api/rfis?status=open

# Test milestones
curl http://localhost:8000/api/milestones?upcoming_days=14
```

---

## Database Quick Reference

```sql
-- Check what tables exist
.tables

-- Key tables you'll query:
-- meeting_transcripts (10 records)
-- emails (3,356 records)
-- email_project_links (links emails to projects)
-- rfis (3 records)
-- project_milestones (110 records)
-- invoices (253 records)
-- projects (54 records)

-- Find a project
SELECT project_id, project_code, project_title FROM projects LIMIT 5;
```

---

## When You're Done

1. Test all endpoints locally
2. Update `.claude/CODEBASE_INDEX.md` with new endpoints
3. Tell Agent 2 (Frontend) that APIs are ready
4. Move to P1 tasks if time remains

---

## Do NOT

- Touch frontend files
- Modify database schema (ask Agent 4)
- Deploy anything (Agent 3's job)
- Add complex AI features (Agent 5's job)

---

**Estimated Time:** 8-10 hours total
**Start:** P0 tasks immediately
**Checkpoint:** After unified-timeline endpoint works
