# URGENT FIXES - Claude 4 (Proposals)

**Your Task:** Fix 2 critical bugs in proposals tracker
**Time:** 45 minutes
**Priority:** BLOCKING - Bill can't use proposals page

---

## 🚨 BUG #1: Proposal Status Update Broken

**Error When Saving:** "no such column updated_BY"

**Root Cause:** Typo in SQL query - using `updated_BY` (uppercase) instead of `updated_by` (lowercase)

**Database Status:** ✅ Column exists as `updated_by` (lowercase)

### Fix Instructions:

1. **Search for the bug:**
```bash
cd backend/services
grep -r "updated_BY" .
```

2. **Find and fix:** Likely in `proposal_tracker_service.py`

**WRONG CODE:**
```python
cursor.execute("""
    UPDATE proposals
    SET status = ?, updated_BY = ?, updated_at = CURRENT_TIMESTAMP
    WHERE project_code = ?
""", (new_status, user_id, project_code))
```

**CORRECT CODE:**
```python
cursor.execute("""
    UPDATE proposals
    SET status = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
    WHERE project_code = ?
""", (new_status, user_id, project_code))
```

3. **Test the fix:**
```bash
# Restart backend
cd backend
uvicorn api.main:app --reload --port 8000

# Test in browser:
# - Open http://localhost:3002/tracker
# - Change a proposal status
# - Click "Save Changes"
# - Should succeed without error
```

---

## 🚨 BUG #2: Project Names Not Showing

**Problem:** Multiple locations show project CODE but not project NAME:
- Proposals tracker table: "Project Name" column is empty
- All proposal rows just show code like "25-BK-018" with no name

**Root Cause:** Backend API not returning `project_name` from database

### Fix Instructions:

#### Backend Fix (proposal_tracker_service.py):

**Find the query that gets proposals list** (likely `get_all_proposals()` or similar)

**CURRENT (Wrong):**
```python
cursor.execute("""
    SELECT
        p.project_code,
        p.status,
        p.project_value,
        p.client_company
        -- Missing project_name!
    FROM proposals p
""")
```

**UPDATED (Correct):**
```python
cursor.execute("""
    SELECT
        p.project_code,
        p.project_name,           -- ADD THIS
        p.status,
        p.project_value,
        p.client_company
    FROM proposals p
    ORDER BY p.created_at DESC
""")
```

**Alternative (if project_name empty in proposals table):**
```python
cursor.execute("""
    SELECT
        p.project_code,
        p.project_name,
        COALESCE(p.project_name, proj.name, p.project_code) as display_name,  -- Fallback to projects table
        p.status,
        p.project_value,
        p.client_company
    FROM proposals p
    LEFT JOIN projects proj ON p.project_code = proj.code
    ORDER BY p.created_at DESC
""")
```

#### Frontend Fix (if needed):

**File:** `frontend/src/app/(dashboard)/tracker/page.tsx`

**Make sure the table displays project_name:**
```typescript
<TableCell>{proposal.project_name || proposal.project_code}</TableCell>
```

---

## 🧪 TESTING CHECKLIST

After fixes:

- [ ] Restart backend: `uvicorn api.main:app --reload --port 8000`
- [ ] Open http://localhost:3002/tracker
- [ ] **Test #1:** Change proposal status and save → Should work without error
- [ ] **Test #2:** Check "Project Name" column → Should show actual names not empty
- [ ] **Test #3:** Hover over proposals → Should see full project info
- [ ] No console errors in browser dev tools

---

## 📊 VERIFY DATA

If project names still don't show, check database:

```bash
sqlite3 database/bensley_master.db

-- Check if proposals have project_name
SELECT project_code, project_name FROM proposals LIMIT 10;

-- If empty, populate from projects table
UPDATE proposals
SET project_name = (
    SELECT name FROM projects
    WHERE projects.code = proposals.project_code
)
WHERE project_name IS NULL OR project_name = '';

-- Verify
SELECT project_code, project_name FROM proposals WHERE project_name IS NOT NULL LIMIT 10;
```

---

## 🎯 SUCCESS CRITERIA

✅ Changing proposal status works without "updated_BY" error
✅ All proposals show actual project names in the table
✅ "Project Name" column is populated
✅ Status dropdown saves correctly
✅ No TypeScript or SQL errors

---

## 📝 REPORT BACK

When done, update COORDINATION_MASTER.md:

```markdown
### Claude 4: Proposals Tracker - URGENT FIXES
Status: ✅ FIXED
Date: 2025-11-25

Bugs Fixed:
1. ✅ Proposal status update error (updated_BY → updated_by)
2. ✅ Project names now showing in all locations

Files Modified:
- backend/services/proposal_tracker_service.py (fix SQL typo + add project_name)
- (frontend file if needed)

Testing: All tests pass, no errors
```

---

**TIME ESTIMATE:** 30-45 minutes

**PRIORITY:** URGENT - Fix before Bill's next demo

**Questions?** Check BILL_FEEDBACK_NOVEMBER_25.md for full context
