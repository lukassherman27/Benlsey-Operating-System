# 🚀 AGENT DEPLOYMENT PLAN

**Created:** 2025-11-26
**Status:** READY FOR USER REVIEW

---

## 📋 EXECUTIVE SUMMARY

This document outlines the coordinated multi-agent strategy to build the Bensley Operations Platform. **All agents follow the mandatory AUDIT-FIRST protocol** to prevent architectural fragmentation.

### Key Principles:
1. **AUDIT BEFORE ACTION** - Every agent audits existing infrastructure first
2. **REPORT FINDINGS** - Agents create detailed audit reports and wait for approval
3. **COORDINATE, DON'T CONFLICT** - Agents use existing tables/scripts, never create duplicates
4. **DOCUMENT EVERYTHING** - All changes logged in MASTER_ARCHITECTURE.md

---

## 🏗️ FOUNDATION DOCUMENTS (READ THESE FIRST)

All agents must read these before starting:

1. **`.claude/MASTER_ARCHITECTURE.md`** - Single source of truth
   - Documents all 60+ existing tables
   - Lists existing scripts and APIs
   - Defines file ownership to avoid conflicts

2. **`.claude/ALIGNMENT_AUDIT.md`** - Critical issues discovered
   - 29 scripts with wrong database path
   - email_content table empty (critical gap)
   - Recommended alignment fixes

---

## 🌊 WAVE 1: FOUNDATION (HIGHEST PRIORITY)

These agents fix critical infrastructure issues. **Run in parallel** after individual audits approved.

### Agent 1: Email Brain Foundation
**File:** `.claude/agents/WAVE1_AGENT1_EMAIL_BRAIN.md`
**Mission:** Fix email body content extraction
**Status:** AWAITING AUDIT

**What it does:**
- Fixes database path in 29 scripts (creates `database_config.py`)
- Modifies `smart_email_system.py` to populate `email_content` table
- Backfills 3,356 existing emails with body content and AI analysis
- Provides foundation for all email-dependent features

**Dependencies:** None (foundational)
**Provides to:** Agent 2, 3, 4 (email content for all)

**Audit Checklist:**
- [ ] Verify which scripts have wrong DB path
- [ ] Check email_content table structure
- [ ] Assess smart_email_system.py architecture
- [ ] Estimate OpenAI API costs (~$5-10 for 3,356 emails)

---

### Agent 2: Proposal Lifecycle & Status Tracking
**File:** `.claude/agents/WAVE1_AGENT2_PROPOSAL_LIFECYCLE.md`
**Mission:** Build complete proposal history tracking
**Status:** AWAITING AUDIT

**What it does:**
- Uses existing `proposal_status_history` table
- Creates backend APIs: `/api/proposals/{code}/history`, `/api/proposals/{code}/status`
- Builds frontend StatusTimeline component
- Tracks who changed what and when

**Dependencies:** Agent 1 (for email-proposal linkage)
**Provides to:** Dashboard, user visibility into proposal pipeline

**Audit Checklist:**
- [ ] Verify proposal_status_history table exists and structure
- [ ] Check existing proposal APIs
- [ ] Assess frontend proposal components
- [ ] Determine auto vs manual status tracking

---

### Agent 3: RFI Detection & Tracking
**File:** `.claude/agents/WAVE1_AGENT3_RFI_DETECTION.md`
**Mission:** Auto-detect and track RFIs from emails
**Status:** AWAITING AUDIT

**What it does:**
- Creates `rfi_detector.py` with keyword/pattern matching
- Integrates with `smart_email_system.py`
- Auto-creates RFI records when detected
- Builds RFI dashboard with overdue alerts

**Dependencies:** Agent 1 (CRITICAL - needs email_content populated)
**Provides to:** PM workload tracking, alert system

**User Context:** Setting up rfi@bensley.com with contract clause enforcement

**Audit Checklist:**
- [ ] Verify `rfis` table exists and structure
- [ ] Check email categorization system
- [ ] Assess RFI detection requirements
- [ ] Determine assignment rules (who gets RFIs?)

---

## 🌊 WAVE 2: INTELLIGENCE (MEDIUM PRIORITY)

