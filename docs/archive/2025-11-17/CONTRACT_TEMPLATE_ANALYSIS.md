# CONTRACT TEMPLATE ANALYSIS

Based on signed contract: **25 BK-030 - Beach Club at Mandarin Oriental Bali**
Date Signed: June 3, 2025

---

## Standard Contract Structure

### Fee Breakdown (Confirmed from Contract Page 8)

**Bensley Standard Fee Structure:**
- **15% Mobilization** (due on signing, non-refundable)
- **25% Conceptual Design**
- **30% Design Development** (Detailed Design)
- **15% Construction Documents**
- **15% Construction Observation** (CA)

**Total: 100%**

### Example from 25 BK-030 ($550K Total):

**Architectural ($220K):**
- Mobilization: $33,000 (15%)
- Conceptual Design: $55,000 (25%)
- Design Development: $66,000 (30%)
- Construction Documents: $33,000 (15%)
- Construction Observation: $33,000 (15%)

**Interior Design ($330K):**
- Mobilization: $49,500 (15%)
- Conceptual Design: $82,500 (25%)
- Design Development: $99,000 (30%)
- Construction Documents: $49,500 (15%)
- Construction Observation: $49,500 (15%)

---

## Contract Terms Structure

### Key Fields from Contract:

1. **Contract Signed Date:** June 3, 2025
2. **Contract Term:** 24 months (from Section 2.5)
3. **Total Fee:** USD 550,000
4. **Contract Type:** Fixed Fee (standard)
5. **Payment Terms:** 15 days from invoice
6. **Late Payment Interest:** 1.5% per month
7. **Currency:** USD
8. **Payment Method:** Telegraphic Transfer

### Payment Schedule Format:

```json
{
  "mobilization": {
    "phase": "mobilization",
    "percentage": 0.15,
    "amount_usd": 82500,
    "due_on": "contract_signing",
    "refundable": false
  },
  "concept_design": {
    "phase": "concept",
    "percentage": 0.25,
    "amount_usd": 137500,
    "due_on": "phase_completion"
  },
  "design_development": {
    "phase": "dd",
    "percentage": 0.30,
    "amount_usd": 165000,
    "due_on": "phase_completion"
  },
  "construction_documents": {
    "phase": "cd",
    "percentage": 0.15,
    "amount_usd": 82500,
    "due_on": "phase_completion"
  },
  "construction_observation": {
    "phase": "ca",
    "percentage": 0.15,
    "amount_usd": 82500,
    "due_on": "phase_completion"
  }
}
```

---

## Project Relationships Identified

### Parent-Child Relationship:
- **Parent:** 23 BK-029 - Mandarin Oriental Bali
- **Child:** 25 BK-030 - Beach Club at Mandarin Oriental Bali (Additional Services)
- **Relationship Type:** additional_services
- **Component Type:** beach_club

This is an **additional services contract** for an existing active project.

---

## Contract Sections (from PDF Structure)

### Section 1.0 - Definitions
- Additional Services
- Project
- Services
- Work Scope
- Work Stage

### Section 2.0 - General Conditions
- 24-month term
- 21-day approval period for drawings
- Services performed from Bangkok office

### Section 3.0 - General Responsibilities of Bensley
- Professional duty to complete on schedule
- Inform client of additional costs

### Section 4.0 - General Responsibilities of Client
- Provide all documents
- Provide instructions promptly
- Designate coordinator
- Render approvals promptly (21 days)
- Pay amounts promptly when due

### Section 5.0 - Services and Work Scope
- Appendices 1-2 define architectural and interior scope

### Section 6.0 - Professional Fees
- Standard 5-phase breakdown
- Separate fees for architectural and interior

### Section 7.0 - Terms of Payment
- Mobilization fee due on signing
- Progress-based payments
- 15-day payment terms
- 1.5% monthly interest on overdue amounts

### Section 8.0 - Additional Services
- Hourly rates for additional work:
  - Directors: USD 220/hour
  - Project Architect: USD 190/hour
  - Architects: USD 90/hour
  - Draftspersons: USD 30/hour
  - Secretaries: USD 24/hour

### Section 9.0 - Additional Costs
- Excludes presentation materials
- Excludes communication charges
- Excludes travel expenses
- Travel reimbursed within 30 days

### Section 10.0 - Changes in Instructions
- Extra fees for scope changes
- Demobilization fee: 20% of uncommenced work

### Section 11.0 - Consultants
- Client employs M&E, structural, local architect directly

### Section 12.0 - Representations and Warranties

### Section 13.0 - Termination
- 90-day notice for termination
- 20% demobilization fee
- Force majeure provisions

### Section 14.0 - Ownership of Documents
- Bensley retains IP rights
- Limited use license to client

### Section 15.0 - Miscellaneous
- Governed by Indonesian law
- English language controls

---

## Appendix 1 - Architectural Scope

**Stage A: Conceptual Design**
- Establish program and parameters
- Co-ordinate with consultants
- Prepare illustrative drawings
- Get approval before proceeding

**Stage B: Design Development**
- Develop design based on approved concept
- Coordinate with local architect
- Liaise with consultants
- Provide construction planning info

**Stage C: Working Drawings**
- Prepare construction drawings
- Prepare specifications
- Construction detailing

**Stage D: Tender Phase**
- Clarify drawings during tender

**Stage E: Construction Observation**
- Monthly site visits
- Observation reports
- Answer clarifications

**Exclusions:**
- Local government approvals (local architect)
- Tender documentation
- Contractor communication
- Full-time resident architect

---

## Appendix 2 - Interior Design Scope

**Six (6) phases:**
- Stage A: Conceptual Design
- Stage B: Design Development
- Stage C: Construction Documentation
- Stage D: Project Coordination
- Stage E: Project Completion and Sign Off
- Stage F: Post Occupancy Refinements

---

## Database Population Template

### For contract_terms table:

```python
{
    "project_code": "25 BK-030",
    "contract_signed_date": "2025-06-03",
    "contract_start_date": "2025-06-03",
    "total_contract_term_months": 24,
    "contract_end_date": "2027-06-03",
    "total_fee_usd": 550000,
    "payment_schedule": payment_schedule_json,
    "contract_type": "fixed_fee",
    "retainer_amount_usd": None,
    "final_payment_amount_usd": 82500,  # CA phase
    "early_termination_terms": "20% demobilization fee",
    "amendment_count": 0,
    "original_contract_id": None,
    "contract_document_path": "/BDS_KnowledgeBase/attachments/.../25-030_Beach_Club_signed.pdf",
    "confirmed_by_user": 1,
    "confidence": 1.0
}
```

### For project_fee_breakdown table:

```python
phases = [
    {"phase": "mobilization", "percentage": 0.15, "amount": 82500},
    {"phase": "concept", "percentage": 0.25, "amount": 137500},
    {"phase": "dd", "percentage": 0.30, "amount": 165000},
    {"phase": "cd", "percentage": 0.15, "amount": 82500},
    {"phase": "ca", "percentage": 0.15, "amount": 82500}
]
```

### For projects table (relationship):

```python
{
    "project_code": "25 BK-030",
    "parent_project_code": "23 BK-029",
    "relationship_type": "additional_services",
    "component_type": "beach_club",
    "contract_signed_date": "2025-06-03"
}
```

---

## Ready to Import!

All contract data can now be populated using the ContractService methods with this template structure.
