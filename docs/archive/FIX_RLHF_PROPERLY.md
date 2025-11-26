# Fix RLHF Feedback System - Make It Actually Useful

**Problem:** Current RLHF is just thumbs up/down with no context
**User Feedback:** "we would need to add some context and some ability to say like this isn't working etc"

---

## What RLHF Should Actually Be

### Current (Useless):
```
[👍] [👎]
```

### Required (Useful):
```
Was this helpful? [👍 Yes] [👎 No] [⚠️ Something's Wrong]

[If thumbs down or something's wrong, show:]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
What's the issue?
┌─────────────────────────────────────┐
│ □ Incorrect data                    │
│ □ Wrong calculation                 │
│ □ Feature not working               │
│ □ Confusing/unclear                 │
│ ☑ Other (explain below)             │
└─────────────────────────────────────┘

Additional context (required):
┌─────────────────────────────────────┐
│ The outstanding invoice number is   │
│ different from what shows in the    │
│ widget below. Should be $4.87M but  │
│ showing $5.47M                       │
└─────────────────────────────────────┘

Expected value (optional):
[                                      ]

[Submit Feedback] [Cancel]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Implementation

### Backend Changes

**File:** `backend/services/training_data_service.py`

**Add new fields to feedback:**
```python
def log_feedback(
    self,
    feature_type: str,
    feature_id: str,
    helpful: bool,
    issue_type: Optional[str] = None,  # NEW: 'incorrect_data', 'wrong_calculation', etc.
    feedback_text: str = None,          # REQUIRED for negative feedback
    expected_value: Optional[str] = None,  # NEW: What user expected
    current_value: Optional[str] = None,   # NEW: What system shows
    context: Optional[Dict] = None
) -> int:
    """
    Log user feedback with context

    Args:
        helpful: True/False
        issue_type: Category of issue (if helpful=False)
        feedback_text: REQUIRED explanation if helpful=False
        expected_value: What user expected to see
        current_value: What system actually shows
    """
    if not helpful and not feedback_text:
        raise ValueError("feedback_text is REQUIRED when helpful=False")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO training_data (
            timestamp, user_id, feature_type, feature_id,
            helpful, issue_type, feedback_text,
            expected_value, current_value, context_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        'bill',
        feature_type,
        feature_id,
        helpful,
        issue_type,
        feedback_text,
        expected_value,
        current_value,
        json.dumps(context) if context else None
    ))

    conn.commit()
    conn.close()
    return cursor.lastrowid
```

**Update database schema:**
```sql
ALTER TABLE training_data ADD COLUMN issue_type TEXT;
ALTER TABLE training_data ADD COLUMN expected_value TEXT;
ALTER TABLE training_data ADD COLUMN current_value TEXT;
```

---

### Frontend Component

**File:** `frontend/src/components/ui/feedback-buttons.tsx`

**Complete rewrite:**
```typescript
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { ThumbsUp, ThumbsDown, AlertTriangle } from 'lucide-react'
import { api } from '@/lib/api'

interface FeedbackButtonsProps {
  featureType: string
  featureId: string
  currentValue?: any
  compact?: boolean
  onFeedbackSubmit?: (feedback: any) => void
}

