# RLHF Feedback Implementation Guide
**For:** Claudes 1, 2, 3, 5
**Status:** ✅ Infrastructure Ready - Add to Your Widgets
**Created:** 2025-11-25 by Claude 4

---

## 🚀 Quick Start - Infrastructure is Ready!

The RLHF feedback system is **complete and tested**. You can now add feedback buttons to your widgets following this guide.

### What's Already Built

✅ **Backend:**
- `training_data_service` initialized in `backend/api/main.py:119`
- API endpoint: `POST /api/training/feedback` (tested & working)
- Database: `user_feedback` table created with indexes

✅ **Frontend:**
- API function: `api.logFeedback()` in `frontend/src/lib/api.ts:613-630`
- Example implementation in `ProposalTrackerWidget`

✅ **Testing:**
- End-to-end tested with curl and browser
- Feedback successfully saves to database
- 2 test entries already in `user_feedback` table

---

## 📋 Implementation Steps (Copy-Paste Ready)

### Step 1: Add State to Your Widget Component

```typescript
import { useState } from "react";
import { ThumbsUp, ThumbsDown, Check } from "lucide-react";

export function YourWidget({ compact = false }) {
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean | null>(null);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  // ... rest of your component
```

### Step 2: Add handleFeedback Function

```typescript
  const handleFeedback = async (helpful: boolean) => {
    if (feedbackSubmitted !== null || isSubmittingFeedback) return;

    setIsSubmittingFeedback(true);
    try {
      await api.logFeedback({
        user: "anonymous",
        feature: "your_widget_name", // e.g., "invoice_aging", "query_interface"
        action: helpful ? "thumbs_up" : "thumbs_down",
        helpful,
        context: {
          widget_location: "dashboard",
          compact_mode: compact,
          // Add any relevant context from your widget
          // e.g., record_count, data_shown, filters_applied
        },
      });
      setFeedbackSubmitted(helpful);
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    } finally {
      setIsSubmittingFeedback(false);
    }
  };
```

### Step 3: Add Feedback UI to Your Widget

Add this **at the bottom of your CardContent**, before the closing `</CardContent>` tag:

```typescript
        {/* RLHF Feedback Section */}
        <div className={cn(
          "pt-3 border-t border-slate-200",
          "flex items-center justify-between"
        )}>
          <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
            Was this helpful?
          </p>
          <div className="flex gap-2">
            {feedbackSubmitted === null ? (
              <>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleFeedback(true)}
                  disabled={isSubmittingFeedback}
                  className={cn(
                    "h-7 w-7 p-0",
                    ds.hover.button,
                    "hover:bg-green-50 hover:text-green-600"
                  )}
                >
                  <ThumbsUp className="h-3.5 w-3.5" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleFeedback(false)}
                  disabled={isSubmittingFeedback}
                  className={cn(
                    "h-7 w-7 p-0",
                    ds.hover.button,
                    "hover:bg-red-50 hover:text-red-600"
                  )}
                >
                  <ThumbsDown className="h-3.5 w-3.5" />
                </Button>
              </>
            ) : (
              <div className={cn(
                "flex items-center gap-1.5",
                ds.typography.caption,
                "text-green-600"
              )}>
                <Check className="h-3.5 w-3.5" />
                Thanks!
              </div>
            )}
          </div>
        </div>
```

---

## 🎯 Widget-Specific Implementation Plans

### Claude 1: Email System Widgets

**Where to add feedback:**
1. **Recent Emails Widget** - After email list
   - Feature name: `"widget_recent_emails"`
   - Context: `{ email_count, compact_mode, category_filter }`

2. **Email Category Manager** - After correction
   - Feature name: `"email_category_correction"`
   - Context: `{ email_id, original_category, corrected_category }`
   - Use: `api.logFeedback()` on category change

**Special case - Corrections:**
```typescript
// When user corrects an email category:
await api.logFeedback({
  user: "anonymous",
  feature: "email_category",
  action: "correction",
  original_value: originalCategory,
  corrected_value: newCategory,
  entity_type: "email",
  entity_id: emailId,
  context: { confidence: aiConfidence }
});
```

---

### Claude 2: Query Interface

**Where to add feedback:**
1. **Query Results Display** - After results table
   - Feature name: `"query_interface"`
   - Context: `{ query_text, result_count, query_type }`

2. **AI-Generated Summary** - After summary text
   - Feature name: `"query_ai_summary"`
   - Context: `{ query_text, summary_length, confidence }`

**Example for Query Results:**
```typescript
const handleQueryFeedback = async (helpful: boolean) => {
  await api.logFeedback({
    user: "anonymous",
    feature: "query_interface",
    action: helpful ? "thumbs_up" : "thumbs_down",
    helpful,
    context: {
      query_text: currentQuery,
      result_count: results.length,
      execution_time_ms: queryStats.duration,
    }
  });
};
```

---

### Claude 3: Active Projects & Invoice Aging

**Where to add feedback:**
1. **Invoice Aging Widget** - After aging breakdown
   - Feature name: `"invoice_aging"`
   - Context: `{ outstanding_count, overdue_90_count, compact_mode }`

2. **Project Health Scores** - When user adjusts
   - Feature name: `"project_health_adjustment"`
   - Action: `"correction"`
   - Context: `{ project_code, ai_score, user_score }`

**Example for Invoice Widget:**
```typescript
const handleInvoiceFeedback = async (helpful: boolean) => {
  await api.logFeedback({
    user: "anonymous",
    feature: "invoice_aging",
    action: helpful ? "thumbs_up" : "thumbs_down",
    helpful,
    context: {
      compact_mode: compact,
      outstanding_invoices: stats.outstanding_count,
      overdue_90_days: stats.overdue_90_count,
      total_outstanding: stats.total_outstanding_value,
    }
  });
};
```

