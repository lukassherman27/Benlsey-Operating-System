# Plan: Suggestion Review UI - Fix & Enhance

**Issue**: #292 (closed prematurely - reopening with actual fixes needed)
**Date**: 2025-12-31
**Author**: Claude Agent

---

## Executive Summary

The suggestion review UI EXISTS but is **broken at the data layer**. Approving suggestions doesn't actually create email links because the handler can't find `proposal_id` in the data.

---

## What I Found (Audit Results)

### Critical Bug: Data Format Mismatch

| System | Creates suggestions? | Includes proposal_id in suggested_data? |
|--------|---------------------|----------------------------------------|
| `suggestion_writer.py` | Yes | **YES** (line 478) |
| `claude_email_analyzer.py` | Yes | **NO** (lines 332-342) |
| `pattern_first_linker.py` | Yes | **YES** (line 805) |

The `claude_email_analyzer.py` script creates suggestions WITHOUT `proposal_id` in the JSON:
```python
suggestion_data = {
    'email_id': email_id,
    'sender': ...,
    'project_code': top['project_code'],  # Has this
    # NO proposal_id here!  <-- BUG
}
```

But `email_link_handler.py` validates (lines 47-51):
```python
if not proposal_id and not project_id:
    errors.append("Either proposal_id or project_id is required")
```

### Database Evidence

| Metric | Value | Problem |
|--------|-------|---------|
| Applied suggestions with null rollback_data | 688 | Handler never ran |
| Applied suggestions with null target_id | 688 | No record of what got linked |
| Applied suggestions with null reviewed_by | 258 | Never properly reviewed |
| Pending email_link suggestions | 18 | Some have bad data format |

### The Frontend Is Fine

The existing `/admin/suggestions` page has:
- Keyboard shortcuts (a/r/j/k/arrows)
- Bulk approve/reject
- Multiple view modes
- Pattern learning integration

The problem is in the **backend data flow**, not the UI.

---

## Research: What Top Companies Do

From [UXPin](https://www.uxpin.com/studio/blog/complex-approvals-app-design/), [Macquarie Case Study](https://sreeja-ux-ui-portfolio.webflow.io/projects/bulk-approval), and Gmail workflow guides:

1. **Auto-advance** - After action, automatically move to next item
2. **Keyboard shortcuts** - j/k navigation, single-key actions
3. **Contextual preview** - Show what will happen before action
4. **Bulk processing** - Select multiple, act on all
5. **Decision support** - Show confidence, reasoning, evidence
6. **Progress indicators** - "17 remaining" not just "pending"

Current UI has most of these. Missing: **auto-advance**.

---

## Three Approaches Considered

### Approach A: Fix Data at Write Time (Chosen)
- Add `proposal_id` to `suggested_data` in `claude_email_analyzer.py`
- Simple, fixes the root cause
- New suggestions will work correctly

### Approach B: Fix Handler to Read Row-Level Data
- Modify `email_link_handler.py` to fall back to `suggestion.proposal_id` if not in JSON
- More complex, but fixes existing suggestions
- Risk: inconsistent data sources

### Approach C: Migration Script + Approach A
- Fix the writer (Approach A)
- Run migration to add `proposal_id` to existing suggestions' JSON
- Most complete, but more work

**Decision**: Start with A, add C if needed for existing data.

---

## What I'm NOT Doing

1. **Rebuilding the UI** - It's already well-built
2. **Adding new features** - Focus on fixing what's broken
3. **Changing the handler validation** - It's correct, the data is wrong
4. **Complex migrations** - Fix forward, let old bad data age out

---

## Implementation Plan

### Phase 1: Fix the Bug (5 mins)
1. Edit `scripts/core/claude_email_analyzer.py` line 332-342
2. Add `proposal_id` to `suggestion_data` dict
3. Already looked up proposal_id at line 327, just not included

### Phase 2: Add Auto-Advance (10 mins)
1. In frontend, after approve/reject mutation succeeds:
2. Auto-increment `focusedIndex`
3. If at end of list, refetch and reset to 0

### Phase 3: Verify Handler Works (5 mins)
1. Create a test suggestion manually with correct format
2. Approve it via API
3. Verify link was created AND rollback_data populated

### Phase 4: Clean Up Bad Data (Optional)
1. Mark 688 orphaned "applied" suggestions as "legacy_applied"
2. They have links created by other systems, just mark them cleaned

---

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| Breaking existing flow | Only adding data, not removing |
| Handler still fails | Add logging to see actual errors |
| UI breaks on data change | suggested_data is flexible JSON |

---

## Success Metrics

After fix:
- [ ] New suggestions have proposal_id in suggested_data
- [ ] Approving a suggestion creates actual link
- [ ] rollback_data is populated after apply
- [ ] Auto-advance moves to next item

---

## Files to Modify

1. `scripts/core/claude_email_analyzer.py` - Add proposal_id to suggestion_data
2. `frontend/src/app/(dashboard)/admin/suggestions/page.tsx` - Add auto-advance

---
