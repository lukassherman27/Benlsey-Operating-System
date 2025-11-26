# 💰 FINANCIAL AUDIT REPORT

## Overview
- **254 invoices** totaling **$29.8M**
- **207 paid**, **47 outstanding**
- Linked to **29 projects** only

## ⚠️ Issues Found:

### 1. Active Projects Missing Invoices (38 projects)
**Total value: $72M+ in signed contracts with NO invoices**

Top 10:
1. 24 BK-074 - Dang Thai Mai Vietnam - $4.9M
2. 23 BK-050 - Ultra Luxury Bodrum Turkey - $4.65M  
3. 22 BK-013 - Tel Aviv High Rise - $4.15M
4. 25 BK-037 - India Wellness hotel - $4M
5. 25 BK-027 - 30 Residence Villas Bai Bac - $3.95M
6. 22 BK-095 - Wynn Al Marjan Island - $3.77M
7. 24 BK-029 - Qinhu Resort China - $3.25M
8. 23 BK-068 - Treasure Island Resort - $3.25M
9. 25 BK-017 - TARC Delhi - $3M
10. 23 BK-029 - Mandarin Oriental Bali - $2.9M

### 2. Payment Tracking Issue
- All invoices show $0 in `payment_amount` field
- But 207 marked as "Paid" status
- Need to verify actual payment amounts

## 📊 Available Audit Tools:

### API Endpoints:
```bash
# Get all invoices
GET /api/invoices

# Get invoices for specific project  
GET /api/projects/{code}/invoices

# Get financial overview
GET /api/dashboard/stats

# Get decision tiles (includes invoice alerts)
GET /api/dashboard/decision-tiles

# Get audit suggestions
GET /api/intel/suggestions
```

### Database Tables:
1. **invoices** - Main invoice tracking (254 records)
2. **project_financials** - Project-level financial data
3. **project_fee_breakdown** - Phase-based fee tracking (Phase 2 - empty)
4. **contract_terms** - Contract details (Phase 2 - empty)

## ✅ Next Steps:

1. **Import missing invoice data** for 38 active projects
2. **Fix payment amounts** - populate payment_amount field for paid invoices
3. **Populate Phase 2 tables** with contract/fee breakdown data
4. **Link invoices to projects** properly (use project_code instead of project_id)
5. **Run comprehensive audit** to find all mismatches

