# Email Cleanup Agent - Fix Duplicates & Consolidate Categories

> Issues: #316, #317 | Priority: P1 | Branch: `fix/email-cleanup-316`

---

## CONTEXT

Two related email system issues:

### #316 - Duplicate Suggestions
Pattern linker creates `link_review` suggestion, then GPT creates `email_link` for same email. Bill sees duplicates in review queue.

### #317 - Three Category Systems
Emails have THREE different category fields:
- `emails.primary_category`
- `emails.email_type`
- `email_content.category`

Should be ONE system.

---

## PHASE 1: UNDERSTAND (Research First)

### Required Research
```bash
# Check duplicate suggestions (#316)
sqlite3 database/bensley_master.db "
SELECT email_id, suggestion_type, COUNT(*) as count
FROM ai_suggestions
GROUP BY email_id, suggestion_type
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 10;"

# Check category systems (#317)
sqlite3 database/bensley_master.db "
SELECT
  e.primary_category,
  e.email_type,
  ec.category,
  COUNT(*)
FROM emails e
LEFT JOIN email_content ec ON e.email_id = ec.email_id
GROUP BY e.primary_category, e.email_type, ec.category
LIMIT 20;"

# Find where suggestions are created
grep -r "INSERT.*ai_suggestions\|create.*suggestion" backend --include="*.py" | head -20
```

### Questions to Answer
1. Where are `link_review` suggestions created?
2. Where are `email_link` suggestions created?
3. Is there a check before insertion?
4. Which category field is actually used?

### Files to Read
- `backend/services/pattern_first_linker.py` - Creates link_review
- `backend/services/suggestion_writer.py` - Creates suggestions
- `backend/services/email_orchestrator.py` - Orchestrates flow
- `backend/api/routers/emails.py` - Which category used?

**STOP HERE** until you understand the flow.

---

## PHASE 2: THINK HARD (Planning)

### Why Duplicates Happen (#316)
```
Email arrives
    ↓
Pattern Linker → Creates link_review (0.75 confidence)
    ↓
Email still marked needs_gpt = true
    ↓
GPT Analyzer → Creates email_link (0.82 confidence)
    ↓
Both in queue → Bill sees duplicates
```

### Category Consolidation (#317)
Pick ONE source of truth:
- `emails.primary_category` - Most used
- Deprecate `email_type` and `email_content.category`

### Solution Approach
1. Add dedup check in suggestion creation
2. Set `needs_gpt = false` when pattern matches
3. Consolidate to `primary_category`
4. Clean up existing duplicates

---

## PHASE 3: IMPLEMENT

### #316 - Add Dedup Check
```python
# backend/services/suggestion_writer.py
async def create_suggestion(db, email_id, suggestion_type, ...):
    # Check for existing
    existing = db.execute("""
        SELECT suggestion_id, confidence FROM ai_suggestions
        WHERE email_id = ? AND suggestion_type = ? AND status = 'pending'
    """, (email_id, suggestion_type)).fetchone()

    if existing:
        if confidence > existing['confidence']:
            # Update with higher confidence
            db.execute("UPDATE ai_suggestions SET confidence = ? WHERE suggestion_id = ?",
                       (confidence, existing['suggestion_id']))
        return None  # Skip duplicate

    # Create new
    ...
```

### #316 - Skip GPT When Pattern Matches
```python
# backend/services/pattern_first_linker.py
if result['matched']:
    await create_suggestion(...)
    # Mark as processed - skip GPT
    db.execute("UPDATE emails SET needs_gpt = 0 WHERE email_id = ?", (email_id,))
```

### #317 - Consolidate Categories
```sql
-- Migrate email_type to primary_category where needed
UPDATE emails
SET primary_category = email_type
WHERE primary_category IS NULL AND email_type IS NOT NULL;

-- After migration, email_type can be deprecated
-- (don't delete column yet, just stop using it)
```

### Cleanup Scripts
Create `scripts/core/cleanup_duplicate_suggestions.py`:
```python
def cleanup_duplicates(db, dry_run=True):
    """Keep highest confidence, delete rest"""
    ...
```

### Files to Modify
| File | Action | Purpose |
|------|--------|---------|
| `backend/services/suggestion_writer.py` | Modify | Add dedup check |
| `backend/services/pattern_first_linker.py` | Modify | Set needs_gpt=false |
| `scripts/core/cleanup_duplicate_suggestions.py` | Create | One-time cleanup |
| `scripts/migrations/consolidate_email_categories.sql` | Create | Category migration |

---

## PHASE 4: VERIFY

### Testing Checklist
- [ ] New suggestions don't create duplicates
- [ ] Pattern-matched emails skip GPT
- [ ] Existing duplicates cleaned up
- [ ] Category queries use single field
- [ ] Review queue shows no duplicates

### Verification Commands
```bash
# Check duplicates
sqlite3 database/bensley_master.db "
SELECT email_id, COUNT(*) as dups FROM ai_suggestions
WHERE status = 'pending' GROUP BY email_id HAVING COUNT(*) > 1;"

# Run cleanup dry run
python scripts/core/cleanup_duplicate_suggestions.py --dry-run
```

### Success Criteria
- 0 duplicate suggestions
- Pattern-matched emails don't trigger GPT
- Single category system in use

---

## PHASE 5: COMPLETE

### Commit Format
```bash
git commit -m "fix(emails): prevent duplicate suggestions and consolidate categories

- Add dedup check in suggestion_writer.py (#316)
- Set needs_gpt=false when pattern matches (#316)
- Consolidate to primary_category (#317)
- Add cleanup script for existing duplicates

Fixes #316, #317"
```

---

## CONSTRAINTS

- **Don't lose high-confidence suggestions**
- **Don't break existing flow**
- **Log all decisions**
- **Cleanup is reversible**

---

## RESOURCES

- `.claude/plans/system-architecture-ux.md` - Appendix F: Email Pipeline
- Issues #316, #317 for scope
- `backend/services/pattern_first_linker.py` - Pattern matching logic
