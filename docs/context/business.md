# Bensley Design Studio - Business Context

**Owner:** Business Context Agent
**Last Updated:** 2025-11-30
**Purpose:** Provide essential business context for all agents before coding

---

## 1. Studio Overview

### Who We Are

**Bensley Design Studios (BDS)** is a world-renowned, full-service design firm led by **Bill Bensley**, one of the most celebrated designers in luxury hospitality. The studio is known for creating immersive, story-driven environments that blend landscape, architecture, and interiors into cohesive guest experiences.

### Headquarters & Offices

| Location | Domain | Notes |
|----------|--------|-------|
| Bangkok, Thailand | bensley.com | Main studio |
| Bali, Indonesia | bensley.co.id | Regional office |

### Leadership

- **Bill Bensley** - Principal/Founder, Creative Director
- Known for maximalist design philosophy - "More is more"
- Designs with narrative and whimsy
- Hands-on involvement in all major projects

### Bill's Extended Business Interests

**This platform is Bill Bensley's Personal Operating System**, not just a project tracker for Bensley Design Studios. Bill manages multiple business contexts:

| Context | Relationship | Coverage in System |
|---------|--------------|-------------------|
| **Bensley Design Studios** | Core business | Fully tracked (proposals, projects, invoices) |
| **Shinta Mani Hotels** | Part-owner/investor | Emails only (P&L, operations updates) |
| **Shinta Mani Foundation** | Charity work | Emails only |
| **Personal matters** | Land sales, investments | Emails only (not in proposals/projects) |

**Key insight:** When Bill receives emails about "Shinta Mani Wild P&L" or "Bali land sale", these are NOT Bensley design projects - they are ownership/investor communications. The system should distinguish:
- **Shinta Mani as client** (Bensley designing for SM) → tracked in projects
- **Shinta Mani as investment** (Bill receiving owner updates) → tracked in emails only

See: `docs/context/workspaces.md` for full context documentation.

---

## 2. Design Disciplines

Bensley is a **full-service design studio** offering:

| Discipline | Description |
|------------|-------------|
| **Landscape Architecture** | Master planning, gardens, pools, outdoor spaces |
| **Architecture** | Building design, resort planning, villas |
| **Interior Design** | Hotel interiors, restaurants, spas, guest rooms |
| **Art Direction** | Custom furniture, art curation, textile design |
| **Brand Experience** | Storytelling, theming, guest journey design |

**Key differentiator:** Bensley doesn't just design spaces - they create **worlds**. Every project has a story, character, and soul.

---

## 3. Sectors Served

### Primary Focus: Luxury Hospitality

Bensley specializes in **5-star luxury hospitality**:

| Sector | Examples |
|--------|----------|
| Luxury Resorts | Four Seasons, Rosewood, Capella |
| Boutique Hotels | Shinta Mani properties |
| Wellness Destinations | Spas, retreats, sanctuaries |
| F&B Venues | Restaurants, bars within hotels |
| Private Estates | Ultra-luxury private residences |

### Geographic Reach

Primarily **Asia-Pacific** with select projects worldwide:
- Thailand, Vietnam, Cambodia, Laos, Nepal
- Indonesia, Maldives, Sri Lanka
- Middle East, Africa (growing)

---

## 4. Project Phases

Bensley follows a standard architecture/design project lifecycle:

| Phase | Code | Typical Duration | Key Deliverables |
|-------|------|------------------|------------------|
| **Concept Design** | CD | 4-8 weeks | Mood boards, narrative, initial sketches |
| **Schematic Design** | SD | 6-12 weeks | Floor plans, elevations, site plans |
| **Design Development** | DD | 8-16 weeks | Detailed drawings, material selections |
| **Construction Documents** | CD | 12-24 weeks | Full technical drawings for builders |
| **Construction Administration** | CA | Ongoing | Site visits, RFI responses, quality control |

### Fee Structure

Fees are typically structured as:
- **Percentage of construction cost** (common for full-service)
- **Fixed fee by phase** (milestone-based payments)
- **Hourly/retainer** (for ongoing advisory)

Fee milestones often: 30% / 40% / 30% split across phases.

---

## 5. Flagship Projects

These are Bensley's signature works - mentioned in press, awards, and client conversations:

### Four Seasons Collection
- **Four Seasons Resort Chiang Mai** - Thailand
- **Four Seasons Tented Camp Golden Triangle** - Thailand
- **Four Seasons Resort Koh Samui** - Thailand

### Capella Hotels
- **Capella Ubud** - Bali, Indonesia
- **Capella Hanoi** - Vietnam

### Rosewood Hotels
- **Rosewood Luang Prabang** - Laos

### Shinta Mani Collection (Bensley-Owned)
- **Shinta Mani Wild** - Cambodia (conservation-focused tented camp)
- **Shinta Mani Mustang** - Nepal

### Other Notable
- **InterContinental Danang Sun Peninsula** - Vietnam
- **One&Only Reethi Rah** - Maldives (Landscape)

### Awards & Recognition
- Numerous Condé Nast Traveler "Hot List" and "Gold List" appearances
- Travel + Leisure "World's Best" awards
- Bill Bensley named "Asia's Designer of the Year" multiple times

