# 🎯 COORDINATOR GUIDE - Operations Platform Fixes

## Overview
This document coordinates 5 parallel workstreams to fix issues in the Bensley Operations Platform.

---

## 📋 Agent Assignment

### Agent 1: Proposals System
**File**: `.claude/AGENT_1_PROPOSALS_SYSTEM.md`
**Priority**: CRITICAL
**Focus**: Import fixes, status tracking, timeline UI
**Key Bugs**:
- Proposal import missing location/currency/country (all NULL)
- Wrong countries imported (France, UK, Australia)
- No status progression tracking
- Page too wide
**Estimated Time**: 2-3 hours

### Agent 2: Active Projects & Invoice Linking
**File**: `.claude/AGENT_2_ACTIVE_PROJECTS_INVOICING.md`
**Priority**: CRITICAL
**Focus**: 0% invoiced bug, breakdown sync, invoice display
**Key Bugs**:
- **CRITICAL**: Lines 5726-5727 in main.py hardcode 0.0 for paid amounts
- Breakdown totals not updating when invoices linked
- Invoice display structure wrong (need hierarchical by phase)
**Estimated Time**: 2-3 hours

### Agent 3: Dashboard Widgets & Metrics
**File**: `.claude/AGENT_3_DASHBOARD_WIDGETS.md`
**Priority**: HIGH
**Focus**: Dashboard widgets, metrics, meetings extraction
**Key Bugs**:
- Invoice aging vs outstanding discrepancy (4.299 vs 4.64)
- Recent payments showing "general" instead of phase/discipline
- No meetings widget
- Aging invoices need red color for 600+ days
**Estimated Time**: 1-2 hours

