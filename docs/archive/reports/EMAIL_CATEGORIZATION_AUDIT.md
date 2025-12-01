# Email Categorization System Audit & Improvement Plan

**Date:** November 23, 2025
**Status:** 95% Coverage, Improvements Needed
**Next Actions:** Add missing categories, improve accuracy, enhance project linking

---

## Executive Summary

The email categorization system has **excellent coverage (95%)** but needs **accuracy improvements** and **additional categories** for the intelligence layer.

### Key Metrics:
- ✅ 395 total emails
- ✅ 375 (95%) have category tags
- ✅ 395 (100%) linked to proposals
- ✅ 210 (53%) linked to projects
- ❌ 20 (5%) completely untagged
- ❌ 185 (47%) not linked to projects

---

## Current Category Distribution

| Category | Count | % of Tagged | Purpose |
|----------|-------|-------------|---------|
| business-development | 125 | 33% | New business, proposals, RFPs |
| project-update | 93 | 25% | Status updates on active work |
| scheduling | 92 | 25% | Meetings, deadlines, timelines |
| legal | 85 | 23% | Contracts, agreements, legal matters |
| inquiry | 28 | 7% | General questions, information requests |
| invoicing | 15 | 4% | Billing, payments, financial |
| high-priority | 2 | 0.5% | Urgent matters |

**Total Tags:** 440 (some emails have multiple tags)

---

## What's Working Well

### 1. Coverage
- 95% of emails have at least one category tag
- 100% of emails are linked to proposals (excellent project association)
- Every email is tracked and searchable

### 2. Tag System Design
- ✅ Multi-tag support (emails can have multiple relevant categories)
- ✅ Confidence scoring (tracks how certain the AI is)
- ✅ Provenance tracking (knows if tag was AI, manual, or rule-based)
- ✅ Tag types: category, priority, topic, project_mention, client_mention

### 3. Scripts & Tools
- `ai_email_processor.py` - AI categorization engine
- `smart_email_matcher.py` - Email-to-project/proposal linking
- `verify_email_categories.py` - Manual verification tool

---

## Issues Identified

### 1. Untagged Emails (20 emails, 5%)

**Why are they untagged?**
Sample of untagged subjects:
- "Re: Sunny Lagoons Maldives RFP"
- "Re: INDIA PROJECT INTRODUCTIONS"
- "Re: The Sukhothai Hotel - Chinese restaurant High Level Concept Study" (9 emails!)
- "Fwd: Bill Bensley and Duc Luu - Paragon Dai Phuoc Hotel"

**Root Cause:**
- Reply threads ("Re:") might be skipped by categorization logic
- Newer emails may not have been processed yet
- Email processor may have failed/stopped partway through

**Impact:** Low (only 5%), but these are important project emails that should be categorized

---

### 2. Only 53% Project Linking

**The Gap:**
- 395 emails total
- 395 linked to proposals (100%)
- 210 linked to projects (53%)
- **185 emails (47%) are NOT linked to projects**

**Possible Reasons:**
1. ✅ **Valid:** These are proposal-stage emails (not yet won projects) - GOOD
2. ❌ **Invalid:** Matching logic is missing active project connections - BAD
3. ❌ **Invalid:** Project table is incomplete or has different project codes

**Need to Investigate:**
- Are the 185 unlinked emails all pre-contract proposals?
- Or are some actually discussing active projects but failed to match?

---

### 3. Missing Critical Categories

**For the Intelligence Layer you described, we need:**

| Missing Category | Why Needed | Example Triggers |
|-----------------|------------|------------------|
| contract-changes | Detect scope/fee modifications | "revise contract", "amendment", "change order" |
| fee-adjustments | Track pricing changes | "reduce fee to 3.25M", "increase budget", "discount" |
| scope-changes | Scope additions/removals | "remove landscape", "add interiors", "expand scope" |
| payment-terms | Payment schedule changes | "monthly installments", "payment plan", "milestone payments" |
| rfis | Requests for information | "RFI", "clarification needed", "question about" |
| meeting-notes | Capture decisions from meetings | "meeting summary", "action items", "we agreed" |

**Impact:** HIGH - Without these, the intelligence layer can't detect the contract changes you want to auto-prompt for database updates

---

### 4. Tag Accuracy Unknown

**Current Status:**
- We have tags, but **no validation** of whether they're correct
- No user feedback loop to correct mis-categorizations
- No confidence threshold filtering (showing low-confidence tags)

**Need:**
- Manual spot-check of 50 random tagged emails
- User feedback mechanism ("Is this tag correct? Yes/No")
- Confidence threshold UI (hide tags below 70% confidence)

---

## Improvement Plan

### Phase 1: Quick Fixes (This Session) ⚡

