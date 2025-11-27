# Invoice Link Examples - Verify These

## 10 SPECIFIC EXAMPLES YOU CAN VERIFY

### 1. TARC Invoices (Your $3M Project)

```sql
-- Current state (WRONG):
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code, p.project_title
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number IN ('I24-017', 'I25-017');

Results:
I24-017 | $150,835 | project_id 3613 | 23 BK-088 | Mandarin Oriental Bali ❌
I25-017 | $150,835 | project_id 3621 | 23 BK-089 | Jyoti's farm house ❌
```

**What it SHOULD be:**
```
I24-017 | $150,835 | project_id 115075 | 25 BK-017 | TARC ✅
I25-017 | $150,835 | project_id 115075 | 25 BK-017 | TARC ✅
```

---

### 2. Mandarin Oriental Bali (BK-088)

```sql
-- Check current state:
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number IN ('I24-088', 'I25-088');

Results:
I24-088 | (amount) | project_id 3632 | 24 BK-074 ❌
I25-088 | (amount) | project_id 115073 | 24 BK-058 ❌
```

**What it SHOULD be:**
```
I24-088 | (amount) | project_id 3613 | 23 BK-088 ✅
I25-088 | (amount) | project_id 3613 | 23 BK-088 ✅
```

---

### 3. Ritz Carlton Nanyan Bay (BK-018)

```sql
-- Check current state:
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number IN ('I23-018');

Results:
I23-018 (3 invoices) | Total $498,755 | project_id 3609 | 22 BK-095 Wynn Al Marjan ❌
```

**What it SHOULD be:**
```
I23-018 (3 invoices) | Total $498,755 | project_id 3614 | 25 BK-018 Ritz Carlton ✅
```

---

### 4. Capella Ubud (BK-021)

```sql
-- Check current state:
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number LIKE 'I23-021%';

Results:
I23-021 (2 invoices) | Total $75,000 | project_id 3607 | 22 BK-013 Tel Aviv ❌
```

**What it SHOULD be:**
```
I23-021 (2 invoices) | Total $75,000 | project_id 3624 | 24 BK-021 Capella Ubud ✅
```

---

### 5. St. Regis Thousand Island (BK-096 & BK-071)

```sql
-- Check current state:
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number IN ('I20-096', 'I23-071');

Results:
I20-096 (3 invoices) | Total $247,000 | project_id 3601 | 19 BK-018 Villa Ahmedabad ❌
I23-071 | $71,175 | project_id 3610 | 23 BK-009 Villa Ahmedabad ❌
```

**What it SHOULD be:**
```
I20-096 (3 invoices) | Total $247,000 | project_id 3616 | 23 BK-096 St. Regis ✅
I23-071 | $71,175 | project_id 3615 | 23 BK-071 St. Regis ✅
```

---

### 6. Treasure Island Resort (BK-067 & BK-068)

```sql
-- Check current state:
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number IN ('I21-067', 'I21-068');

Results:
I21-067 | $71,250 | project_id 3601 | 19 BK-018 Villa Ahmedabad ❌
I21-068 | $149,625 | project_id 3601 | 19 BK-018 Villa Ahmedabad ❌
```

**What it SHOULD be:**
```
I21-067 | $71,250 | project_id 3617 | 23 BK-067 Treasure Island Intercontinental ✅
I21-068 | $149,625 | project_id 3618 | 23 BK-068 Treasure Island Caribbean Castle ✅
```

---

### 7. Ramhan Marina Abu Dhabi (BK-001)

```sql
-- Check current state:
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number = 'I23-001';

Results:
I23-001 | $17,812.50 | project_id 3601 | 19 BK-018 Villa Ahmedabad ❌
```

**What it SHOULD be:**
```
I23-001 | $17,812.50 | project_id 3634 | 25 BK-001 Ramhan Marina Abu Dhabi ✅
```

---

### 8. Tonkin Palace Hanoi (BK-002)

```sql
-- Check current state:
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number = 'I23-002';

Results:
I23-002 | $24,937.50 | project_id 3601 | 19 BK-018 Villa Ahmedabad ❌
```

**What it SHOULD be:**
```
I23-002 | $24,937.50 | project_id 3633 | 25 BK-002 Tonkin Palace Hanoi ✅
```

---

### 9. Hotel Trident India (BK-043)

```sql
-- Check current state:
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number = 'I22-043';

Results:
I22-043 | $49,875 | project_id 3601 | 19 BK-018 Villa Ahmedabad ❌
```

**What it SHOULD be:**
```
I22-043 | $49,875 | project_id 3629 | 24 BK-043 Hotel Trident India ✅
```

---

### 10. Ultra Luxury Beach Resort (BK-050)

```sql
-- Check current state:
SELECT i.invoice_number, i.payment_amount, i.project_id, p.project_code
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number = '25-050';

Results:
25-050 | $31,172.50 | project_id 3609 | 22 BK-095 Wynn Al Marjan ❌
```

**What it SHOULD be:**
```
25-050 | $31,172.50 | project_id 3622 | 23 BK-050 Ultra Luxury Beach Resort ✅
```

---

## THE PATTERN

**Notice anything?** A few projects are being used as "dumping grounds":

- **Project 3601 (19 BK-018 Villa Ahmedabad):** Has invoices from 30+ different projects
- **Project 3607 (22 BK-013 Tel Aviv):** Has invoices from 15+ different projects
- **Project 3608 (22 BK-046 Nusa Penida):** Has invoices from 10+ different projects
- **Project 3609 (22 BK-095 Wynn Al Marjan):** Has invoices from 12+ different projects

This suggests invoices were imported and randomly assigned to whatever project IDs existed, rather than matching by project code.

## HOW TO VERIFY IN YOUR DATABASE

Run this query to see the problem:

```sql
SELECT
    i.invoice_number,
    i.payment_amount,
    p.project_code as "Current Project Code",
    p.project_title as "Current Project Name",
    CASE
        WHEN i.invoice_number LIKE 'I%' THEN
            'BK-' || substr(i.invoice_number, instr(i.invoice_number, '-') + 1, 3)
        WHEN i.invoice_number LIKE '25-%' THEN
            'BK-' || substr(i.invoice_number, 4, 3)
        ELSE 'Unknown'
    END as "Should be project code"
FROM invoices i
LEFT JOIN projects p ON i.project_id = p.project_id
WHERE i.invoice_number IN (
    'I24-017', 'I25-017',  -- TARC
    'I24-088', 'I25-088',  -- Mandarin Oriental
    'I23-018',             -- Ritz Carlton
    'I23-021',             -- Capella
    'I23-001', 'I23-002'   -- Ramhan, Tonkin
)
ORDER BY i.invoice_number;
```

This will show you the mismatch between where invoices are currently linked vs. where they should be linked.