### Agent 4: Email Intelligence
**File**: `.claude/AGENT_4_EMAIL_INTELLIGENCE.md`
**Priority**: MEDIUM
**Focus**: Email categorization, linking, interactivity
**Key Bugs**:
- Not interactive (can't approve/reject categorizations)
- Only shows "general" category
- Refresh doesn't work
- No manual email-proposal linking UI
**Estimated Time**: 1-2 hours

### Agent 5: Query Interface & Financial Entry
**File**: `.claude/AGENT_5_QUERY_FINANCIAL_ENTRY.md`
**Priority**: LOW
**Focus**: Chat history, financial entry improvements
**Key Bugs**:
- No conversation history in query interface
- Can't see existing breakdowns when adding new ones
- Data validation UI needs improvement
**Estimated Time**: 1-2 hours

---

## 🚀 How to Execute

### Step 1: Open 5 Claude Code Windows
Open 5 separate Claude Code sessions in the project directory:
```bash
# In 5 different terminal windows
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
```

### Step 2: Assign Each Agent
In each Claude Code window, paste the corresponding prompt:

**Window 1**:
```
I am Agent 1 working on Proposals System fixes. Please read the file:
.claude/AGENT_1_PROPOSALS_SYSTEM.md

Follow all instructions in that file. I will work independently on proposals import, status tracking, and UI fixes. Report back when complete.
```

**Window 2**:
```
I am Agent 2 working on Active Projects & Invoice Linking. Please read the file:
.claude/AGENT_2_ACTIVE_PROJECTS_INVOICING.md

Follow all instructions in that file. I will fix the CRITICAL 0% invoiced bug and breakdown sync. Report back when complete.
```

**Window 3**:
```
I am Agent 3 working on Dashboard Widgets & Metrics. Please read the file:
.claude/AGENT_3_DASHBOARD_WIDGETS.md

Follow all instructions in that file. I will fix dashboard widgets and add meetings extraction. Report back when complete.
```

**Window 4**:
```
I am Agent 4 working on Email Intelligence. Please read the file:
.claude/AGENT_4_EMAIL_INTELLIGENCE.md

Follow all instructions in that file. I will make email categorization interactive and fix linking. Report back when complete.
```

**Window 5**:
```
I am Agent 5 working on Query Interface & Financial Entry. Please read the file:
.claude/AGENT_5_QUERY_FINANCIAL_ENTRY.md

Follow all instructions in that file. I will add chat history and improve financial entry UI. Report back when complete.
```

### Step 3: Monitor Progress
Each agent will work independently and report completion. Track progress here:

- [ ] Agent 1: Proposals System
- [ ] Agent 2: Active Projects & Invoice Linking
- [ ] Agent 3: Dashboard Widgets & Metrics
- [ ] Agent 4: Email Intelligence
- [ ] Agent 5: Query Interface & Financial Entry

### Step 4: Integration Testing
Once all agents complete, test integration:
1. Check proposals page - should have all data, fit on screen
2. Check active projects - should show real percentages (not 0%)
3. Check dashboard - all widgets working, meetings displayed
4. Check emails - interactive categorization working
5. Check query interface - has chat history

---

## 🔗 Dependencies Between Agents

### Agent 1 ↔ Agent 4
- Agent 1 provides proposal data
- Agent 4 links emails to proposals
- **Coordination**: Ensure proposal project_codes are consistent

### Agent 2 ↔ Agent 3
- Agent 2 fixes invoice calculations
- Agent 3 uses those calculations in widgets
- **Coordination**: Agent 3 should wait for Agent 2 to fix critical bug before testing

### Agent 3 ↔ Agent 4
- Agent 3 needs meeting extraction
- Agent 4 handles email parsing
- **Coordination**: Agent 4 should expose meeting extraction API for Agent 3

---

## ⚠️ Critical Bugs (Fix First)

### 1. CRITICAL: 0% Invoiced Bug (Agent 2)
**File**: `backend/api/main.py` lines 5726-5727
**Impact**: All active projects show 0% invoiced
**Fix**: Remove hardcoded `0.0 as paid_to_date_usd`

### 2. CRITICAL: Proposal Import Broken (Agent 1)
**Impact**: 89 proposals missing location/currency/country
**Fix**: Update `import_proposals.py` and re-import

---

## 📊 Expected Outcomes

### After Agent 1 Completes:
- ✅ 89 proposals have location, country, currency
- ✅ Correct countries only (no France/UK/Australia)
- ✅ Status tracking with visual timeline
- ✅ Proposals page fits on one screen
- ✅ "Total Sent 2025" metric for conversion rate

### After Agent 2 Completes:
- ✅ Active projects show real percentages (not 0%)
- ✅ Invoices grouped by phase in correct order
- ✅ Breakdown totals auto-update
- ✅ Project names displayed (not codes)
- ✅ Color coding for progress

### After Agent 3 Completes:
- ✅ Invoice aging = Outstanding invoice (numbers match)
- ✅ Recent payments show phase/discipline
- ✅ Aging invoices red for 600+ days
- ✅ Meetings widget with today's schedule

### After Agent 4 Completes:
- ✅ Interactive email categorization (approve/reject)
- ✅ All categories visible (not just "general")
- ✅ Manual email-proposal linking UI
- ✅ Refresh button works

### After Agent 5 Completes:
- ✅ Query interface with chat history
- ✅ Financial entry shows existing breakdowns
- ✅ Can't create duplicate breakdowns

---

## 🔄 Current System State

### Database:
- **Invoices**: 253 total, 253 linked (100%)
- **Proposals**: 89 total, 8 won, 81 pending
- **Projects**: Multiple active projects
- **Emails**: Thousands imported, need categorization

### Known Issues:
- Proposal data incomplete (NULL locations)
- Invoice percentages showing 0%
- Dashboard widgets have calculation errors
- Email system not interactive

### Recent Achievements:
- ✅ 100% invoice-to-breakdown linking (253/253)
- ✅ Multi-scope architecture (Wynn Marjan, Art Deco)
- ✅ Custom parsers for special formats

---

## 📝 Coordination Notes

### For Agent 1:
- Ask user for Excel file path if you can't find "Proposals.xlsx"
- Backup database before re-importing
- Check with coordinator if unsure about status logic

### For Agent 2:
- This is CRITICAL - fix the 0% bug FIRST
- Verify all 253 invoice links still intact
- Test with Wynn Marjan (should show 100% invoiced)

### For Agent 3:
- Wait for Agent 2 to fix calculations before testing widgets
- Coordinate with Agent 4 for meeting extraction from emails

### For Agent 4:
- Provide meeting extraction API for Agent 3
- Ensure proposal linking works with Agent 1's data

### For Agent 5:
- Lower priority - can work independently
- Focus on UX improvements

---

## 🎉 Success Criteria

System is complete when:
1. All proposals have complete data (location, country, currency, status)
2. Active projects show accurate invoiced percentages (not 0%)
3. All dashboard widgets display correct data
4. Email categorization is interactive and working
5. Query interface has chat history
6. All displays use project names (not codes)
7. No console errors in frontend
8. All API endpoints return expected data

---

## 📞 Questions?
If any agent gets stuck or needs clarification, report back to the coordinator with:
- Which task you're on
- What's blocking you
- What information you need
