# Workspaces & Contexts - Bill Bensley's Operating System

**Owner:** Brain Agent
**Last Updated:** 2025-11-30
**Purpose:** Document all work contexts managed by this system

---

## Core Insight

**This is NOT just a project tracker - it's Bill Bensley's Personal Operating System.**

Bill manages multiple business contexts beyond Bensley Design Studios:
- Design studio (core business)
- Shinta Mani Hotels (part-owner, investor)
- Shinta Mani Foundation (charity)
- Personal matters (real estate, investments)
- Internal operations (social media, team)

The system must organize and surface information across ALL these contexts.

---

## Identified Workspaces

### 1. Bensley Design Studios (BDS)

**Description:** Core design consultancy business - proposals, projects, client work.

| Attribute | Value |
|-----------|-------|
| **Status** | Fully tracked |
| **Tables** | `proposals`, `proposal_tracker`, `projects`, `invoices`, `rfis`, `deliverables` |
| **Email Domains** | bensley.com, bensley.co.id, bdlbali.com |
| **Volume** | 81 proposals, 62 projects, 253 invoices |
| **Primary Contact** | All Bensley staff |

**How to Identify:**
- Project codes start with `BK-XXX`
- Emails to/from @bensley.com
- Subject mentions proposals, contracts, design phases

**Subcontexts:**
- **Proposals** (pre-contract) - tracked in `proposal_tracker`
- **Projects** (active contracts) - tracked in `projects`
- **Completed** (archived work) - status = 'Completed' or 'archived'

---

### 2. Shinta Mani Hotels (Owner/Investor)

**Description:** Hotel brand Bill partly owns. This is NOT Bensley design work - it's ownership/investor updates.

| Attribute | Value |
|-----------|-------|
| **Status** | Partially tracked (emails only) |
| **Tables** | Emails in `emails` table, not in projects |
| **Email Domains** | shintamani.com |
| **Volume** | ~50 emails |
| **Key Contacts** | Marc LEBLANC (GM Wild), Jason Friedman (financial advisor) |

**How to Identify:**
- Email from @shintamani.com (NOT @shintamanifoundation.org)
- Subject mentions: P&L, occupancy, revenue, operations
- Key terms: "SMW" (Shinta Mani Wild), "owners eyes", "financial performance"

**Properties Tracked:**
- **Shinta Mani Wild** (Cambodia) - Tented camp, conservation focus
- **Shinta Mani Mustang** (Nepal) - Also tracked as Bensley project 25 BK-015

**Key Contacts:**
| Name | Role | Email Domain |
|------|------|--------------|
| Marc LEBLANC | GM, Shinta Mani Wild | shintamani.com |
| Jason Friedman | Financial Advisor | jmfriedman.com |
| Mandy Le | JMF Admin | jmfriedman.com |

**Note:** JM Friedman (jmfriedman.com) provides financial advisory for BOTH Shinta Mani Wild and Shinta Mani Foundation.

---

### 3. Shinta Mani Foundation (Charity)

**Description:** Non-profit foundation doing charitable work in Cambodia.

| Attribute | Value |
|-----------|-------|
| **Status** | Minimally tracked (few emails) |
| **Tables** | Emails only |
| **Email Domain** | shintamanifoundation.org |
| **Volume** | ~5 emails |
| **Key Contacts** | CHHUNNIN |

**How to Identify:**
- Email from @shintamanifoundation.org
- Subject mentions: foundation, donations, community
- Key terms: "SMF" (Shinta Mani Foundation)

---

### 4. Chang Gu / Bali Land Sale (Personal)

**Description:** Bill's personal real estate transaction - selling land in Canggu, Bali (~12,000 sqm).

| Attribute | Value |
|-----------|-------|
| **Status** | Not formally tracked |
| **Tables** | Emails only |
| **Email Domains** | ssek.com, hhplawfirm.com, hsfkramer.com |
| **Volume** | ~20 emails |
| **Key Contacts** | Indonesian law firms |

**How to Identify:**
- Subject mentions: "Bali land sale", "Canggu", "engagement request"
- Law firm domains (Indonesian legal)
- Personal/private nature (not Bensley business)

**Key Contacts:**
| Name | Firm | Email Domain |
|------|------|--------------|
| Irfan Ghazali | Herbert Smith Freehills | hsfkramer.com |
| Bima Sarumpaet | HHP Law Firm | hhplawfirm.com |
| Nico Mooduto | SSEK | ssek.com |
| Denny Rahmansyah | SSEK | ssek.com |

---

### 5. Social Media / Marketing (Internal)

**Description:** Bensley's social media management and brand marketing.

| Attribute | Value |
|-----------|-------|
| **Status** | Tracked as internal operations |
| **Tables** | Emails only |
| **Email Domains** | sproutsocial.com |
| **Volume** | ~20 emails |
| **Key Contacts** | Fah (internal), Sprout Social |

