# BENSLEY PROPOSAL AUTOMATION SYSTEM
## Your AI-Powered Business Operations Assistant

---

## 🎯 WHAT IT DOES

Every morning, the system automatically:

1. **📧 Imports new emails** from your server (INBOX + Sent)
2. **🏷️  Categorizes them** (Proposal, RFI, Invoice, Contract, etc.)
3. **🔗 Links to projects** (finds BK-XXX codes, project names)
4. **💡 Generates suggestions** like:
   - "BK-070: No contact in 18 days → Follow up (here's a draft email)"
   - "BK-042: Similar to BK-020 → Use that contract as template"
   - "BK-055: Client asked about timeline → Update milestones"
   - "$45K outstanding from Client X → Send payment reminder"
5. **📊 Shows you in dashboard** - Urgent/Needs Attention/FYI buckets
6. **✅ You approve/reject** - System learns from your decisions

---

## 🚀 HOW TO USE IT

### **Option A: Fully Automated (Set It & Forget It)**

Set up daily cron job to run every morning:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 8am every day):
0 8 * * * cd /path/to/Bensley && ./daily_automation.sh >> logs/daily_automation.log 2>&1
```

### **Option B: Manual Trigger (When You Want)**

Run the automation whenever you want:

```bash
./daily_automation.sh
```

Or run individual steps:

```bash
python3 import_all_emails.py              # Get new emails
python3 smart_email_matcher.py            # Categorize
python3 proposal_automation_engine.py     # Generate suggestions
```

---

## 💡 AI SUGGESTION TYPES

### 1. **Follow-Up Reminders**
**When:** No contact in 14+ days
**What you see:**
```
🔔 BK-070: Bali Resort Project
   No contact in 21 days (last: Oct 28)
   Risk: Losing $850K opportunity

   💡 Suggested Action: Send follow-up email

   📧 Draft Email:
   ---
   Hi Sarah,

   I hope this finds you well! I wanted to follow up on the
   Bali Resort design proposal we sent a few weeks ago.

   Have you had a chance to review? I'd be happy to discuss
   any questions or adjust the scope if needed.

   Looking forward to hearing from you!

   Best,
   Bill
   ---

   [Approve & Send] [Edit Draft] [Snooze 1 Week] [Dismiss]
```

### 2. **Contract Template Matching**
**When:** New proposal needs contract, similar past project found
**What you see:**
```
📄 BK-089: Mumbai Hotel Project
   Status: In negotiation, no contract yet

   💡 Suggested Action: Use BK-020 contract as template

   Why BK-020?
   ✓ Same project type (Hotel/Resort)
   ✓ Same location region (India)
   ✓ Similar budget ($500K vs $650K)
   ✓ Has signed contract + all documents

   Similar alternatives:
   - BK-033: Chennai Resort (85% match)
   - BK-042: Singapore Hotel (80% match)

   [Use BK-020 Template] [View BK-020 Files] [Pick Different] [Dismiss]
