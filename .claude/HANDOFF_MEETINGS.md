# Meetings & Transcripts Integration Handoff

**Issue:** #154
**Created:** 2025-12-26
**Status:** Ready for pickup

---

## Your Mission

Integrate meetings and transcripts into the proposals and projects pages so Bill can see:
1. What meetings happened for each proposal
2. What was discussed (transcript summaries)
3. What action items came out of meetings

---

## Quick Start

```bash
# 1. Read this file
cat .claude/HANDOFF_MEETINGS.md

# 2. Check the issue
gh issue view 154

# 3. Audit current state
sqlite3 database/bensley_master.db "
SELECT 'Meetings:' as tbl, COUNT(*) FROM meetings
UNION SELECT 'Transcripts:', COUNT(*) FROM meeting_transcripts;
"

# 4. Create your branch
git checkout -b feat/meetings-proposals-154
```

---

## Database Schema

### meetings (7 records)
```sql
meeting_id INTEGER PRIMARY KEY
title TEXT
meeting_date DATE
meeting_type TEXT  -- 'client', 'internal', 'site_visit', 'review'
project_code TEXT  -- links to proposals.project_code
proposal_id INTEGER  -- links to proposals.proposal_id
participants TEXT  -- JSON array
transcript_id INTEGER  -- links to meeting_transcripts.id (NOT USED)
notes TEXT
outcome TEXT
```

### meeting_transcripts (28 records)
```sql
id INTEGER PRIMARY KEY
meeting_title TEXT
meeting_date TEXT
detected_project_code TEXT  -- auto-detected from transcript
proposal_id INTEGER  -- links to proposals.proposal_id (only 4 linked)
transcript TEXT  -- full transcript text
summary TEXT  -- AI-generated summary
key_points TEXT  -- JSON array
action_items TEXT  -- JSON array of {task, assignee, due_date}
duration_seconds REAL
```

---

## Current Linking Stats

```
Meetings → Proposals: 3/7 (43%)
Meetings → Projects: 6/7 (86%)
Transcripts → Proposals: 4/28 (14%)  <-- BIG GAP
Transcripts → Projects: 18/28 (64%)
```

---

## What Needs to Happen

### 1. Link Orphan Transcripts to Proposals
```sql
-- Find linkable transcripts
SELECT mt.id, mt.meeting_title, mt.detected_project_code, p.proposal_id
FROM meeting_transcripts mt
JOIN proposals p ON mt.detected_project_code = p.project_code
WHERE mt.proposal_id IS NULL;

-- Link them
UPDATE meeting_transcripts
SET proposal_id = (SELECT proposal_id FROM proposals WHERE project_code = detected_project_code)
WHERE proposal_id IS NULL AND detected_project_code IS NOT NULL;
```

### 2. Add Meetings Section to Proposal Detail Page

Location: `frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx`

Add after the email section:
```tsx
{/* Meetings & Transcripts */}
<Card>
  <CardHeader>
    <CardTitle>Meetings</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Show meetings linked to this proposal */}
    {/* Show transcript summaries */}
    {/* Show action items */}
  </CardContent>
</Card>
```

### 3. Create API Endpoint for Proposal Meetings

Create or modify: `backend/api/routers/proposals.py`

```python
@router.get("/proposals/{project_code}/meetings")
async def get_proposal_meetings(project_code: str):
    """Get meetings and transcripts for a proposal"""
    # Get meetings
    # Get transcripts
    # Combine and return
```

### 4. Add Meetings to Project Detail Page

Location: `frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx`

Similar to proposals - show meetings and transcripts for this project.

---

## API Endpoints Available

### Meetings
- `GET /api/meetings` - List meetings
- `GET /api/meetings/{id}` - Single meeting
- `GET /api/meetings/stats` - Meeting stats
- `POST /api/meetings` - Create meeting

### Transcripts
- `GET /api/meeting-transcripts` - List transcripts
- `GET /api/meeting-transcripts/{id}` - Single transcript
- `GET /api/meeting-transcripts/by-project/{code}` - Project transcripts
- `POST /api/meeting-transcripts/{id}/claude-summary` - Save AI summary

---

## Files You'll Touch

### Backend (if needed)
- `backend/api/routers/proposals.py` - Add meetings endpoint
- `backend/api/routers/meetings.py` - Already exists
- `backend/api/routers/transcripts.py` - Already exists

### Frontend
- `frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx`
- `frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx`
- `frontend/src/lib/api.ts` - Add new API calls
- `frontend/src/lib/types.ts` - Add types

### New Components Maybe
- `frontend/src/components/proposals/meetings-section.tsx`
- `frontend/src/components/proposals/transcript-card.tsx`

---

## Testing

```bash
# Start backend
cd backend && uvicorn api.main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Test meetings API
curl http://localhost:8000/api/meetings | python -m json.tool

# Test transcripts API
curl http://localhost:8000/api/meeting-transcripts | python -m json.tool

# Build check
cd frontend && npm run build
```

---

## When You're Done

1. Create PR referencing #154
2. Update this handoff file if needed
3. Close sub-issues you created
4. Update `.claude/STATUS.md`

---

## Questions?

Check these for context:
- `docs/ARCHITECTURE.md` - System overview
- `docs/ROADMAP.md` - Where this fits
- `.claude/STATUS.md` - Current state
- `CLAUDE.md` - Workflow rules