**How to Identify:**
- Subject mentions: Instagram, social media, Sprout
- Email from sproutsocial.com
- Internal Bensley discussions about content

**Tools Used:**
- Sprout Social (scheduling, analytics)

---

## Email Categorization Patterns

### Domain-Based Detection

```
bensley.com → internal
bensley.co.id → internal (Bali office)
bdlbali.com → internal
shintamani.com → shinta-mani-ops
shintamanifoundation.org → shinta-mani-foundation
jmfriedman.com → financial-advisory (check subject for SM vs other)
ssek.com, hhplawfirm.com, hsfkramer.com → personal-legal
sproutsocial.com → social-marketing
```

### Subject-Based Detection

```
"P&L", "revenue", "occupancy" + "Shinta Mani" → shinta-mani-ops
"foundation" → shinta-mani-foundation
"Bali land", "Canggu" → personal-legal
"Instagram", "social media" → social-marketing
"BK-XXX" → bensley-project
"proposal", "quote", "fee" → bensley-proposal
```

---

## Current Data Distribution

### By Email Domain (Top Non-Bensley)
| Domain | Count | Context |
|--------|-------|---------|
| gmail.com | 131 | Various (clients, personal) |
| soudah.sa | 42 | Client |
| jmfriedman.com | 32 | Financial advisor (SM) |
| shintamani.com | ~10 | SM Operations |
| hsfkramer.com | 21 | Personal legal |
| ssek.com | 9 | Personal legal |

### By Email Category (Current)
| Category | Count | Notes |
|----------|-------|-------|
| meeting | 1,024 | Well-categorized |
| general | 634 | Needs refinement |
| contract | 597 | Bensley work |
| design | 459 | Bensley work |
| financial | 318 | Mixed (Bensley + SM) |
| administrative | 169 | Internal |
| internal | 106 | Bensley internal |

---

## Recommended Schema Enhancements

### Phase 1: Email Context Tags (Low Effort)

Add new tag types to `email_tags` table:

```sql
-- New context tags (add to tag_mappings)
INSERT INTO tag_mappings (tag, mapped_tag, tag_type) VALUES
('shintamani.com', 'shinta-mani-ops', 'context'),
('shintamanifoundation.org', 'shinta-mani-foundation', 'context'),
('hsfkramer.com', 'personal-legal', 'context'),
('ssek.com', 'personal-legal', 'context'),
('hhplawfirm.com', 'personal-legal', 'context'),
('sproutsocial.com', 'social-marketing', 'context');
```

### Phase 2: Workspace Column on Emails (Medium Effort)

Add `workspace` column to emails table:

```sql
ALTER TABLE emails ADD COLUMN workspace TEXT;

-- Values: 'bensley', 'shinta-mani', 'foundation', 'personal', 'internal'
```

### Phase 3: Workspaces Table (Future)

Only if Shinta Mani operations grow significantly:

```sql
CREATE TABLE workspaces (
    workspace_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    email_patterns TEXT, -- JSON array of domain patterns
    subject_patterns TEXT, -- JSON array of subject patterns
    is_active INTEGER DEFAULT 1
);
```

---

## Recommendations for Jan 15 Demo

### Priority 1: Visual Context Indicator
- Add workspace badge to email list view
- Color-code: Blue (Bensley), Green (SM Hotels), Orange (Foundation), Red (Personal)

### Priority 2: Filtered Views
- "Shinta Mani" filter button on emails page
- "Personal" filter (exclude from main view by default)

### Priority 3: Dashboard Context Switcher
- Top-level dropdown: "All" | "Bensley Design" | "Shinta Mani" | "Personal"
- Filters all dashboard widgets

---

## Agent Tasks for Context Implementation

### Task 1: Email Context Tagger
**Agent:** Data Pipeline
**Action:** Run domain-based tagging on existing emails
**Output:** ~500 emails tagged with workspace context

### Task 2: Email List UI Enhancement
**Agent:** Frontend Builder
**Action:** Add context badge/filter to emails page
**Files:** `frontend/src/app/(dashboard)/emails/page.tsx`

### Task 3: Dashboard Context Switcher
**Agent:** Frontend Builder
**Action:** Add workspace dropdown to main dashboard
**Files:** `frontend/src/app/(dashboard)/page.tsx`

---

## Notes

1. **JM Friedman emails** need manual review - they handle finances for BOTH Shinta Mani Wild AND Shinta Mani Foundation
2. **Shinta Mani Mustang** is BOTH a Bensley design project AND a Shinta Mani property - dual context
3. **Personal emails** should be hidden from default views but accessible
4. **Sprout Social** is a tool, not a context - but emails about social media are "internal operations"

---

**Last Investigation:** 2025-11-30
**Next Review:** After Jan 15 demo, reassess if workspaces table needed
