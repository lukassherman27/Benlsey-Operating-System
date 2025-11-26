# Data Import Template for Accountant

## CRITICAL: What We Need Right Now

### 1. INVOICES (Most Urgent)
**Excel columns needed:**
- `invoice_number` - e.g., "I25-069"
- `project_code` - e.g., "25 BK-030"
- `invoice_date` - when invoice was issued
- `due_date` - when payment is due
- `amount_usd` - total invoice amount
- `amount_paid` - how much has been paid
- `payment_date` - when payment was received (if paid)
- `status` - "pending", "paid", "overdue", "partial"
- `description` - brief description (e.g., "Mobilization Fee", "Design Development 25%")

**Example Row:**
```
I25-069 | 25 BK-030 | 2025-06-15 | 2025-07-15 | 50000 | 50000 | 2025-06-20 | paid | Mobilization Fee
```

---

### 2. CONTRACT VALUES (Important)
**Excel columns needed:**
- `project_code` - e.g., "25 BK-030"
- `contract_total_usd` - total contract value
- `contract_signed_date` - when contract was signed
- `payment_terms` - e.g., "30% upfront, 40% at DD, 30% at completion"

**Example Row:**
```
25 BK-030 | 150000 | 2025-06-01 | 30% upfront, 40% at DD, 30% at completion
```

---

### 3. PROPOSAL VALUES (For Active Proposals)
**Excel columns needed:**
- `project_code` - e.g., "25 BK-068"
- `proposal_value_usd` - proposed contract value
- `proposal_sent_date` - when proposal was sent to client
- `proposal_status` - "sent", "negotiating", "won", "lost"
- `last_contact_date` - last time we followed up

**Example Row:**
```
25 BK-068 | 200000 | 2025-06-10 | negotiating | 2025-06-20
```

---

## OPTIONAL (Can Wait)

### 4. EXPENSES (Lower Priority)
- Date, Description, Amount, Project Code

### 5. BUDGET/FORECAST (Lower Priority)
- Project Code, Budgeted Hours, Actual Hours

---

## FORMAT REQUIREMENTS

1. **Use simple Excel (.xlsx) or CSV**
2. **One sheet per category** (Invoices, Contracts, Proposals)
3. **First row must be column headers**
4. **Dates in format: YYYY-MM-DD** (e.g., 2025-06-15)
5. **Numbers without commas** (e.g., 50000 not 50,000)
6. **Project codes must match existing codes** (see list below)

---

## EXISTING PROJECT CODES (For Reference)

Based on current database:
- 25 BK-006, 25 BK-012, 25 BK-013, 25 BK-017, 25 BK-018
- 25 BK-021, 25 BK-023, 25 BK-024, 25 BK-030, 25 BK-033
- BK-008, BK-028, BK-029, BK-035, BK-036, BK-038, BK-040
- BK-041, BK-042, BK-045, BK-046, BK-048, BK-051, BK-052
- BK-053, BK-054, BK-058, BK-068, BK-069, BK-070, BK-071
- BK-072, BK-074, BK-078, BK-080, BK-087

**If project code doesn't exist, add column `project_name` so we can create it.**

---

## DELIVERY

Send completed Excel file to: [your email]

**Target delivery:** ASAP (critical for financial dashboard)
