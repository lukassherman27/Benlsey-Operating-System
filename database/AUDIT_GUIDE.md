# DATABASE AUDIT GUIDE
**Created:** November 24, 2025
**Purpose:** Manual review and cleanup of all proposals and projects

---

## 📂 FILES CREATED FOR YOU

### 1. **PROPOSALS_AUDIT.csv** (87 proposals + header = 88 lines)
Open in Excel/Numbers to review ALL proposals

**Breakdown:**
- 53 LOST proposals ($74M total value, $1.86M avg)
- 33 ACTIVE proposals ($99M total value, $3.95M avg)
- 1 WON proposal (BK-033 Ritz Carlton, $3.15M)

### 2. **PROJECTS_AUDIT.csv** (46 projects + header = 47 lines)
Open in Excel/Numbers to review ALL active contracts

**Breakdown:**
- 36 Active contracts (from contracts DB)
- 5 Completed contracts
- 1 Cancelled contract
- 4 Active (source unknown - needs investigation)

### 3. **comprehensive_audit_tool.py** (Interactive CLI tool)
Run in terminal for step-by-step interactive audit

---

## 🔍 WHAT YOU NEED TO AUDIT

### SECTION 1: PROPOSALS (87 total)

#### A. Active Proposals (33) - PRIORITY 1
**What to check:**
- [ ] Is the status still "proposal" or should it be "won" or "lost"?
- [ ] Is client company filled in?
- [ ] Is project value accurate?
- [ ] Are dates correct (first contact, proposal sent)?
- [ ] Update current_remark with latest status

**Common issues to fix:**
- "Still waiting on client response since..." → Add remark
- "Client said they'll decide by..." → Add expected date
- "Lost to competitor" → Change status to "lost"
- "Signed contract!" → Change status to "won", set contract_signed_date

#### B. Lost Proposals (53) - PRIORITY 2
**What to check:**
- [ ] Confirm they're actually lost (not just dormant)
- [ ] Add reason in current_remark if missing
- [ ] Set project_value if missing (for records)

**Common reasons to document:**
- "Lost to competitor"
- "Client budget constraints"
- "Project on hold indefinitely"
- "Client went another direction"

#### C. Won Proposal (1) - PRIORITY 3
**What to check:**
- [ ] BK-033 (Ritz Carlton) - Verify it's in projects table
- [ ] Contract signed date is correct
- [ ] Project value matches contract

---

### SECTION 2: PROJECTS (46 total)

#### A. Active Projects (40) - PRIORITY 1
**What to check:**
- [ ] Is it actually still active or should it be "Completed"/"Cancelled"?
- [ ] Add context notes like:
  - "On hold - waiting for client permits"
  - "Delayed - supply chain issues"
  - "90% complete - final review pending"
  - "Cancelled but client owes $50k final payment"
  - "Active and on track"

**Check for invoices/payments:**
- [ ] Does it have invoices in the system?
- [ ] Are payments being received?
- [ ] Any outstanding balances?

#### B. Completed Projects (5) - PRIORITY 2
**What to check:**
- [ ] Confirm completion date
- [ ] All invoices paid?
- [ ] Any final deliverables pending?

#### C. Cancelled Projects (1) - PRIORITY 3
**What to check:**
- [ ] Reason for cancellation
- [ ] Any money owed?
- [ ] Final resolution notes

#### D. Unknown Source (4) - PRIORITY 1
**These need investigation:**
- BK-033 (Ritz Carlton) - From won proposal ✅
- BK-015 (Shinta Mani Mustang) - Check if real contract or should be removed
- BK-017 (TARC New Delhi) - Check if real contract or should be removed
- BK-058 (Fenfushi Island) - Check if real contract or should be removed

---

## 🛠️ HOW TO DO THE AUDIT

### Option 1: Excel/Numbers (Recommended for bulk review)

1. **Open PROPOSALS_AUDIT.csv in Excel/Numbers**
2. **Sort by status column**
3. **Review each row:**
   - Update status if needed
   - Fill in missing data (client, dates, values)
   - Add notes/remarks
