# Dashboard User Flows

## Personas
- **Bill (Principal)** – needs high-level visibility, checks finances and commitments.
- **Brian (PM)** – manages proposals, RFIs, and meetings.
- **Lukas (Ops)** – audits data, prepares reports, ensures follow-through.

---

## Flow 1: Track Overdue Invoices & Follow-Up
1. **Executive Overview** – Bill sees “Overdue Invoices $420k (5)” KPI.
2. Clicks KPI → **Financial Insights** screen filtered to overdue items.
3. Table shows project name + PM + days overdue; Bill selects invoice.
4. Invoice drawer reveals linked milestone and latest email thread.
5. Bill triggers **“Send reminder”** (prepares email template) or assigns follow-up to PM.
6. Status change writes back via `/invoices/{id}/actions` endpoint and surfaces in next daily report.

---

## Flow 2: Verify Contract Scope for Client Question
1. Brian receives “Is lighting design included?” request.
2. Opens **Proposal Detail** for BK-069 and jumps to **Query Console**.
3. Runs natural language query; backend returns answer + source documents.
4. Brian reviews highlighted excerpts in document viewer.
5. If out-of-scope, he generates change-order draft from same view.

---

## Flow 3: Prepare Weekly Schedule & Deliverables
1. Lukas opens **Meetings & Schedule** screen with week view.
2. Cross-checks deliverables panel showing “CD presentation 11/22” etc.
3. Uses staff workload widget to ensure owners have capacity.
4. Exports combined report (“next week schedule”) via download button powered by `/reports/schedule?week=...`.

---

## Flow 4: Monitor RFIs and Hold PMs Accountable
1. Brian starts day on **Executive Overview**; RFIs widget shows “Overdue: 2”.
2. Click to **RFI board** listing each RFI, due date, reason.
3. Select overdue item → detail pane shows latest email/comments and attachments.
4. Assign new due date or log reason via `/rfis/{id}/update`.

---

## Flow 5: Proposal Pipeline Review
1. Bill opens **Proposal Tracker** list; sorts by health ascending.
2. Filters to “Negotiating” proposals.
3. For each item, inspects timeline to see blockers (e.g., “awaiting client signature”).
4. Logs decision notes (“Call client tomorrow”) that feed accountability reports.

---

## Flow 6: Document & Email Deep Dive (Phase 1 core)
1. From Proposal Detail, Bill switches to **Email** tab to review categorized emails.
2. Hover shows AI summary, urgency, follow-up date.
3. Switch to **Documents** tab; opens contract or scope doc inline.
4. Uses quick query (“Show last invoice for this project”) to cross-validate.

---

## Flow 7: Staff Performance Snapshot
1. Lukas visits **Staff Workbench**.
2. Sorts by load % to identify overextended team members.
3. Uses assignment drawer to rebalance (calls `/projects/{code}/assignments`).
4. Notes feed into daily accountability email.

---

These flows ensure every planned feature ties back to the real questions Bill, Brian, and Lukas need answered.