---

## 6. Voice & Tone Guidelines

### The Bensley Personality

Bill Bensley is known for being:
- **Playful** - Design should bring joy
- **Maximalist** - More is more, detail matters
- **Storytelling** - Every space has a narrative
- **Irreverent** - Doesn't take himself too seriously
- **Passionate** - Design is life, not just work

### Platform Communication Style

**Use a BALANCED approach:**

| Context | Tone | Example |
|---------|------|---------|
| Data tables, metrics | **Professional** | Clean numbers, no fluff |
| Empty states | **Playful** | "The pipeline's looking thirsty" |
| Loading messages | **Whimsical** | "Waking up the elephants..." |
| Error states | **Helpful, not jokey** | "Something went wrong. Try again?" |
| Navigation & labels | **Clear & Direct** | "Projects", "Invoices", "Dashboard" |
| Success confirmations | **Warm** | "Saved. The cloud remembers everything." |

### Writing Guidelines

**DO:**
- Use active voice
- Keep labels short and scannable
- Add personality to dead ends (empty states, 404s)
- Reference elephants, tropical imagery, design culture

**DON'T:**
- Add fluff to data-heavy screens
- Use jargon or corporate speak
- Make jokes about money or deadlines (serious topics)
- Be cute when users need help

---

## 7. Anti-Patterns (What Bensley Doesn't Do)

### Design Anti-Patterns

| We DON'T | Why |
|----------|-----|
| Cookie-cutter designs | Every project is custom |
| Budget-driven compromises | Quality over speed |
| Design without story | Narrative is core to everything |
| Ignore sustainability | Bill is passionate about conservation |

### Business Anti-Patterns

| We DON'T | Why |
|----------|-----|
| Rush proposals | Quality takes time |
| Compete on price | We compete on vision |
| Take every project | Selectivity matters |
| Work without contracts | Professionalism always |

### Platform Anti-Patterns

| NEVER Do | Do Instead |
|----------|------------|
| Show stale data | Show last-updated timestamps |
| Guess project links | Verify with project codes |
| Send automated emails to clients | All external comms human-reviewed |
| Delete data without backup | Always backup before bulk operations |
| Mix proposals and projects | They are distinct lifecycle stages |

---

## 8. Key Business Concepts

### Proposals vs Projects

| Stage | Table | Description |
|-------|-------|-------------|
| **Proposal** | `proposals` | Pre-contract, sales pipeline, pursuing work |
| **Project** | `projects` | Won contract, active delivery, billing |

A proposal becomes a project when **contract is signed**.

### Project Codes

Format: `BK-XXX` (e.g., BK-069, BK-045)

- BK = Bensley project identifier
- Numbers are sequential within the system
- Same code used across proposals → projects → invoices

### Invoice Codes

Format: `I24-XXX` (e.g., I24-017)

- I = Invoice
- 24 = Year (2024)
- XXX = Project number

### Client Relationship Levels

| Level | Description |
|-------|-------------|
| **Repeat Client** | Multiple projects over years (Four Seasons, Capella) |
| **New Client** | First project together |
| **Developer** | Large-scale developers with multiple properties |
| **Owner** | Individual property owners |

---

## 9. Key Stakeholders

### Internal

| Role | Responsibilities |
|------|------------------|
| **Bill Bensley** | Creative direction, client relationships, final approvals |
| **Project Managers (PMs)** | Day-to-day project execution, client communication |
| **Design Team** | Drawings, renderings, specifications |
| **Landscape Team** | Site planning, planting, hardscape |
| **Operations** | Contracts, invoices, scheduling |
| **Accounting** | Financial tracking, payment processing |

### External

| Role | Communication Style |
|------|---------------------|
| **Clients** | Professional, warm, responsive |
| **Contractors** | Technical, precise, documented |
| **Consultants** | Collaborative, clear scope boundaries |
| **Vendors** | Specification-driven, quality-focused |

---

## 10. Seasonal Patterns

| Period | Business Pattern |
|--------|------------------|
| Q1 (Jan-Mar) | New project starts, budget approvals |
| Q2 (Apr-Jun) | Peak activity, site visits |
| Q3 (Jul-Sep) | Monsoon season, more office work |
| Q4 (Oct-Dec) | Project completions, year-end invoicing |

---

## Quick Reference for Agents

### Before Writing Any Code, Ask:

1. **Does this respect the proposal → project lifecycle?**
2. **Does this use BK-XXX project codes consistently?**
3. **Would Bill approve of this UI/UX?**
4. **Is this appropriate for luxury hospitality context?**
5. **Does this match the Bensley voice (balanced: professional + playful)?**

### Key Files

| Purpose | File |
|---------|------|
| Design tokens | `frontend/src/lib/design-system.ts` |
| Voice/copy | `bensleyVoice` in design-system.ts |
| Project lifecycle | `docs/architecture/BENSLEY_PROJECT_LIFECYCLE.md` |
| Full UX guide | `docs/guides/DESIGN_SYSTEM.md` |

---

**Remember:** This platform serves one of the world's most creative design studios. The tool should be as thoughtful and well-crafted as the spaces Bensley creates.
