# Claude 1: Add RLHF Feedback to Email Categories

## Context
You built the complete email system (100% complete, A+ grade). Now add RLHF feedback collection so users can correct email categories, enabling Phase 2 machine learning.

## Your Previous Work
- ✅ `backend/services/email_service.py` (23KB, comprehensive)
- ✅ 6+ API endpoints for emails
- ✅ `frontend/src/app/(dashboard)/emails/page.tsx` - Email list page
- ✅ Email categorization (9 categories)
- ✅ Email-project linking
- ✅ Recent emails widget for overview dashboard

## What You Need to Add Now

### 1. Add RLHF Feedback Buttons to Email List

**File to Modify:** `frontend/src/app/(dashboard)/emails/page.tsx`

**What to Add:**

#### Import Claude 2's Feedback System
```typescript
import { FeedbackButtons } from '@/components/ui/feedback-buttons'
import { api } from '@/lib/api'
```

#### Add Feedback Next to Each Email Category

**Current (probably something like):**
```typescript
<div className="email-item">
  <span>{email.subject}</span>
  <Badge>{email.category}</Badge>  {/* Current category badge */}
</div>
```

**Updated (add feedback):**
```typescript
<div className="email-item">
  <span>{email.subject}</span>
  <div className="flex items-center gap-2">
    <Badge>{email.category || 'uncategorized'}</Badge>

    <FeedbackButtons
      featureType="email_category"
      featureId={email.email_id}
      originalValue={email.category}
      type="correction"
      options={[
        'contract',
        'invoice',
        'proposal',
        'design_document',
        'correspondence',
        'internal',
        'financial',
        'rfi',
        'presentation'
      ]}
      compact={true}
      onCorrectionSubmit={(newCategory) => {
        // Log correction to training data
        api.logFeedback({
          feature_type: 'email_category',
          feature_id: email.email_id,
          original_value: email.category,
          corrected_value: newCategory,
          context: {
            subject: email.subject,
            from: email.sender_email,
            project_code: email.project_code
          }
        })

        // Update email category in real-time
        updateEmailCategory(email.email_id, newCategory)
      }}
    />
  </div>
</div>
```

---

### 2. Add "Was this helpful?" to Email Summaries

If your email detail view has AI-generated summaries (from email chain summarization), add thumbs up/down:

```typescript
<div className="email-summary">
  <p>{email.ai_summary}</p>

  <FeedbackButtons
    featureType="email_summary"
    featureId={email.email_id}
    type="helpful"
    compact={true}
    onFeedback={(helpful) => {
      api.logFeedback({
        feature_type: 'email_summary',
        feature_id: email.email_id,
        helpful,
        context: { summary_length: email.ai_summary?.length }
      })
    }}
  />
</div>
```

---

### 3. Add Feedback to Email-Project Links

If users can see which project an email is linked to, let them flag wrong links:

```typescript
<div className="email-project-link">
  <span>Linked to: <strong>{email.project_code}</strong></span>

  <FeedbackButtons
    featureType="email_project_link"
    featureId={email.email_id}
    type="helpful"
    compact={true}
    onFeedback={(helpful) => {
      if (!helpful) {
        api.logFeedback({
          feature_type: 'email_project_link',
          feature_id: email.email_id,
          helpful: false,
          feedback_text: 'Incorrect project link',
          context: {
            email_subject: email.subject,
            linked_project: email.project_code
          }
        })
      }
    }}
  />
</div>
```

---

### 4. Update Backend (Optional)

If you want to update email categories in real-time when user corrects them:

**Add to:** `backend/services/email_service.py`

```python
def update_email_category(self, email_id: str, new_category: str, user_id: str = 'bill') -> bool:
    """
    Update email category based on user correction
    Used for RLHF training data collection
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE emails
            SET
                category = ?,
                updated_at = CURRENT_TIMESTAMP,
                updated_by = ?
            WHERE email_id = ?
        """, (new_category, user_id, email_id))

        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating email category: {e}")
        return False
    finally:
        conn.close()
```

**Add API Endpoint:** `backend/api/main.py`

```python
@app.patch("/api/emails/{email_id}/category")
def update_email_category(
    email_id: str,
    category: str = Body(..., embed=True),
    user_id: str = 'bill'
):
    """Update email category based on user correction"""
    service = EmailService()
    success = service.update_email_category(email_id, category, user_id)

    if success:
        return {"success": True, "message": "Category updated"}
    else:
        raise HTTPException(status_code=404, detail="Email not found")
```

**Then call from frontend:**
```typescript
async function updateEmailCategory(emailId: string, newCategory: string) {
  try {
    await api.patch(`/api/emails/${emailId}/category`, { category: newCategory })
    // Refresh email list
    queryClient.invalidateQueries(['emails'])
  } catch (error) {
    console.error('Failed to update category:', error)
  }
}
```

---

## Visual Examples

### Before (Current):
```
─────────────────────────────────────────────
Email: Contract for 25-BK030
From: client@example.com
[correspondence]  ← Just the badge
─────────────────────────────────────────────
```

### After (With RLHF):
```
─────────────────────────────────────────────
Email: Contract for 25-BK030
From: client@example.com
[correspondence] [✏️ Wrong category?]  ← Feedback button
                 ↓ (click shows dropdown)
                 [contract]
                 [invoice]
                 [proposal]
                 ...
─────────────────────────────────────────────
```

---

## Technical Details

### Claude 2's Feedback System (Already Built)

