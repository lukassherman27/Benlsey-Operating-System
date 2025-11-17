-- Migration 019: Fix Invoice Data Quality Issues
-- 1. Set payment_amount = invoice_amount for paid invoices
-- 2. Calculate due_date based on contract payment terms

-- Fix 1: Set payment_amount for paid invoices that have payment_date but no payment_amount
UPDATE invoices
SET payment_amount = invoice_amount
WHERE payment_date IS NOT NULL
  AND (payment_amount IS NULL OR payment_amount = 0)
  AND invoice_amount IS NOT NULL
  AND invoice_amount > 0;

-- Fix 2: Calculate due_date based on contract payment terms
-- For invoices linked to contracts, calculate: due_date = invoice_date + days_to_pay
UPDATE invoices
SET due_date = date(invoice_date, '+' || (
    SELECT json_extract(ct.payment_schedule, '$.payment_terms.days_to_pay')
    FROM contract_terms ct
    WHERE ct.project_code = invoices.project_code
    LIMIT 1
) || ' days')
WHERE invoice_date IS NOT NULL
  AND due_date IS NULL
  AND project_code IN (SELECT project_code FROM contract_terms);

-- Update migration ledger
INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (19, '019_fix_invoice_data_quality',
       'Fix payment amounts for paid invoices and calculate due dates from contract terms',
       datetime('now'));
