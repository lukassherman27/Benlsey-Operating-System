# Invoice Review Instructions

## 📄 File Location
**CSV to review:** `reports/invoices_for_review.csv`
**Copy on Desktop:** `/Users/lukassherman/Desktop/invoices_for_review.csv`

---

## 📊 What You Have

**Total Invoices:** 186 (cleaned from 1,875 raw rows)
- ✅ **Paid:** 146 invoices
- ⚠️ **Outstanding:** 40 invoices ($9.8M)
- 🚩 **Needs Review:** 6 invoices (missing project codes)

**Projects Covered:** 14 projects
- 24 BK-074 (Dang Thai Mai): 31 invoices
- 20 BK-047 (Audley Square): 27 invoices
- 23 BK-071 (St. Regis Thousand Island): 26 invoices
- 23 BK-093 (Mumbai): 17 invoices
- 22 BK-095 (Wynn Al Marjan): 10 invoices
- And 9 more...

---

## ✏️ How to Review

### Option 1: Quick Review (Recommended)
**Just fix the 6 invoices marked "needs_review: YES"**

These 6 rows are missing project codes. You need to:
1. Open `reports/invoices_for_review.csv` in Excel/Numbers
2. Filter where `needs_review = YES`
3. Add the correct `project_code` for each invoice
4. Save and send back to me

### Option 2: Full Review
Open the CSV and verify/edit these columns:
- `project_code` - Should match your project list (e.g., "25 BK-030")
- `invoice_number` - Invoice ID (e.g., "I25-087")
- `invoice_date` - When invoice was issued (YYYY-MM-DD)
- `invoice_amount` - Invoice total
- `payment_date` - When payment received (blank if unpaid)
- `payment_amount` - Amount received (blank if unpaid)
- `phase` - mobilization, concept, dd, cd, ca (or leave blank)
- `discipline` - Landscape, Architectural, Interior (or leave blank)
- `notes` - Any notes for yourself

**What to check:**
- ✅ Dates are in YYYY-MM-DD format (e.g., 2025-10-06)
- ✅ Amounts are numbers without currency symbols
- ✅ Project codes exist in your database
- ✅ Invoice numbers match your records

---

## 🚩 Priority Items

### Outstanding Invoices Needing Review
```
UNKNOWN PROJECT:
  I25-082: $294,000
  I25-099: $1,960,000  ← BIG ONE!
  I25-121: $294,000
```

**These 3 invoices are $2.5M outstanding but have no project code!**

---

## 📥 When You're Done

**Option A - Quick Fix:**
Just tell me the project codes for those 6 invoices and I'll update them manually.

**Option B - Full Review:**
Save the CSV and I'll import everything to the database.

**Option C - Add More:**
Add any missing invoices directly to the CSV using the same format.

---

## 📋 CSV Column Reference

| Column | Required | Format | Example |
|--------|----------|--------|---------|
| project_code | YES | XX BK-XXX | 25 BK-030 |
| project_name | Auto-filled | Text | Beach Club Mandarin |
| invoice_number | YES | IXXXX | I25-087 |
| invoice_date | YES | YYYY-MM-DD | 2025-08-26 |
| invoice_amount | YES | Number | 8000.00 |
| payment_date | If paid | YYYY-MM-DD | 2025-10-06 |
| payment_amount | If paid | Number | 8000.00 |
| phase | Optional | mobilization/concept/dd/cd/ca | mobilization |
| discipline | Optional | Landscape/Architectural/Interior | Landscape |
| notes | Optional | Text | Monthly installment |
| status | Auto | paid/outstanding | paid |
| needs_review | Flag | YES/blank | YES |

---

## 💡 Tips

1. **Focus on outstanding invoices first** - That's the $9.8M we need to track
2. **Don't worry about phase/discipline** - We can add that later
3. **The 3 unknown invoices** - These are the most critical to identify
4. **Duplicates removed** - I already removed 68 duplicate invoice numbers
5. **Dates converted** - I converted "6-Oct-25" to "2025-10-06" format

---

## ❓ Questions to Answer

1. What are the project codes for these 3 big unknown invoices?
   - I25-082 ($294K)
   - I25-099 ($1.96M) ← This is huge!
   - I25-121 ($294K)

2. Should I import all 186 invoices or just the outstanding 40?

3. Do you want to add more invoices manually or is this good for now?

---

**Ready to import when you are!** 🚀
