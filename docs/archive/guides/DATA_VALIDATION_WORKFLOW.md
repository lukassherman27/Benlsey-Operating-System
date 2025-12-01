# AI-Powered Data Validation System - Complete Workflow

## What This System Does

Automatically finds inconsistencies between your emails and database:
- AI reads emails about projects
- Extracts facts (status, fees, team, timeline, etc.)
- Compares to database
- Flags mismatches for your review
- You approve/deny each suggestion

**Example:**
- Email: "5 people working on Rosewood this week"
- Database: `status = "archived"`
- → 🚨 AI creates suggestion: Change status to "active"
- → You review and approve/deny

---

## Complete Workflow

### **Step 1: Link Emails to Projects** (AI figures out which project each email is about)

```bash
# Link unlinked emails (AI analyzes subject, sender, content)
python3 ai_email_linker.py unlinked 50

# Link all unlinked emails with body content
python3 ai_email_linker.py unlinked 298
```

**What it does:**
- Checks if sender is a known contact → instant link
- Fuzzy matches project names in subject/body
- Uses AI to analyze context and pick best match
- Creates link with confidence score

**Example output:**
```
✅ Linked to BK-033 (confidence: 100%)
   Method: ai_analysis
   Evidence: Email mentions 'Ritz Carlton Reserve, Nusa Dua'
```

---

### **Step 2: Validate Data** (Find database inconsistencies)

```bash
# Validate recently linked emails
python3 smart_email_validator.py recent 50

# Validate specific email
python3 smart_email_validator.py process 2024693
```

**What it does:**
- Extracts facts from email using GPT-4
- Compares to database values
- Detects mismatches (status, fees, timeline, etc.)
- Creates suggestions with evidence & confidence

**Example output:**
```
🚨 Mismatch detected: status
   DB: archived
   Email: active (mentioned "proceeding with design work")
   Confidence: 90%
```

---

### **Step 3: Review Suggestions** (Human approval)

```bash
# List all pending suggestions
python3 manage_suggestions.py list

# Approve a suggestion
python3 manage_suggestions.py approve 5 "Database was outdated"

# Deny a suggestion
python3 manage_suggestions.py deny 3 "This is about separate branding service"

# View statistics
python3 manage_suggestions.py stats
```

**Review carefully:**
- ✅ **Approve** if AI is right → database needs updating
- ❌ **Deny** if AI is wrong (false positive)
- Add notes explaining your decision (helps future improvements)

---

## Files Created

### **1. Database Migration**
- `database/migrations/026_data_validation_suggestions.sql`
- Tables: `data_validation_suggestions`, `suggestion_application_log`

### **2. AI Email Linker**
- `ai_email_linker.py` - Links emails to projects using AI

### **3. Data Validator**
- `smart_email_validator.py` - Finds data inconsistencies

### **4. Suggestion Manager**
- `manage_suggestions.py` - Approve/deny suggestions
- `review_suggestions.py` - Interactive review (for terminal use)

---

## Common Commands

```bash
# === LINKING EMAILS ===
# Link 50 unlinked emails
python3 ai_email_linker.py unlinked 50

# Link recent 20 emails
python3 ai_email_linker.py recent 20

# === VALIDATION ===
# Validate 50 linked emails
python3 smart_email_validator.py recent 50

# === REVIEW ===
# List suggestions
python3 manage_suggestions.py list

# Approve suggestion
python3 manage_suggestions.py approve 12 "Confirmed status change needed"

# Deny suggestion
python3 manage_suggestions.py deny 13 "Email is about different scope"

# Stats
python3 manage_suggestions.py stats
```

---

## Typical Session

```bash
# 1. Link new emails to projects
python3 ai_email_linker.py unlinked 100

# 2. Validate those emails for data issues
python3 smart_email_validator.py recent 100

# 3. Review and approve/deny suggestions
python3 manage_suggestions.py list
python3 manage_suggestions.py approve 5
python3 manage_suggestions.py deny 6 "False positive"

# 4. Check stats
python3 manage_suggestions.py stats
```

---

## How AI Linking Works

**Method 1: Known Contact**
- Email from: john@client.com
- System knows: john@client.com works on BK-045
- → Instant link (95% confidence)

**Method 2: Project Name Fuzzy Matching**
- Email subject: "Haeundae Project in Busan"
- Database has: "MDM World - Haeundae Project in Busan"
- → Fuzzy match (85-100% confidence)

**Method 3: AI Context Analysis**
- Email mentions: "the Soudah resort", "mountain project", "Saudi Arabia"
- AI matches to: BK-017 (Soudah Mountain Resort)
- → AI analysis (75-95% confidence)

---

## What Facts Are Validated

Currently checks:
- **Status** (active, completed, archived, on-hold)
- **Project value** (fees, budget)
- **Team size** (number of people)
- **Timeline** (deadlines, completion dates)

Can be extended to validate:
- Client names
- Contact information
- Scope changes
- Payment status
- Anything in the database

---

## False Positives (Known Issues)

**Issue:** AI can't distinguish between:
- Main project contract
- Separate service agreements (branding, additional scope)

**Example:**
- Main contract: Status = "won" ✅ Correct
- Branding service: Being negotiated ✅ Separate thing
- AI thinks: "Project status should be 'active'" ❌ Wrong

**Solution:** YOU review and deny these. Over time, we can improve AI prompts.

---

## Next Steps

### Immediate:
1. Process all 298 emails with body content
2. Review generated suggestions
3. Build up a dataset of approved/denied suggestions

### Future Improvements:
1. Better AI prompts to reduce false positives
2. Learn from your approve/deny decisions
3. Auto-apply high-confidence suggestions (>95%)
4. Web UI for easier review
5. Validate more field types
6. Track multiple agreements per project

---

## Questions?

**"How many emails should I process at once?"**
- Start with 50-100 to test
- Then batch process all 298

**"What if AI links email to wrong project?"**
- You'll see it when reviewing suggestions
- Deny the suggestion with notes
- Can manually fix email_project_links table if needed

**"Can I auto-approve high-confidence suggestions?"**
- Not yet - safer to review manually first
- After you've reviewed 100+ and trust the AI, we can add auto-approve

**"What happens after I approve a suggestion?"**
- Right now: just marks it approved
- Next step: Build script to actually update database
- Or you manually update based on approved suggestions

---

## Summary

**You built:**
✅ AI email-to-project linker (contact + name + context matching)
✅ Data consistency validator (GPT-4 powered)
✅ Suggestion review system (human-in-the-loop)
✅ Complete workflow from email → validation → approval

**Next:** Run on all your emails and catch every data quality issue!