**Frontend Component:**
```typescript
// frontend/src/components/ui/feedback-buttons.tsx
// Already exists, you just need to import it

interface FeedbackButtonsProps {
  featureType: string        // 'email_category', 'email_summary', etc.
  featureId: string          // email.email_id
  type: 'helpful' | 'correction'
  originalValue?: any        // Current category (for corrections)
  options?: string[]         // Dropdown options (for corrections)
  compact?: boolean          // Small buttons for lists
  onFeedback?: (helpful: boolean) => void
  onCorrectionSubmit?: (newValue: any) => void
}
```

**Backend API:**
```python
# backend/api/main.py - Already exists
POST /api/training/feedback
{
  "feature_type": "email_category",
  "feature_id": "email_123",
  "original_value": "correspondence",
  "corrected_value": "contract",
  "context": {...}
}
```

**Frontend API Wrapper:**
```typescript
// frontend/src/lib/api.ts - Already exists
api.logFeedback({
  feature_type: string,
  feature_id: string,
  helpful?: boolean,
  original_value?: any,
  corrected_value?: any,
  feedback_text?: string,
  context?: object
})
```

---

## Where to Add Feedback

### Priority 1: Email Category Corrections (CRITICAL)
This is the most valuable training data for Phase 2 email categorization model.
- **Location:** Email list page, next to every category badge
- **Type:** Correction (dropdown with 9 category options)
- **Impact:** HIGH - Trains AI to categorize emails correctly

### Priority 2: Email-Project Link Validation (HIGH)
Helps improve AI that links emails to projects.
- **Location:** Email detail view, next to project link
- **Type:** Helpful (thumbs up/down)
- **Impact:** MEDIUM - Improves project linking accuracy

### Priority 3: Email Summary Quality (MEDIUM)
If you have AI summaries, collect feedback on quality.
- **Location:** Email detail view, below summary
- **Type:** Helpful (thumbs up/down)
- **Impact:** MEDIUM - Improves summary generation

---

## Email Categories Reference

Your current 9 categories:
1. `contract` - Contract documents, signed agreements
2. `invoice` - Invoices, payment documents
3. `proposal` - Proposals, quotes
4. `design_document` - Design docs, drawings, specifications
5. `correspondence` - General correspondence
6. `internal` - Internal BDS communication
7. `financial` - Financial reports, budgets
8. `rfi` - RFI, submittals, project documents
9. `presentation` - Presentations, pitch decks

---

## Testing Checklist

After implementation, test:

- [ ] Feedback buttons appear next to email categories
- [ ] Clicking "Wrong category?" shows dropdown with 9 options
- [ ] Selecting new category logs to training_data table
- [ ] (Optional) Email category updates in real-time
- [ ] Compact mode works (small buttons for list view)
- [ ] No layout breaking on mobile
- [ ] Console shows no errors
- [ ] Check database: `SELECT * FROM training_data WHERE feature_type = 'email_category'`

---

## Database Verification

After users correct categories, verify data is logged:

```sql
-- Check training data is being collected
SELECT
    feature_type,
    original_value,
    corrected_value,
    timestamp,
    context_json
FROM training_data
WHERE feature_type = 'email_category'
ORDER BY timestamp DESC
LIMIT 10;
```

Should show corrections like:
```
email_category | correspondence | contract | 2025-11-25 | {"subject": "Contract for..."}
```

---

## Phase 2 Impact

**What this enables:**

When Bill corrects email categories, you're collecting training data for:
1. **Fine-tuning:** Llama3 70B fine-tuned on BDS-specific email patterns
2. **RLHF:** Reward model that learns Bill's preferences
3. **Continuous improvement:** System gets smarter as Bill uses it

**Example Training Loop (Phase 2):**
```
1. AI categorizes email as "correspondence"
2. Bill corrects to "contract"
3. System logs correction with context (subject, from, attachments)
4. Phase 2: Fine-tune model on 1,000+ corrections
5. AI learns: "Subject contains 'SoW' + PDF attachment = contract"
6. Future emails auto-categorized correctly
```

---

## Estimated Time: 1-2 hours

- Add feedback buttons to email list: 30 min
- Add email-project link feedback: 20 min
- (Optional) Backend category update: 30 min
- Testing & verification: 20 min

---

## Reference Files

1. **Your work:** `backend/services/email_service.py`, `frontend/src/app/(dashboard)/emails/page.tsx`
2. **Feedback component:** `frontend/src/components/ui/feedback-buttons.tsx` (Claude 2)
3. **RLHF guide:** `RLHF_IMPLEMENTATION_GUIDE.md` (Claude 2's documentation)
4. **API wrapper:** `frontend/src/lib/api.ts` (has logFeedback method)
5. **Claude 4's example:** `frontend/src/app/(dashboard)/tracker/page.tsx` (see how they integrated feedback)

---

## Success Criteria

✅ Feedback buttons appear next to all email categories
✅ Users can correct wrong categories via dropdown
✅ Corrections log to training_data table with context
✅ (Optional) Email categories update in real-time
✅ Compact mode works in list view
✅ No TypeScript errors, no runtime errors
✅ Database shows training_data rows with feature_type = 'email_category'

---

## Questions?

If you encounter issues:
1. Check Claude 2's feedback-buttons.tsx component
2. Look at RLHF_IMPLEMENTATION_GUIDE.md for examples
3. See how Claude 4 integrated feedback in tracker page
4. Verify api.logFeedback() exists in frontend/src/lib/api.ts

---

## Final Note

Your email system is already excellent (A+ grade). This RLHF integration is the cherry on top that enables Phase 2 intelligence. Every correction Bill makes trains the AI to be smarter.

**After you're done, report back in COORDINATION_MASTER.md:**
- Mark your RLHF work as "✅ COMPLETE"
- Note any issues or questions

Great work so far! 🚀
