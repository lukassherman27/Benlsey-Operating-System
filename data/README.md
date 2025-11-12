# BENSLEY DESIGN STUDIOS - DATA ORGANIZATION

This folder contains ALL actual project files, emails, and documents.

## Structure:

### 01_CLIENTS/
Client entities who PAY for projects (developers, owners, private clients)
- Each client has: contracts, invoices, payments, project links

### 02_OPERATORS/
Hotel brands/operators (Rosewood, Mandarin Oriental, Four Seasons, etc.)
- Brand guidelines, design standards, project references

### 03_PROPOSALS/
Active proposals that haven't been signed yet
- Status: draft, submitted, negotiating

### 04_ACTIVE_PROJECTS/
Signed contracts, ongoing work (BK-XXX format)
Subfolders: Contract, Invoicing, Design, Scheduling, Correspondence, RFIs, Meetings, Photos

### 05_LEGAL_DISPUTES/
Projects with legal issues, disputes, payment problems

### 06_ARCHIVE/
Completed and closed projects

### 07_EMAILS/
- raw/ - Downloaded directly from email server
- processed/ - Organized and linked to projects
- attachments/ - All email attachments extracted

### 08_TEMPLATES/
Reusable templates for invoices, proposals, contracts, schedules

---

## Project Folder Standard Structure:

```
BK-XXX_Project_Name/
├── 01_CONTRACT/
├── 02_INVOICING/
│   ├── invoices_sent/
│   ├── payment_receipts/
│   └── billing_schedule.json
├── 03_DESIGN/
│   ├── architecture/
│   ├── interiors/
│   └── landscape/
├── 04_SCHEDULING/
│   ├── project_schedule.json
│   ├── staff_assignments/
│   └── milestones/
├── 05_CORRESPONDENCE/
├── 06_SUBMISSIONS/
├── 07_RFIS/
├── 08_MEETINGS/
├── 09_PHOTOS/
└── metadata.json
```

## Metadata JSON Format:

```json
{
  "project_code": "BK-001",
  "project_name": "Resort Project Name",
  "client": "ABC Development Corp",
  "operator": "Rosewood Hotels",
  "contract_value": 2500000,
  "start_date": "2024-01-01",
  "completion_target": "2025-12-31",
  "current_phase": "Design Development",
  "team_lead": "Bill Bensley",
  "status": "active"
}
```
