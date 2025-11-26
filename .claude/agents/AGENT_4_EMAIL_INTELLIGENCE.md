# Agent 4: Email Intelligence & Categorization Fixes

## Your Mission
You are responsible for fixing email categorization, email-proposal linking, and making the system interactive.

## Context
- **Codebase**: Bensley Design Studio Operations Platform
- **Backend**: `backend/services/email_intelligence_service.py` and `backend/api/main.py`
- **Frontend**: `frontend/src/components/proposal-email-intelligence.tsx`
- **Database**: SQLite at `database/bensley_master.db`

## Current State & Problems

### Problem 1: Email Categorization Not Interactive
**Current**: System auto-categorizes emails, but user can't approve/reject
**Need**: Add UI buttons to approve or reject AI categorization

**Example wanted**:
```
Email: "Updated proposal for Wynn Marjan"
AI Categorized as: Proposal ✓ or ✗

[Approve] [Reject] [Recategorize...]
```

### Problem 2: Only Shows "General" Category
**Issue**: When viewing emails, only "general" category appears
**Files**:
- `frontend/src/components/proposal-email-intelligence.tsx`
- `backend/api/main.py` email endpoints (lines 1457-1638)

**Expected**: Show proper categories like:
- contract
- rfi
- proposal
- invoice
- meeting
- technical
- administrative

### Problem 3: Refresh Button Doesn't Work
**Issue**: Clicking refresh/plus icon does nothing
**Fix**: Hook up refresh functionality to re-fetch email categorizations

### Problem 4: No Proposal Selection When Categorizing
**Current**: Can change category, but can't specify WHICH proposal the email belongs to
**Need**: Dropdown to select project/proposal when categorizing

### Problem 5: Email-Proposal Link Manager Issues
**File**: Likely in email management section
**Issues**:
- Only shows auto-linked emails
- No way to search for unlinked emails
- No manual linking UI

**Need**:
- Search/filter for unlinked emails
- Manual link button
- Dropdown to select proposal
- Confidence score display

### Problem 6: Email Formatting Issues
**Various display issues** - need to check and fix UI formatting

## Your Tasks

### Task 1: Make Categorization Interactive
1. Update `frontend/src/components/proposal-email-intelligence.tsx`
2. Add approve/reject buttons for each email:
```typescript
<div className="categorization-actions">
  <span>AI Suggested: {email.ai_category}</span>
  <Button onClick={() => approveCategory(email.id)}>
    ✓ Approve
  </Button>
  <Button onClick={() => rejectCategory(email.id)}>
    ✗ Reject
  </Button>
  <Select onChange={(cat) => recategorize(email.id, cat)}>
    {categories.map(c => <option value={c}>{c}</option>)}
  </Select>
</div>
```

3. Create API endpoints:
   - `POST /api/emails/{id}/approve-category` - Mark as human-approved
   - `POST /api/emails/{id}/reject-category` - Mark as needing review
   - `PUT /api/emails/{id}/category` - Update category

4. Add `human_approved` field to emails table if not exists

### Task 2: Fix Category Display
1. Check `backend/api/main.py` line 1547 (`/api/emails/categories/list`)
2. Verify all categories are returned:
```python
categories = [
    "contract",
    "rfi",
    "proposal",
    "invoice",
    "meeting",
    "technical",
    "administrative",
    "financial",
    "general"
]
```

3. Update frontend to fetch and display all categories
4. Add category badges with color coding

### Task 3: Fix Refresh Button
1. Find refresh button in `proposal-email-intelligence.tsx`
2. Hook up to refetch function:
```typescript
const handleRefresh = async () => {
  setLoading(true)
  await refetch() // React Query refetch
  setLoading(false)
}
```

3. Show loading spinner during refresh

### Task 4: Add Proposal Selection to Categorization
1. Update categorization UI to include proposal dropdown:
```typescript
<Select
  placeholder="Link to proposal..."
  onChange={(projectCode) => linkToProposal(email.id, projectCode)}
>
  {proposals.map(p => (
    <option key={p.project_code} value={p.project_code}>
      {p.project_code} - {p.project_name}
    </option>
  ))}
</Select>
```

2. Create API endpoint:
   - `POST /api/emails/{id}/link-proposal` with body: `{project_code: string}`

3. Update email record with linked proposal

### Task 5: Build Email-Proposal Link Manager
1. Create new component: `frontend/src/components/email-proposal-link-manager.tsx`
2. Features:
   - **Search bar** - filter by sender, subject, date
   - **Filter options**:
     - All emails
     - Linked emails
     - Unlinked emails
     - Low confidence links
   - **Email list** with:
     - From/To
     - Subject
     - Date
     - Current link (if any)
     - Confidence score
     - Manual link button
   - **Manual link modal**:
     - Search proposals by name/code
     - Preview email content
     - Save link with confidence = 1.0 (manual)

3. API endpoints needed:
   - `GET /api/emails/validation-queue` - Get unlinked/low confidence emails
   - `POST /api/emails/{id}/manual-link` - Create manual link

### Task 6: Fix Email Formatting
1. Review all email display components
2. Fix issues:
   - Column widths
   - Text overflow
   - Date formatting
   - Category badge display
3. Make responsive

## Expected Deliverables

1. **Interactive categorization UI** with approve/reject buttons
2. **Fixed category display** showing all categories (not just "general")
3. **Working refresh button** that re-fetches data
4. **Proposal selection dropdown** when categorizing emails
5. **Email-Proposal Link Manager** with search and manual linking
6. **Fixed email formatting** across all components
7. **New API endpoints** for email operations

## Success Criteria

- ✅ Can approve/reject AI categorizations
- ✅ All email categories visible (contract, RFI, proposal, etc.)
- ✅ Refresh button works
- ✅ Can select which proposal when categorizing
- ✅ Can search for unlinked emails
- ✅ Can manually link emails to proposals
- ✅ Email formatting is clean and readable
- ✅ Confidence scores visible for links

## Testing Checklist

- [ ] View email intelligence summary - see all categories
- [ ] Click on email - see approve/reject buttons
- [ ] Approve a categorization - verify it's saved
- [ ] Reject and recategorize - verify new category saved
- [ ] Link email to proposal - verify link created
- [ ] Open link manager - see unlinked emails
- [ ] Search for specific email - find it
- [ ] Manually link email to proposal - verify link saved
- [ ] Check email-proposal links in proposal detail page

## Database Schema Reference

```sql
CREATE TABLE emails (
    email_id INTEGER PRIMARY KEY,
    email_address TEXT,
    subject TEXT,
    body TEXT,
    date_received DATETIME,
    category TEXT,              -- contract/rfi/proposal/etc
    ai_category_confidence REAL,
    human_approved INTEGER DEFAULT 0,  -- Add this if missing
    ...
)

CREATE TABLE email_project_links (
    link_id INTEGER PRIMARY KEY,
    email_id INTEGER,
    project_code TEXT,
    confidence_score REAL,      -- 1.0 = manual, <1.0 = AI
    link_method TEXT,           -- 'manual' or 'ai'
    created_at DATETIME,
    ...
)
```

## Notes
- Coordinate with Agent 1 for proposal data integration
- Coordinate with Agent 3 for meeting extraction from emails
- Use existing `email_intelligence_service.py` where possible
- Test with real email data
