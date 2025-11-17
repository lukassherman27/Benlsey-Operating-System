# AI Agent Context & Collaboration Charter

**Goal:** Build the Bensley Business Brain — a unified operations platform that surfaces everything Bill/Brian need (proposals, finances, meetings, staff, RFIs, documents, AI intelligence) with minimal UI friction. Codex (frontend) and Claude (backend/data) collaborate to deliver end-to-end capabilities without blindly rubber-stamping requests. Every decision should serve this end-state, even if it means challenging the initial idea.

---

## Roles

### Claude (Backend/Data/Infrastructure)
- Owns database schema, migrations, ingestion scripts, service layer, FastAPI endpoints, cron jobs, automation agents.
- Responsible for data quality, consistency, and scalability. Should propose better architecture or data models instead of just wiring whatever Codex asks for.
- Expected to push back when the suggested approach (e.g., RAG, new tables, automation) isn’t ideal for the business brain or would create long-term debt.

### Codex (Frontend/Product Integration)
- Owns Next.js/Tailwind dashboard, documentation, coordination, user-facing polish, and integration with backend APIs.
- Responsible for translating Bill’s needs into clear UI/UX and specifying data contracts. Should call out when backend endpoints are missing/incomplete or when the UX request doesn’t align with the goal.
- Expected to challenge feature ideas if they don’t improve the business brain (e.g., “we don’t need another table of buttons; we need automation”).

### Shared Responsibilities
- Keep MCP filesystem server running so both agents automatically see file updates (no manual relays). If MCP access fails, pause and notify the user.
- Maintain `AI_DIALOGUE.md`, `SESSION_LOGS.md`, `SYSTEM_STATUS.md`, and `BENSLEY_BRAIN_MASTER_PLAN.md` so they reflect current reality within the same day.
- Use manual overrides + intelligence queue as guardrails: backend enforces data integrity, frontend ensures UX gives Bill easy ways to approve/snooze/fix.

---

## Communication & Coordination Principles

1. **Context first:** Before coding, both agents read `AI_DIALOGUE.md`, `SESSION_LOGS.md`, and this file to align with current progress.
2. **Challenge vs. confirm:** If the user suggests a tool/approach (e.g., “let’s do RAG”), evaluate fit vs. the Bensley Brain goal. Explain pros/cons rather than auto-approving.
3. **Single source of truth:** Database path, schema status, audit results must be consistent across docs. If numbers conflict, call it out and resolve before building UI/automation.
4. **Document everything:** Major changes, audits, and plans go into `SESSION_LOGS.md` and `AI_DIALOGUE.md` so both agents and the user can see the narrative.
5. **Hand-offs:** When Claude finishes backend work, he should note any API changes in `AI_DIALOGUE.md` + docs. When Codex finishes UI changes, he should note required backend follow-ups.
6. **User-first automation:** Always ask “Does this remove friction for Bill/Brian?” If not, propose a better alternative.
7. **MCP usage:** Both agents connect to the MCP filesystem server and rely on it for reading/writing shared files. When a file changes, re-check `AI_DIALOGUE.md` before proceeding.
8. **Manual overrides & intelligence queue:** Treat `/api/manual-overrides` and `/api/intel/*` as the canonical override/learning pipelines. UI/UX or scripting changes should integrate with those services, not bypass them.

---

## Live Systems to Be Aware Of

- **Daily Briefing API/UI** — `/api/briefing/daily` powers the main dashboard hero/priority feed. Any backend change here must be coordinated immediately with frontend.
- **Intelligence Suggestions** — `/api/intel/suggestions`, `/api/intel/suggestions/{id}/decision`, `/api/intel/patterns`, `/api/intel/decisions`. Frontend inbox is live; backend changes must maintain payload shape (id, project_code, impact, evidence).
- **Manual Overrides** — `/api/manual-overrides` (GET/POST/PATCH/apply). Used for “Provide context” modal; keep schema stable.
- **MCP Coordination** — Server configured per `MCP_SETUP_GUIDE.md`. Both agents must confirm MCP is active before each work session.
- **Comprehensive Audit Plan** — See `COMPREHENSIVE_AUDIT_SYSTEM_PLAN.md`. Phase 2 introduces new tables/endpoints (scope, fee breakdown, timeline, contract, audit feedback). Treat this as the near-term roadmap.

---

## Shared Deliverables & Priorities (Rolling)

1. **Canonical Database** – both agents use the same SQLite DB (`/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db`) unless otherwise noted. Audits must match DB in use.
2. **Documentation** – keep `DATA_QUALITY_REPORT.md`, `SYSTEM_STATUS.md`, `AI_DIALOGUE.md`, `SESSION_LOGS.md`, and this context file updated so future sessions hit the ground running.
3. **Business Brain End-State** – every feature should move toward a system where Bill can ask “What’s blocking BK-033?” and instantly get answers. Prefer automation/AI flows over manual UI where possible.
4. **Healthy disagreement** – If one agent sees a better approach, they should state it clearly and explain tradeoffs. The goal is the best outcome, not blind agreement.
5. **Phase 2 Audit System** – Claude builds the scope/fee/timeline/contract tables + APIs; Codex designs the audit review UI. Both document payloads/types as soon as they exist (`INTEGRATION_GUIDE.md`).

---

## How to Adjust This File

- If responsibilities shift or collaboration rules change, edit this file and note the update in `AI_DIALOGUE.md` so both agents refresh context.
- Treat this as the “team charter” — it should evolve as we learn what works best for building the business brain.

---
### AI Dialogue Status Tracker
| Timestamp (YYYY-MM-DD HH:MM) | Subject | Claude | Codex |
| --- | --- | --- | --- |
| 2025-11-15 11:00 | Recent-activity fix + email import | ✅ | ☑️ |
| 2025-11-16 04:00 | Phase 2 audit schema kickoff | 🚧 | ☐ |

## Coordination Conventions (Checklist + Threads)

1. **Every entry in `AI_DIALOGUE.md` ends with a status tag**  
   ` [**Status:** Claude ☐ | Codex ☐]`  
   - Agent checks their box (☐ → ✅) when they read/respond.  
   - This makes it obvious which requests are pending.

2. **Subject headers stay intact**  
   - Claude and Codex append replies under the relevant heading.  
   - No editing older content; only append to keep chronology clear.

3. **Daily session summary**  
   - Each agent logs a short summary in `SESSION_LOGS.md` (date, focus, key files, next steps).

4. **Shared table (optional)**  
   - If needed, maintain a simple “Request → Owner → Status” table at the top of `AI_DIALOGUE.md` to visualize pending items.

5. **MCP check-ins**  
   - At session start, confirm MCP connection (see `MCP_SETUP_GUIDE.md`). If either agent can’t access files, pause and resolve before editing to avoid divergent context.

Following these conventions ensures both agents and the user can see at a glance which messages have been addressed and what’s outstanding.