**A. Tag the 20 Untagged Emails**
- Run `ai_email_processor.py` on untagged emails
- Add rule-based tagging for common patterns ("Re: RFP" → business-development)

**B. Add Missing Categories**
- Add: contract-changes, fee-adjustments, scope-changes, payment-terms, rfis, meeting-notes
- Update `ai_email_processor.py` with new category detection rules
- Re-process all emails with new categories

**C. Improve Project Linking**
- Analyze the 185 unlinked emails
- Enhance `smart_email_matcher.py` logic
- Add fuzzy matching for project codes (BK-001, BK001, Bodrum, etc.)

---

### Phase 2: Accuracy Improvements (Next Session) 🎯

**D. Sample Tag Accuracy Check**
- Query 50 random tagged emails
- Manual review of tag correctness
- Calculate accuracy rate
- Identify common mis-categorizations

**E. Add Contextual Categorization**
- Use proposal/project data to improve tags
- If email mentions project BK-001 + "invoice" → add invoicing tag
- If email from lawyer + contract mention → add legal tag

**F. Implement Confidence Thresholds**
- Only show tags with >70% confidence in UI
- Flag low-confidence tags for manual review
- Build feedback loop for corrections

---

### Phase 3: Intelligence Features (Future) 🧠

**G. Contract Change Detection**
```
IF email contains:
  - ("reduce fee" OR "increase fee" OR "change scope")
  AND linked to active project
  AND confidence > 80%
THEN:
  - Tag: contract-changes, fee-adjustments
  - AI Prompt: "This email discusses fee changes. Update project value?"
  - Extract: old_value, new_value, reason
  - Suggest: Database update + new contract draft
```

**H. Auto-Draft Contracts**
- Parse email for scope changes
- Generate contract amendment text
- Prompt user: "Should I draft a new agreement?"

**I. Meeting Minutes Intelligence**
- Detect meeting notes emails
- Extract action items, decisions, deadlines
- Auto-populate project updates

---

## Technical Details

### Database Schema

**email_tags** table:
```sql
email_id                INTEGER
tag                     TEXT (e.g., "business-development")
tag_type                TEXT ('category' | 'priority' | 'topic' | 'project_mention' | 'client_mention')
confidence              REAL (0.0 - 1.0)
created_by              TEXT ('ai' | 'manual' | 'rule')
created_at              DATETIME
```

**email_project_links** table:
```sql
email_id                INTEGER
project_id              INTEGER
project_code            TEXT (e.g., "BK-001")
confidence              REAL
link_method             TEXT ('alias' | 'ai' | 'manual' | 'subject_match')
evidence                TEXT (why this link was made)
```

**email_proposal_links** table:
```sql
email_id                INTEGER
proposal_id             INTEGER
confidence_score        REAL
match_reasons           TEXT
auto_linked             INTEGER (0/1)
```

---

## Recommended Actions (Priority Order)

### Immediate (Do Now):
1. ✅ Run categorization on 20 untagged emails
2. ✅ Add 6 missing critical categories
3. ✅ Investigate project linking gap (185 unlinked emails)

### This Week:
4. ⏳ Manual accuracy check (50 random samples)
5. ⏳ Improve project matching logic
6. ⏳ Add rule-based categorization for common patterns

### Next Sprint:
7. ⏳ Build user feedback UI for tag corrections
8. ⏳ Implement confidence thresholds
9. ⏳ Add contextual categorization (use project data)

### Phase 2 (Intelligence Layer):
10. ⏳ Contract change detection
11. ⏳ Auto-draft contract amendments
12. ⏳ Meeting minutes intelligence

---

## Success Metrics

**Target State (End of Phase 1):**
- 100% of emails tagged (not 95%)
- >90% tag accuracy (validated by manual spot-checks)
- 75%+ project linking (up from 53%)
- All 6 critical categories added and working
- User can correct mis-categorizations via UI

**Target State (End of Phase 2):**
- Contract change detection working
- Auto-prompt for database updates
- 95%+ tag accuracy
- Feedback loop operational

---

## Files to Modify

1. `ai_email_processor.py` - Add new categories, improve logic
2. `smart_email_matcher.py` - Enhance project matching
3. `backend/api/main.py` - Add API endpoints for tag feedback
4. `frontend/.../email-category-review.tsx` - UI for tag validation (future)

---

## Next Steps

**Right Now:**
1. Run categorization on untagged emails
2. Add missing categories to categorization engine
3. Re-process all emails with new categories

**Tomorrow:**
1. Investigate project linking gap
2. Improve matching logic
3. Validate 50 random tags manually

---

**Questions for User:**
- Should we re-run categorization on ALL 395 emails with new categories?
- Do you want to manually review tag accuracy now or later?
- Priority: Fix untagged (20) or improve project linking (185)?
