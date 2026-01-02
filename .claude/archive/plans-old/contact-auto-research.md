# Contact Auto-Research Plan (#19)

## Current State

### Database Analysis
- **Total contacts**: 467
- **Missing company**: 72 (15%)
- **Missing role/title**: 288 (62%)
- **Contacts table has fields**: company, role, position, phone, linkedin_url, location, expertise

### Email Data Available
- **1,170 emails** from external senders have body content
- Email signatures found with extractable data:
  - Titles: "Director of Planning and Development", "Head of Alternative Investments"
  - Phone numbers: +960 768 4940, +84 90 1188983
  - Companies: "MDC Project Development LLC", "Dynam Capital"
  - LinkedIn URLs (occasionally)

---

## Proposed Solution

### Data Source: Email Signatures (FREE)
We already have the data. No paid APIs needed for primary enrichment.

### Fields to Extract
| Field | Extraction Method | Confidence |
|-------|-------------------|------------|
| Phone | Regex patterns | High |
| Company | Regex + position heuristics | Medium |
| Title/Role | Line position + dictionary | Medium |
| LinkedIn URL | Regex | High |
| Location | Regex (address patterns) | Low |

### Parser Approach: Hybrid

**Stage 1: Signature Detection**
- Use simple heuristics (not full Talon) for signature location:
  - Lines after "Best regards", "Kind regards", "Sincerely", etc.
  - Lines before quoted reply markers (">", "On ... wrote:")
  - Last N lines of the email body

**Stage 2: Field Extraction (Regex)**
```python
# Phone patterns (international)
PHONE_PATTERNS = [
    r'(?:Tel|Phone|M|Mobile|T|P)[\s.:]*([+\d\s\-\(\)]{10,20})',
    r'(\+\d{1,3}[\s\-]?\d[\s\d\-]{8,15})',
]

# LinkedIn
LINKEDIN_PATTERN = r'linkedin\.com/in/[\w\-]+'

# Company (often on line with address keywords)
COMPANY_INDICATORS = ['LLC', 'Inc', 'Ltd', 'Corp', 'Group', 'Company']
```

**Stage 3: Title Detection (Dictionary + Position)**
- Dictionary of ~500 common job titles
- Titles usually appear 1-2 lines after the person's name
- Use `find-job-titles` PyPI package as starting point

### When to Run

| Trigger | Action |
|---------|--------|
| Email import | Extract signature from new emails, update contact if exists |
| Manual trigger | API endpoint: `POST /api/contacts/{id}/enrich` |
| Batch job | Nightly backfill for existing contacts |

### Storage Strategy

```sql
-- Track enrichment source and don't overwrite manual edits
ALTER TABLE contacts ADD COLUMN enrichment_source TEXT;  -- 'manual', 'email_signature', 'api'
ALTER TABLE contacts ADD COLUMN enrichment_date TEXT;
ALTER TABLE contacts ADD COLUMN enrichment_confidence REAL;
```

**Rules:**
1. Never overwrite fields marked as `enrichment_source = 'manual'`
2. Store highest confidence extraction per field
3. Log all extraction attempts for learning

---

## Implementation Plan

### Phase 1: Signature Parser Service
Create `backend/services/signature_parser_service.py`:
- Signature detection (simple heuristics)
- Phone extraction
- LinkedIn extraction
- Company name extraction
- Title extraction

### Phase 2: Integration Points
1. Hook into email import: When email is imported, try to enrich sender contact
2. Add API endpoint: `POST /api/contacts/{id}/enrich-from-emails`
3. Create background job for batch enrichment

### Phase 3: Testing & Tuning
- Test against 50 sample emails with known signatures
- Tune regex patterns based on actual data
- Set confidence thresholds

---

## Safeguards

1. **Manual edit protection**: Track `enrichment_source` column
2. **Confidence scoring**: Only apply high-confidence extractions automatically
3. **Review queue**: Low-confidence extractions create suggestions for human review
4. **Audit log**: Store all extraction attempts in `contact_enrichment_log` table

---

## Success Criteria

- [ ] Parser extracts company/title from 50%+ of signatures with signatures
- [ ] Phone extraction works for 80%+ of signatures with phone numbers
- [ ] Manual edits are NEVER overwritten
- [ ] New contacts get auto-enriched on email import
- [ ] Can manually trigger enrichment for any contact
- [ ] All extractions logged for learning

---

## Future Enhancements (Not This PR)

1. **External API fallback**: Use Apollo.io or Hunter.io free tier for contacts without signatures
2. **LinkedIn scraping**: If we have LinkedIn URL, could scrape public profile
3. **Company website lookup**: Domain from email -> company website -> about page

---

## Research Sources

- [Talon (Mailgun)](https://github.com/mailgun/talon) - Email signature extraction library
- [Parsio Guide](https://parsio.io/blog/parsing-email-signatures/) - Comprehensive signature parsing guide
- [find-job-titles PyPI](https://pypi.org/project/find-job-titles/) - Job title extraction library
- [Hunter.io](https://hunter.io/clearbit-enrichment-api-alternative) - Contact enrichment API with free tier
- [Apollo.io](https://www.apollo.io) - B2B contact database with 100 free credits

---

## Questions for Lukas

1. **Automatic vs Suggestions**: Should extracted data be applied automatically (high confidence) or always create suggestions for review?
2. **Priority contacts**: Should we focus on proposal-related contacts first?
3. **External APIs**: Worth the complexity of integrating Hunter.io/Apollo for cases where signatures don't have the data?