Build on Wave 1 foundation. **Start after Wave 1 agents complete.**

### Agent 4: Deliverables & Scheduling
**File:** `.claude/agents/WAVE2_AGENT4_DELIVERABLES_SCHEDULING.md`
**Mission:** Extract and track deliverables, PM workload
**Status:** AWAITING AUDIT

**What it does:**
- Creates `deliverable_extractor.py` to parse contracts/emails
- Tracks deadlines and submission status
- Calculates PM workload (upcoming/overdue deliverables)
- Builds PM workload dashboard

**Dependencies:** Agent 1 (email content for extraction)
**Provides to:** PM management, project scheduling

**Audit Checklist:**
- [ ] Verify `deliverables` table structure
- [ ] Check contract/email data availability
- [ ] Assess PM assignment infrastructure
- [ ] Determine manual vs auto deliverable extraction

---

### Agent 5: Dashboard Coordinator & Widget Fixes
**File:** `.claude/agents/WAVE2_AGENT5_DASHBOARD_COORDINATOR.md`
**Mission:** Polish dashboard UX and fix remaining issues
**Status:** AWAITING AUDIT

**What it does:**
- Fixes invoice aging bar scale (0.5M increments)
- Fixes active projects phase ordering (Mobilization first)
- Adds summary bar to active projects tab
- Debugs query interface
- Fixes email content loading

**Dependencies:** Agent 1 (for email content viewer)
**Provides to:** Improved user experience, polished dashboard

**Audit Checklist:**
- [ ] Assess invoice aging scale calculation
- [ ] Check phase ordering logic
- [ ] Determine summary bar requirements
- [ ] Debug query interface status
- [ ] Check field name consistency

---

## 🌊 WAVE 3: ADVANCED (FUTURE)

Advanced features for scaling. **Defer until Wave 1 & 2 complete.**

### Agent 6: Contract Versioning & Negotiation Tracking
**File:** `.claude/agents/WAVE3_AGENT6_CONTRACT_VERSIONING.md`
**Mission:** Track contract versions and negotiation changes
**Status:** AWAITING AUDIT

**What it does:**
- Creates `contract_versions` and `contract_change_history` tables
- Builds `contract_version_detector.py` for change detection
- Creates visual diff viewer for contracts
- Links contract changes to email threads

**Dependencies:** None (standalone)
**Provides to:** Legal compliance, negotiation audit trail

**Audit Checklist:**
- [ ] Check contract storage infrastructure
- [ ] Assess version tracking capabilities
- [ ] Verify PDF text extraction feasibility
- [ ] Determine email-contract linkage method

---

## 🔄 COORDINATION STRATEGY

### Dependency Chain

```
Agent 1 (Email Brain)
   ↓
   ├──→ Agent 2 (Proposal Lifecycle)
   ├──→ Agent 3 (RFI Detection) ← CRITICAL DEPENDENCY
   ├──→ Agent 4 (Deliverables)
   └──→ Agent 5 (Dashboard - email viewer)

Agent 6 (Contract Versioning) - Independent
```

### Execution Order

**Phase 0: Pre-Alignment** (Optional but recommended)
- Create `database_config.py`
- Fix 29 scripts with wrong DB path (~2-3 hours)

**Phase 1: Wave 1 Agents Audit** (Parallel)
- Agent 1 audits email system
- Agent 2 audits proposal system
- Agent 3 audits RFI infrastructure
- Each creates AGENT[N]_AUDIT_REPORT.md
- **STOP and wait for user approval**

**Phase 2: Wave 1 Execution** (Sequential)
1. Agent 1 executes (FIRST - others depend on this)
2. Agent 2 & 3 execute (parallel, after Agent 1 completes)

**Phase 3: Wave 2 Agents** (After Wave 1 complete)
- Agent 4 & 5 audit → report → execute

**Phase 4: Wave 3 Agents** (Future)
- Agent 6 when contracts become priority

---

## ⚠️ CRITICAL RULES

