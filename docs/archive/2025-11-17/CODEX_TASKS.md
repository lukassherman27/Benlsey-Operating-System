# Codex Task List - While Backend Processes Emails

Hey Codex! Claude here. User topped up OpenAI and I'm processing 269 emails now (~30-60 min).

**While that runs, here's what you should work on:**

---

## 🎯 Priority 1: Polish Phase 1 UX (2-3 hours)

Make the dashboard feel production-ready:

### 1. Loading States
- [ ] Skeleton loaders for proposal table (while fetching)
- [ ] Skeleton loaders for timeline (while fetching)
- [ ] Loading spinners for dashboard stats cards
- [ ] Loading state for natural language query
- [ ] Smooth transitions when data loads

### 2. Empty States
- [ ] "No proposals found" - when filter returns nothing
- [ ] "No emails yet" - when proposal has no emails
- [ ] "No documents" - when proposal has no documents
- [ ] "No timeline events" - when timeline is empty
- [ ] Nice illustrations or icons for empty states

### 3. Error Handling
- [ ] Toast notifications for API errors (use shadcn/ui toast)
- [ ] Retry button when API call fails
- [ ] Offline detection ("API server not running")
- [ ] Graceful degradation (show cached data if API fails)
- [ ] Error boundary for React errors

### 4. Responsive Design
- [ ] Test on tablet (iPad)
- [ ] Test on mobile (iPhone)
- [ ] Collapsible sidebar on mobile
- [ ] Stack dashboard cards on mobile
- [ ] Touch-friendly button sizes

### 5. UX Polish
- [ ] Keyboard shortcuts (/ for search, arrows to navigate)
- [ ] Persist filters in localStorage (remember user's choices)
- [ ] Smooth scrolling in timeline
- [ ] Hover states on all interactive elements
- [ ] Focus indicators for accessibility

---

## 🎯 Priority 2: Category Correction UI (2 hours)

**This is the killer feature** - lets user fix AI mistakes and train the model!

### What to Build:
```tsx
// Email category badge (clickable)
<Badge
  variant="outline"
  className="cursor-pointer hover:bg-gray-100"
  onClick={() => setEditingCategory(true)}
>
  {email.category}
  <PencilIcon className="ml-1 h-3 w-3" />
</Badge>

// Dropdown to change category
<Select value={category} onValueChange={handleCategoryChange}>
  <SelectItem value="general">General</SelectItem>
  <SelectItem value="contract">Contract</SelectItem>
  <SelectItem value="invoice">Invoice</SelectItem>
  <SelectItem value="design">Design</SelectItem>
  <SelectItem value="rfi">RFI</SelectItem>
  <SelectItem value="schedule">Schedule</SelectItem>
  <SelectItem value="meeting">Meeting</SelectItem>
</Select>
```

### Backend Endpoint (I'll create):
```typescript
// API call
const updateCategory = async (emailId: number, category: string) => {
  const response = await fetch(`${API_URL}/api/emails/${emailId}/category`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ category })
  });
  return response.json();
};
```

### Features:
- [ ] Clickable category badge on emails
- [ ] Dropdown to select new category
- [ ] Optimistic UI update (change immediately, sync in background)
- [ ] Undo button (toast notification with "Undo" action)
- [ ] Success feedback ("Category updated!")
- [ ] Show training indicator (e.g., "🎓 Learning from your feedback")

**Value:** Every correction you make trains the ML model to be smarter!

---

## 🎯 Priority 3: Test Everything (1 hour)

### Start Both Servers:
```bash
# Terminal 1 - Backend API
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
uvicorn backend.api.main_v2:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Test Checklist:
- [ ] Dashboard loads without errors
- [ ] All stats cards show correct data
- [ ] Proposal table displays and sorts correctly
- [ ] Click proposal → shows details, emails, documents, timeline
- [ ] Health scores display with color coding
- [ ] Timeline shows both emails and documents
- [ ] Natural language query works ("Show me all proposals")
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] Test with different proposals (find edge cases)

### Edge Cases to Test:
- [ ] Proposal with 0 emails
- [ ] Proposal with 0 documents
- [ ] Proposal with very long name (does it truncate?)
- [ ] Proposal with null/missing data
- [ ] Very old proposals (dates from years ago)
- [ ] Health score of 0 or 100

---

## 🔮 Optional (If You Have Time):

### Health Score Details Modal
When user clicks a health score, show breakdown:

```tsx
<Dialog>
  <DialogTrigger>
    <Badge className={getHealthColor(score)}>{score}</Badge>
  </DialogTrigger>
  <DialogContent>
    <DialogTitle>Health Score Breakdown</DialogTitle>
    <div>
      <h4>Factors:</h4>
      <ul>
        <li>18 days since last contact (-20 points)</li>
        <li>Low email activity (-15 points)</li>
        <li>No documents in 30 days (-10 points)</li>
      </ul>
      <h4>Recommendation:</h4>
      <p>Schedule a follow-up call to maintain momentum</p>
    </div>
  </DialogContent>
</Dialog>
```

---

## 📊 What Claude (Backend) is Doing:

**Current:** Processing 269 emails with OpenAI (~30-60 min)
- AI categorization (contract, invoice, design, etc.)
- Entity extraction (fees, dates, decisions)
- Importance scoring (0-100%)
- AI summaries
- Training data collection (3,568 → 4,400+ examples)

**Next:**
- Improve email-proposal linking (63% → 80%)
- Recalculate health scores with complete data
- Test API endpoints
- Create category correction endpoint for you

---

## 📝 When You're Done:

1. Update `SESSION_LOGS.md` with what you built
2. Commit your changes
3. Test with the backend API running
4. Let me know what bugs you found!

---

## 💡 Tips:

- **Don't block on backend** - Use mock data if needed
- **Focus on UX** - Make it feel smooth and professional
- **Test edge cases** - That's where bugs hide
- **Use shadcn/ui** - Already set up, great components
- **Keep it simple** - Polish > features

---

**Questions?** Just ask in your session notes and I'll see them in SESSION_LOGS.md!

— Claude (Backend) 🤖

**Estimated time:** 4-5 hours total
**Priority:** 1 + 2 (Polish + Category Correction UI)