---

### Claude 5: Overview Dashboard

**Where to add feedback:**
1. **KPI Cards** - After cards section
   - Feature name: `"dashboard_kpi_cards"`
   - Context: `{ cards_shown, data_freshness }`

2. **Quick Actions Widget** - After actions
   - Feature name: `"dashboard_quick_actions"`
   - Context: `{ actions_available }`

**Note:** Individual widgets (emails, proposals, invoices) already have feedback from their respective Claudes. Claude 5 should add feedback only for dashboard-specific components.

---

## 📊 What Data Gets Captured

Every feedback submission saves:

```sql
CREATE TABLE user_feedback (
    feedback_id INTEGER PRIMARY KEY,
    user TEXT,                    -- "anonymous" or username
    feature TEXT,                 -- Widget/feature name
    action TEXT,                  -- "thumbs_up", "thumbs_down", "correction"
    original_value TEXT,          -- For corrections only
    corrected_value TEXT,         -- For corrections only
    helpful INTEGER,              -- 1 = yes, 0 = no, NULL = not rated
    entity_type TEXT,             -- "email", "project", "invoice", etc.
    entity_id INTEGER,            -- ID of the entity
    context TEXT,                 -- JSON with additional data
    created_at DATETIME           -- Timestamp
);
```

---

## 🧪 Testing Your Implementation

### 1. Visual Test
- Open widget in browser
- Look for "Was this helpful?" at bottom
- Click thumbs up → Should show "✓ Thanks!"
- Refresh page → Buttons reset (session-based)

### 2. API Test
```bash
curl -X POST http://localhost:8000/api/training/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user": "test_user",
    "feature": "your_feature_name",
    "action": "thumbs_up",
    "helpful": true
  }'
```

Expected response:
```json
{"success":true,"feedback_id":N,"message":"Feedback logged successfully"}
```

### 3. Database Verification
```bash
sqlite3 database/bensley_master.db "SELECT * FROM user_feedback ORDER BY created_at DESC LIMIT 5;"
```

Should show your feedback entries.

---

## 📝 Example: Full Implementation (ProposalTrackerWidget)

See: `frontend/src/components/dashboard/proposal-tracker-widget.tsx`

**Lines 20-54:** State and handleFeedback function
**Lines 200-249:** Feedback UI section

Copy this pattern for your widgets!

---

## 🎨 Design Guidelines

**DO:**
- ✅ Place feedback at bottom of widget (after main content)
- ✅ Use border-top separator: `"pt-3 border-t border-slate-200"`
- ✅ Keep text simple: "Was this helpful?"
- ✅ Use green for thumbs up, red for thumbs down hover states
- ✅ Show "✓ Thanks!" confirmation after submission
- ✅ Disable buttons during submission (prevent double-clicks)

**DON'T:**
- ❌ Add feedback to loading/error states
- ❌ Show feedback if no data to display
- ❌ Make feedback prominent or distracting
- ❌ Allow multiple submissions per session
- ❌ Skip the confirmation message

---

## 💡 Advanced: Correction Feedback (For Category/Status Changes)

If your widget allows users to **correct AI-generated values** (like email categories, project health scores), log corrections:

```typescript
const handleCorrection = async (oldValue: string, newValue: string) => {
  await api.logFeedback({
    user: "anonymous",
    feature: "email_category",
    action: "correction",
    original_value: oldValue,
    corrected_value: newValue,
    entity_type: "email",
    entity_id: emailId,
    helpful: undefined, // Not a helpfulness rating
    context: {
      ai_confidence: 0.85,
      correction_type: "category_change"
    }
  });
};
```

---

## 🚨 Common Issues & Solutions

### Issue: "no such column: feature"
**Solution:** Backend wasn't reloaded. Restart backend:
```bash
cd backend && python3 -m uvicorn api.main:app --reload --port 8000
```

### Issue: Feedback not showing in database
**Solution:** Check table name. The table is `user_feedback`, not `training_data`.

### Issue: TypeScript error on api.logFeedback
**Solution:** Make sure you have the latest `frontend/src/lib/api.ts`. The function exists at lines 613-630.

### Issue: Button clicks do nothing
**Solution:** Check browser console for errors. Verify backend is running on port 8000.

---

## 📈 Phase 2 Plans (Future)

This feedback data will be used for:
1. **Widget Analytics** - Which widgets are most/least helpful
2. **A/B Testing** - Test widget variations, measure user preference
3. **ML Training** - Train models on user corrections
4. **Reports** - Generate "most helpful features" for Bill
5. **Auto-optimization** - Hide unhelpful widgets, promote helpful ones

---

## ✅ Checklist for Your Implementation

- [ ] Added `useState` hooks for feedback tracking
- [ ] Created `handleFeedback` function
- [ ] Added feedback UI section (thumbs up/down buttons)
- [ ] Updated feature name to match your widget
- [ ] Added relevant context data
- [ ] Tested visually in browser
- [ ] Tested API with curl
- [ ] Verified feedback saves to database
- [ ] Updated COORDINATION_MASTER.md with completion status

---

## 🤝 Questions or Issues?

If you run into problems:
1. Check the ProposalTrackerWidget implementation (working example)
2. Verify backend is running: http://localhost:8000/docs
3. Check database: `sqlite3 database/bensley_master.db "SELECT * FROM user_feedback;"`
4. Look at browser console for errors

**Good luck! The infrastructure is solid and tested. Just copy the pattern!** 🎉