### Every Agent MUST:
1. ✅ **READ** MASTER_ARCHITECTURE.md first
2. ✅ **READ** ALIGNMENT_AUDIT.md second
3. 🔍 **AUDIT** their assigned area thoroughly
4. 📊 **CREATE** AGENT[N]_AUDIT_REPORT.md
5. ⏸️ **WAIT** for user approval (DO NOT PROCEED WITHOUT APPROVAL)
6. ✅ **EXECUTE** only after explicit user go-ahead
7. 📝 **DOCUMENT** changes in MASTER_ARCHITECTURE.md

### What Agents MUST NOT Do:
- ❌ **NEVER** create new tables that already exist
- ❌ **NEVER** replace existing working scripts
- ❌ **NEVER** create parallel systems
- ❌ **NEVER** skip the audit phase
- ❌ **NEVER** proceed without user approval
- ❌ **NEVER** use hardcoded database paths

---

## 📊 SUCCESS METRICS

### Wave 1 Complete When:
- [ ] email_content table populated (3,356 records)
- [ ] All email scripts use database_config.py
- [ ] proposal_status_history being populated
- [ ] RFI detection working on new emails
- [ ] At least 10 test emails processed end-to-end

### Wave 2 Complete When:
- [ ] Deliverables extracted from contracts
- [ ] PM workload dashboard functional
- [ ] Dashboard widgets fixed (aging scale, phase order, summary bar)
- [ ] Email content viewer working

### Overall Success:
- [ ] User can track complete proposal lifecycle
- [ ] RFIs auto-detected and tracked
- [ ] Dashboard shows accurate, real-time data
- [ ] No duplicate tables or conflicting systems
- [ ] All changes documented in MASTER_ARCHITECTURE.md

---

## 🎯 NEXT STEPS

### For User:
1. **Review this plan** - Does the strategy make sense?
2. **Decide on alignment approach:**
   - **Option A (Recommended):** Fix 29 scripts first (2-3 hours)
   - **Option B:** Fix only critical scripts, proceed with features
   - **Option C:** Document issues, work around them (risky)
3. **Launch Agent 1 audit** - Start with email brain
4. **Review Agent 1's audit report**
5. **Approve Agent 1 execution** (if report looks good)
6. **Repeat for Agents 2 & 3**

### For Claude (Next Session):
If user approves, I will:
1. Act as **Agent 1** and perform audit
2. Create **AGENT1_AUDIT_REPORT.md**
3. Wait for user approval
4. Execute Agent 1 tasks if approved
5. Hand off to Agent 2 & 3

---

## 📁 FILES CREATED

- [x] `.claude/MASTER_ARCHITECTURE.md` - Architecture documentation
- [x] `.claude/ALIGNMENT_AUDIT.md` - Misalignment issues
- [x] `.claude/agents/WAVE1_AGENT1_EMAIL_BRAIN.md`
- [x] `.claude/agents/WAVE1_AGENT2_PROPOSAL_LIFECYCLE.md`
- [x] `.claude/agents/WAVE1_AGENT3_RFI_DETECTION.md`
- [x] `.claude/agents/WAVE2_AGENT4_DELIVERABLES_SCHEDULING.md`
- [x] `.claude/agents/WAVE2_AGENT5_DASHBOARD_COORDINATOR.md`
- [x] `.claude/agents/WAVE3_AGENT6_CONTRACT_VERSIONING.md`
- [x] `.claude/AGENT_DEPLOYMENT_PLAN.md` (this file)

---

## ❓ DECISION REQUIRED

**User, please choose:**

### A. Proceed with Wave 1 Audits (Recommended)
"Start Agent 1 audit. I'll review the report before you execute."

### B. Fix Alignment First
"Fix the 29 scripts with wrong DB path first, then start agents."

### C. Modify Plan
"I want to change [specific aspect] of the plan."

### D. Questions
"I have questions about [specific agents or approach]."

---

**This plan prevents fragmentation by:**
- Mandatory audit phase (agents discover existing infrastructure)
- Required approval gates (user reviews before execution)
- Clear dependency chains (agents don't step on each other)
- Architecture documentation (single source of truth)
- Explicit file ownership (avoid conflicts)

**Ready to proceed when you are.** 🚀