export function FeedbackButtons({
  featureType,
  featureId,
  currentValue,
  compact = false,
  onFeedbackSubmit
}: FeedbackButtonsProps) {
  const [showDialog, setShowDialog] = useState(false)
  const [feedbackType, setFeedbackType] = useState<'positive' | 'negative' | 'issue' | null>(null)
  const [issueTypes, setIssueTypes] = useState({
    incorrect_data: false,
    wrong_calculation: false,
    not_working: false,
    confusing: false,
    other: false
  })
  const [feedbackText, setFeedbackText] = useState('')
  const [expectedValue, setExpectedValue] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleThumbsUp = async () => {
    setSubmitting(true)
    try {
      await api.logFeedback({
        feature_type: featureType,
        feature_id: featureId,
        helpful: true,
        current_value: currentValue?.toString()
      })
      onFeedbackSubmit?.({ helpful: true })
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const handleThumbsDown = () => {
    setFeedbackType('negative')
    setShowDialog(true)
  }

  const handleIssue = () => {
    setFeedbackType('issue')
    setShowDialog(true)
  }

  const handleSubmitFeedback = async () => {
    if (!feedbackText.trim()) {
      alert('Please provide details about the issue')
      return
    }

    setSubmitting(true)
    try {
      const selectedIssues = Object.entries(issueTypes)
        .filter(([_, selected]) => selected)
        .map(([type, _]) => type)

      await api.logFeedback({
        feature_type: featureType,
        feature_id: featureId,
        helpful: false,
        issue_type: selectedIssues.join(', '),
        feedback_text: feedbackText,
        expected_value: expectedValue || null,
        current_value: currentValue?.toString() || null,
        context: {
          feedback_type: feedbackType,
          timestamp: new Date().toISOString()
        }
      })

      onFeedbackSubmit?.({
        helpful: false,
        issue_type: selectedIssues,
        feedback_text: feedbackText
      })

      // Reset and close
      setShowDialog(false)
      setFeedbackText('')
      setExpectedValue('')
      setIssueTypes({
        incorrect_data: false,
        wrong_calculation: false,
        not_working: false,
        confusing: false,
        other: false
      })
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      alert('Failed to submit feedback. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <div className={compact ? "flex gap-1" : "flex gap-2"}>
        <Button
          variant="ghost"
          size={compact ? "sm" : "default"}
          onClick={handleThumbsUp}
          disabled={submitting}
          className="hover:bg-green-50"
        >
          <ThumbsUp className={compact ? "h-3 w-3" : "h-4 w-4"} />
        </Button>
        <Button
          variant="ghost"
          size={compact ? "sm" : "default"}
          onClick={handleThumbsDown}
          disabled={submitting}
          className="hover:bg-red-50"
        >
          <ThumbsDown className={compact ? "h-3 w-3" : "h-4 w-4"} />
        </Button>
        {!compact && (
          <Button
            variant="ghost"
            size="default"
            onClick={handleIssue}
            disabled={submitting}
            className="hover:bg-yellow-50"
          >
            <AlertTriangle className="h-4 w-4 mr-2" />
            Report Issue
          </Button>
        )}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {feedbackType === 'issue' ? 'Report an Issue' : 'What\'s wrong?'}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            {/* Issue Type Checkboxes */}
            <div className="space-y-2">
              <Label>What's the issue? (select all that apply)</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="incorrect_data"
                    checked={issueTypes.incorrect_data}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, incorrect_data: checked as boolean }))
                    }
                  />
                  <label htmlFor="incorrect_data" className="text-sm cursor-pointer">
                    Incorrect data
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="wrong_calculation"
                    checked={issueTypes.wrong_calculation}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, wrong_calculation: checked as boolean }))
                    }
                  />
                  <label htmlFor="wrong_calculation" className="text-sm cursor-pointer">
                    Wrong calculation
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="not_working"
                    checked={issueTypes.not_working}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, not_working: checked as boolean }))
                    }
                  />
                  <label htmlFor="not_working" className="text-sm cursor-pointer">
                    Feature not working
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="confusing"
                    checked={issueTypes.confusing}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, confusing: checked as boolean }))
                    }
                  />
                  <label htmlFor="confusing" className="text-sm cursor-pointer">
                    Confusing/unclear
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="other"
                    checked={issueTypes.other}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, other: checked as boolean }))
                    }
                  />
                  <label htmlFor="other" className="text-sm cursor-pointer">
                    Other
                  </label>
                </div>
              </div>
            </div>

            {/* Feedback Text - REQUIRED */}
            <div className="space-y-2">
              <Label htmlFor="feedback">
                Explain the issue <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="feedback"
                placeholder="E.g., The outstanding invoice number is different from what shows in the widget below. Should be $4.87M but showing $5.47M"
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                rows={4}
                className="resize-none"
                required
              />
              <p className="text-xs text-muted-foreground">
                Please provide as much detail as possible
              </p>
            </div>

            {/* Current Value Display */}
            {currentValue && (
              <div className="space-y-2">
                <Label>Current value shown:</Label>
                <div className="p-2 bg-gray-50 rounded border text-sm">
                  {currentValue.toString()}
                </div>
              </div>
            )}

            {/* Expected Value */}
            <div className="space-y-2">
              <Label htmlFor="expected">Expected value (optional)</Label>
              <Input
                id="expected"
                placeholder="What you expected to see"
                value={expectedValue}
                onChange={(e) => setExpectedValue(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDialog(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmitFeedback}
              disabled={submitting || !feedbackText.trim()}
            >
              {submitting ? 'Submitting...' : 'Submit Feedback'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
```

---

## Usage Examples

### In KPI Cards:
```typescript
<div className="kpi-card">
  <h3>Outstanding Invoices</h3>
  <p className="text-3xl">${kpis.outstanding_invoices.toLocaleString()}</p>

  <FeedbackButtons
    featureType="kpi_outstanding_invoices"
    featureId="dashboard"
    currentValue={kpis.outstanding_invoices}
    compact={true}
  />
</div>
```

### In Email Category:
```typescript
<div className="flex items-center gap-2">
  <Badge>{email.category}</Badge>

  <FeedbackButtons
    featureType="email_category"
    featureId={email.email_id}
    currentValue={email.category}
    onFeedbackSubmit={(feedback) => {
      if (!feedback.helpful) {
        console.log('User reported issue:', feedback.feedback_text)
        // Optionally: highlight for review
      }
    }}
  />
</div>
```

---

## What Gets Logged

**Positive Feedback:**
```json
{
  "feature_type": "kpi_outstanding_invoices",
  "feature_id": "dashboard",
  "helpful": true,
  "current_value": "5474223.75"
}
```

**Negative Feedback with Context:**
```json
{
  "feature_type": "kpi_outstanding_invoices",
  "feature_id": "dashboard",
  "helpful": false,
  "issue_type": "incorrect_data, wrong_calculation",
  "feedback_text": "The outstanding invoice number is different from what shows in the widget below. Should be $4.87M but showing $5.47M. The invoice aging widget shows the correct number.",
  "expected_value": "4870000",
  "current_value": "5474223.75",
  "context": {
    "feedback_type": "negative",
    "timestamp": "2025-11-25T02:30:00Z"
  }
}
```

---

## Benefits

1. **Actionable Feedback** - Know exactly what's wrong
2. **Categorized Issues** - Can filter by issue type
3. **Expected vs Actual** - Can see what user wanted
4. **Training Data** - Useful for Phase 2 ML improvements
5. **Bug Tracking** - Doubles as issue reporting system

---

## Phase 2 Use

With this data, you can:
- **Fine-tune models** on correct vs incorrect examples
- **Identify patterns** in what users find confusing
- **Prioritize fixes** by issue frequency
- **A/B test improvements** and measure feedback quality

---

This is REAL RLHF, not just thumbs up/down!
