# Bensley Business Intelligence Data Inventory

## Goal
Build a comprehensive LLM that knows everything about Bensley operations through model distillation from GPT-4.

## Current Data Assets (✅ Have)

### 1. Email System
- **Location**: `database/bensley_master.db` → `emails` table
- **Count**: 3,523 emails (May 2025 - Nov 2025)
- **Includes**: Subject, body, sender, recipients, date, folder
- **Attachments**: 1,800+ files in `/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/`
- **Status**: ✅ Imported and indexed

### 2. Projects/Proposals
- **Location**: `database/bensley_master.db` → `proposals` table
- **Count**: 87 projects
- **Includes**: Project code, name, client, status, value, contact info, dates
- **Status**: ✅ Structured and tracked

### 3. Email-Project Links
- **Location**: `database/bensley_master.db` → `email_proposal_links` table
- **Count**: 395+ links (growing)
- **Status**: 🔄 In progress (AI linking running)

### 4. Contact Mappings
- **Location**: `database/bensley_master.db` → `contact_project_mapping` table
- **Count**: 86 contact-project relationships
- **Status**: ✅ Mapped

## Missing Data Assets (❌ Need)

### 1. Contracts (CRITICAL)
- **What**: Signed contract PDFs
- **Where to find**: Finance team, project folders, email attachments
- **Data to extract**:
  - Contract value & payment terms
  - Scope of work
  - Deliverables & milestones
  - Client obligations
  - Change order terms
  - Expiration dates
- **Priority**: 🔴 HIGH
- **Action**: Request from finance team + scan email attachments

### 2. RFIs (Requests for Information)
- **What**: RFI documents and responses
- **Where to find**: Email attachments, shared drives
- **Data to extract**:
  - Question/issue raised
  - Response provided
  - Date submitted/answered
  - Project phase
- **Priority**: 🟡 MEDIUM
- **Action**: Create rfi@bensley.com email, scan historical emails

### 3. Invoices
- **What**: Invoice PDFs sent to clients
- **Where to find**: Finance team, accounting system
- **Data to extract**:
  - Invoice number & date
  - Amount billed
  - Payment status
  - Services/phase covered
  - Payment received date
- **Priority**: 🔴 HIGH
- **Action**: Request from finance team (use ACCOUNTANT_DATA_TEMPLATE.md)

### 4. Financial Sheets
- **What**: P&L statements, budgets, forecasts
- **Where to find**: Finance team, Bill's records
- **Data to extract**:
  - Revenue by project
  - Costs by project
  - Profit margins
  - Cash flow
  - Forecast vs actual
- **Priority**: 🔴 HIGH
- **Action**: Request from finance team

### 5. Project Schedules
- **What**: Timelines, Gantt charts, milestone tracking
- **Where to find**: Project managers, shared drives
- **Data to extract**:
  - Phase start/end dates
  - Milestone completions
  - Delays and reasons
  - Critical path items
- **Priority**: 🟡 MEDIUM
- **Action**: Request from project managers

### 6. Meeting Notes/Transcripts
- **What**: Client meeting notes, internal meeting records
- **Where to find**: Bill's notes, email summaries, Zoom transcripts
- **Data to extract**:
  - Decisions made
  - Action items
  - Client feedback
  - Design changes
- **Priority**: 🟢 LOW (can be extracted from emails)
- **Action**: Set up Zoom auto-transcription

### 7. Design Files (Metadata Only)
- **What**: CAD files, renderings, presentations
- **Where to find**: Design team drives
- **Data to extract**: File names, versions, dates, project links (NOT the actual files)
- **Priority**: 🟢 LOW
- **Action**: Scan drive structure

## Data Organization Structure

```
/Users/lukassherman/Desktop/BDS_SYSTEM/
├── 01_CONTRACTS/
│   ├── {project_code}_{contract_name}.pdf
│   └── extracted/
│       └── {project_code}_contract_data.json
├── 02_INVOICES/
│   ├── {invoice_number}.pdf
│   └── extracted/
│       └── {invoice_number}_data.json
├── 03_RFIS/
│   ├── {project_code}/
│   │   └── RFI_{number}_{date}.pdf
│   └── extracted/
│       └── {project_code}_rfis.json
├── 04_FINANCIAL/
│   ├── P&L/
│   ├── Budgets/
│   └── Forecasts/
└── 05_FILES/  ← Already exists (email attachments)
    └── BY_DATE/
```

## Data Collection Plan

### Week 1: Critical Data
1. ✅ Import all emails (DONE)
2. ⏳ Link emails to projects (IN PROGRESS)
3. 📋 Request contracts from finance team
4. 📋 Request invoices from finance team
5. 📋 Request P&L and financial sheets

### Week 2: Extraction & Processing
1. Extract data from contract PDFs
2. Extract data from invoice PDFs
3. Parse financial sheets into database
4. Link RFIs found in email attachments
5. Run full email-project linking

### Week 3: Intelligence Layer
1. Build query interface over all data
2. Create embeddings for semantic search
3. Fine-tune/distill model on Bensley data
4. Test Q&A capabilities
5. Deploy dashboard

## Business Intelligence Use Cases

Once complete, the LLM should be able to answer:

**Project Questions:**
- "What's the status of the Maldives project?"
- "Show me all emails with DAR Global"
- "What were the payment terms for BK-042?"
- "Has the Sabrah project responded to our last email?"

**Financial Questions:**
- "What's our revenue for Q3?"
- "Which projects are most profitable?"
- "Show me all overdue invoices"
- "What's the pipeline value for India projects?"

**Operational Questions:**
- "Which proposals need follow-up this week?"
- "What RFIs are pending response?"
- "Who do we know at Reliance Industries?"
- "What projects is Bill personally involved in?"

## Next Steps

1. **Immediate**: Send ACCOUNTANT_DATA_TEMPLATE.md to finance team
2. **This Week**: Scan email attachments for contracts/invoices
3. **Next Week**: Build PDF extraction pipeline
4. **Month 1**: Complete data collection
5. **Month 2**: Build intelligence layer