```

### 3. **Financial Risk Alerts**
**When:** Outstanding invoices > 30 days
**What you see:**
```
💰 BK-070: Bali Resort Project
   Outstanding: $45,000 (Invoice #BK070-002)
   Due: Sept 15 (32 days overdue)

   💡 Suggested Action: Send payment reminder

   📧 Draft Email:
   ---
   Hi Sarah,

   I hope you're doing well. I wanted to follow up on
   Invoice #BK070-002 for $45,000, which was due on Sept 15.

   Could you let me know the expected payment timeline?
   Happy to discuss if there are any issues.

   Best,
   Bill
   ---

   [Send Reminder] [Mark as Paid] [Snooze] [Dismiss]
```

### 4. **Lifecycle Actions** (Coming Soon)
- "Proposal sent 30 days ago → Schedule check-in call"
- "Verbal yes received → Send formal contract"
- "Contract signed → Set up kickoff meeting"

---

## 🧠 HOW IT LEARNS FROM YOU

Every time you approve/reject a suggestion, the system learns:

### **Your Approval = Pattern Created**

```
You: [Approve] "Follow up on BK-070 after 21 days"

System learns:
✅ Pattern: "For Hotel projects with value >$500K, follow up after 21 days"
✅ Next time: Auto-suggests follow-ups at 21 days for similar projects
✅ Future: "Also suggest follow-up for BK-089 (similar: Hotel, >$500K, 22 days)"
```

### **Your Rejection = Pattern Avoided**

```
You: [Dismiss] "Follow up on BK-042"

System asks why:
- "Client explicitly said they need 60 days"
- "Waiting on their board approval"
- "Other reason" (you explain)

System learns:
❌ Don't suggest BK-042 follow-ups for 60 days
❌ For projects "awaiting board approval" → wait longer
✅ Stored in manual_overrides table for future reference
```

---

## 📊 DASHBOARD INTEGRATION

All suggestions appear in your dashboard:

### **Main Dashboard View:**

```
┌─────────────────────────────────────────────────────┐
│ 🔔 AI SUGGESTIONS (12 pending)                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│ 🔥 URGENT (3)                                       │
│ ├─ BK-070: Follow up (21 days no contact)           │
│ ├─ BK-033: Payment reminder ($45K overdue)           │
│ └─ BK-089: Client asked question (respond today)     │
│                                                      │
│ ⚠️  NEEDS ATTENTION (7)                             │
│ ├─ BK-042: Use BK-020 contract template             │
│ ├─ BK-055: Update milestone dates                   │
│ └─ ... (5 more)                                     │
│                                                      │
│ ℹ️  FYI (2)                                         │
│ └─ BK-012: New email from client (low priority)     │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### **Review Workflow:**

1. Click suggestion → See details
2. Read AI's reasoning + evidence
3. See draft email (if applicable)
4. Choose action:
   - ✅ **Approve** - Execute the suggestion
   - ✏️  **Edit** - Modify draft email, then send
   - ⏰ **Snooze** - Remind me in 1 week / 2 weeks / 1 month
   - ❌ **Dismiss** - Not relevant (system learns why)

---

## 🎛️  CONFIGURATION

### **Adjust Sensitivity**

Edit `proposal_automation_engine.py` to change thresholds:

```python
# Line 89: Follow-up timing
if days_since > 30:     # Change to 21 or 45
    severity = 'high'

# Line 92: Medium urgency
elif days_since > 21:   # Change to 14 or 30
    severity = 'medium'
```

### **Add Custom Rules**

Create manual overrides in dashboard or database:

```sql
INSERT INTO manual_overrides (
    project_code,
    scope,
    instruction,
    urgency,
    status
) VALUES (
    'BK-070',
    'followup_timing',
    'Wait 60 days for this client - they explicitly requested',
    'high',
    'active'
);
```

### **Enable/Disable Suggestion Types**

In `daily_automation.sh`, comment out generators you don't want:

```bash
# Disable financial alerts:
# python3 proposal_automation_engine.py --skip-financial
```

---

## 🤖 AI EMAIL DRAFTING

The system uses OpenAI GPT-4 to draft emails. Set API key:

```bash
export OPENAI_API_KEY="sk-..."
```

**Email drafts consider:**
- Recent email thread context
- Project status & history
- Client communication style (formal/casual)
- Days since last contact
- Cultural context (if location known)

**You always review before sending!** Nothing is sent automatically.

---

## 📈 METRICS & ANALYTICS

Track automation performance:

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('database/bensley_master.db')
c = conn.cursor()

# Suggestions created
c.execute('SELECT COUNT(*) FROM ai_suggestions_queue')
print(f'Total suggestions: {c.fetchone()[0]}')

# Approval rate
c.execute('SELECT status, COUNT(*) FROM ai_suggestions_queue GROUP BY status')
for status, count in c.fetchall():
    print(f'{status}: {count}')
"
```

Expected output:
```
Total suggestions: 47
pending: 12
approved: 28
rejected: 5
auto_applied: 2
```

---

## 🔄 WORKFLOW EXAMPLE

### **Day 1 - Morning**

```
8:00 AM: Daily automation runs
- Imports 23 new emails
- Categorizes: 8 proposals, 5 RFIs, 4 invoices, 6 general
- Links 12 emails to existing projects
- Generates 6 new suggestions:
  - 3 follow-ups
  - 2 contract templates
  - 1 financial alert

9:00 AM: You check dashboard
- See "BK-070: Follow up (21 days)" in URGENT
- Read draft email AI generated
- Edit slightly (make it more casual)
- Click [Approve & Send]
- Email sent ✅
- Suggestion marked "approved"
- System learns: "User prefers casual tone for this client"
```

### **Day 2 - Morning**

```
8:00 AM: Daily automation runs again
- Imports 31 new emails
- Finds reply from BK-070 client!
- Categorizes as "proposal_response"
- Links to BK-070
- Updates health score: 🔥 Hot (immediate response)
- Generates suggestion: "BK-070: Client interested → Schedule call"

9:00 AM: You see notification
- "BK-070 responded to your follow-up!"
- Email summary shows client wants to move forward
- AI suggests: "Schedule kickoff call this week"
- You approve → Calendar invite sent
```

---

## 🎯 NEXT STEPS

1. **Let automation run for 1 week** - Build up suggestion history
2. **Review suggestions daily** - Teach the system your preferences
3. **Monitor patterns learned** - See what AI figures out
4. **Add custom rules** - For VIP clients, special projects
5. **Track conversion** - Did follow-ups → more wins?

---

## 🛠️ TROUBLESHOOTING

### **No suggestions generated**

Check active projects:
```bash
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM projects WHERE is_active_project=1"
```

### **Draft emails are generic**

Need more email context:
```bash
python3 smart_email_matcher.py  # Re-categorize with better context
```

### **OpenAI errors**

Check API key:
```bash
echo $OPENAI_API_KEY
```

---

**Your proposal automation is now LIVE! 🚀**

Run `./daily_automation.sh` to generate your first batch of suggestions!