4. **Save as new CSV when done**
5. **Import changes back** (we'll create an import script)

### Option 2: Interactive CLI Tool (Recommended for detailed review)

```bash
cd database
python3 comprehensive_audit_tool.py
```

**Features:**
- Shows one proposal/project at a time
- See all fields + linked emails + timeline
- Press 'u' to update interactively
- Press Enter to skip to next
- Press 'q' to quit

**Example session:**
```
Project: BK-070 Dubai Resort
Client: Hilton Group
Value: $5,000,000
Status: proposal

Options:
  [Enter] = Next
  u = Update
  q = Quit

Choice: u

New status: lost
Current remark: Client chose local firm
```

### Option 3: Direct SQL Updates (For power users)

```bash
cd database
sqlite3 bensley_master.db
```

```sql
-- Update a proposal status
UPDATE proposals
SET status = 'lost',
    current_remark = 'Lost to competitor'
WHERE project_code = 'BK-070';

-- Update project notes
UPDATE projects
SET notes = 'Cancelled but client owes $50k balance',
    status = 'Cancelled'
WHERE project_code = 'BK-033';
```

---

## 📋 AUDIT CHECKLIST

### Before You Start:
- [ ] Backup database (already done: `bensley_master_BACKUP_2025-11-24.db`)
- [ ] Open PROPOSALS_AUDIT.csv
- [ ] Open PROJECTS_AUDIT.csv
- [ ] Have client emails/notes handy for reference

### During Audit:
- [ ] Review all 33 active proposals
- [ ] Update won/lost statuses
- [ ] Add missing contact dates
- [ ] Fill in project values
- [ ] Add current remarks/notes
- [ ] Review all 40 active projects
- [ ] Add context notes to projects
- [ ] Mark completed/cancelled correctly
- [ ] Investigate 4 unknown source projects

### After Audit:
- [ ] Run data quality check
- [ ] Verify counts make sense
- [ ] Commit changes to database
- [ ] Update frontend to show clean data

---

## 💡 TIPS FOR EFFECTIVE AUDITING

### For Proposals:
1. **Group by status** - Do all "proposal" first, then "lost"
2. **Check email history** - CSV shows linked email count
3. **Be realistic** - If no contact in 6+ months, probably lost
4. **Document everything** - Add remarks even if brief

### For Projects:
1. **Focus on active** - These need most attention
2. **Check invoices** - Missing invoices = red flag
3. **Add context** - Notes help future you understand status
4. **Be honest** - Mark cancelled if it's dead, even if painful

### Common Scenarios:
- **"Not sure if lost or dormant"** → Keep as "proposal" but add remark "Dormant - last contact MM/DD"
- **"Client keeps delaying"** → Keep as "proposal", add "On hold - client internal delays"
- **"We stopped working but didn't formally cancel"** → Status "Cancelled", note why
- **"Still invoicing but work is done"** → Status "Completed", note "Final invoicing in progress"

---

## 🚨 IMPORTANT NOTES

### Data Fields to Focus On:
**Proposals:**
- `status` - proposal, won, lost
- `client_company` - Must be filled
- `project_value` - Even estimates help
- `contract_signed_date` - For won proposals
- `current_remark` - Context for status
- `project_summary` - Brief description

**Projects:**
- `status` - Active, Completed, Cancelled, On Hold
- `notes` - Add context! This is gold
- `total_fee_usd` - Contract value
- Check for invoices/payments

### What NOT to Change:
- `project_code` - Never change
- `created_at` - Historical record
- `proposal_id` / `client_id` - System IDs
- `source_db` - Database provenance

### Provenance Tracking:
Every change you make is automatically logged with:
- WHO: Your name (manual_audit_tool)
- WHAT: Field changed, old value, new value
- WHEN: Timestamp
- WHY: Change reason (if you add it)

---

## 📞 QUESTIONS TO ASK YOURSELF

### For Each Proposal:
1. Have we heard from this client in the last 3 months?
2. Do we have a realistic chance of winning this?
3. Is the project value still accurate?
4. What's blocking progress? (Client decision, our bandwidth, budget, etc.)
5. Should this be marked lost and moved on from?

### For Each Project:
1. Are we actively working on this?
2. Is the client paying invoices?
3. What's the current phase? (Design, construction, final review, etc.)
4. Any issues or delays?
5. Expected completion date?

---

## 🎯 SUCCESS METRICS

**After audit, you should have:**
- ✅ All active proposals have current remarks
- ✅ All lost proposals have reasons documented
- ✅ All projects have status notes
- ✅ No missing client companies on active proposals
- ✅ No missing project values on active proposals
- ✅ Clear understanding of pipeline ($99M in active proposals)
- ✅ Clear understanding of contracted work (46 projects)

---

## 🔄 NEXT STEPS AFTER AUDIT

1. **Import changes** back to database (we'll create import tool)
2. **Verify data quality** - Run quality checks
3. **Update dashboard** - Refresh frontend to show clean data
4. **Set up monitoring** - Weekly reviews to keep data fresh
5. **Document insights** - What did you learn about your pipeline?

---

## 📧 NEED HELP?

Run the interactive tool:
```bash
cd database
python3 comprehensive_audit_tool.py
```

Or ask Claude to help with specific queries:
- "Show me all proposals with no client company"
- "Show me projects with no invoices"
- "What's the total pipeline value?"

---

**Remember:** This is YOUR data about YOUR business. You know the real status better than any database. Trust your knowledge and update accordingly!
