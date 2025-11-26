# Admin Interface Implementation Plan

**Created:** 2025-11-24
**Status:** IN PROGRESS

---

## CRITICAL FINDINGS FROM AUDIT

- **3,356 emails** imported and categorized
- **1,553 emails** linked to proposals (46% coverage)
- **8 pending data validation suggestions** requiring CLI review
- **NO admin UI exists** - all management via CLI scripts
- **Manual intervention time: ~50%** (should be <5%)

---

## PHASE 1: CRITICAL ADMIN FEATURES (THIS WEEK)

### Priority 1: Data Validation Dashboard ✅ STARTING NOW
**Problem:** 8 suggestions pending, require CLI script `manage_suggestions.py`

**Solution:** `/admin/validation` page

**Features:**
- List pending suggestions with evidence
- Show email snippet that triggered suggestion
- Display current vs. suggested value
- Show AI confidence and reasoning
- Approve/Deny buttons with notes
- Stats: pending/approved/denied/applied

**API Endpoints Needed:**
```typescript
GET  /api/admin/validation/suggestions              // List all suggestions
GET  /api/admin/validation/suggestions/{id}         // Get single suggestion
POST /api/admin/validation/suggestions/{id}/approve // Approve + apply
POST /api/admin/validation/suggestions/{id}/deny    // Deny + notes
GET  /api/admin/validation/stats                    // Dashboard stats
```

**Database Tables:**
- `data_validation_suggestions` (already exists)
- `suggestion_application_log` (already exists)

---

### Priority 2: Email Link Manager
**Problem:** 1,553 links, no visibility into confidence scores or linking evidence

**Solution:** `/admin/email-links` page

**Features:**
- Search emails by project code
- Show linked emails with confidence scores
- Display linking method (auto/manual/AI)
- Show evidence/reasoning
- Unlink/relink buttons
- Bulk relinking tools

**API Endpoints Needed:**
```typescript
GET    /api/admin/email-links                           // List all links
GET    /api/admin/email-links/by-project/{project_code} // Project's emails
DELETE /api/admin/email-links/{link_id}                 // Unlink
POST   /api/admin/email-links                           // Create manual link
POST   /api/admin/email-links/bulk-relink               // Bulk operations
```

---

### Priority 3: Enhanced Email Dashboard (Bulk Operations)
**Problem:** Must edit emails one-by-one, no bulk actions

**Solution:** Enhance existing `/emails` page

**Add:**
- Checkbox selection (multi-select)
- Bulk category assignment
- Bulk project linking
- Bulk delete/archive
- Export selected emails

**API Endpoints Needed:**
```typescript
POST /api/emails/bulk-categorize   // Bulk update categories
POST /api/emails/bulk-link          // Bulk link to project
POST /api/emails/bulk-archive       // Bulk archive
```

---

## PHASE 2: AI & ATTACHMENTS (NEXT WEEK)

### Priority 4: AI Suggestions Review Dashboard
**Solution:** `/admin/ai-suggestions` page

**Features:**
- View AI-generated action items from `ai_suggestions_queue`
- Filter by type/project/date
- Approve/dismiss
- Track outcomes

### Priority 5: Attachment Browser
**Solution:** `/admin/attachments` page

**Features:**
- Browse all attachments
- Filter by type/date/project
- Preview files
- Reclassify types
- Link to entities

---

## ARCHITECTURE

### Frontend Structure
```
/frontend/src/app/(dashboard)/
  └── admin/
      ├── page.tsx                    # Admin dashboard overview
      ├── validation/
      │   └── page.tsx               # Data validation suggestions
      ├── email-links/
      │   └── page.tsx               # Email link management
      ├── ai-suggestions/
      │   └── page.tsx               # AI suggestions queue
      └── attachments/
          └── page.tsx               # Attachment browser

/frontend/src/components/admin/
  ├── validation-dashboard.tsx       # Main validation UI
  ├── validation-suggestion-card.tsx # Single suggestion view
  ├── email-link-manager.tsx         # Link management UI
  ├── link-evidence-viewer.tsx       # Show linking evidence
  └── bulk-operations-panel.tsx      # Bulk action controls
```

### Backend Structure
```
/backend/api/
  └── admin.py                       # NEW: Admin endpoints
      ├── /validation/*
      ├── /email-links/*
      └── /ai-suggestions/*

/backend/services/
  └── admin_service.py               # NEW: Admin operations
```

---

## NAVIGATION UPDATE

**Add to app-shell.tsx:**
```typescript
{
  label: "Admin",
  href: "/admin",
  icon: Settings,
  badge: pendingSuggestionsCount, // Show notification badge
  children: [
    { label: "Data Validation", href: "/admin/validation" },
    { label: "Email Links", href: "/admin/email-links" },
    { label: "AI Suggestions", href: "/admin/ai-suggestions" },
    { label: "Attachments", href: "/admin/attachments" },
  ]
}
```

---

## SUCCESS METRICS

**Before Admin Interface:**
- ❌ 8 pending suggestions (CLI-only)
- ❌ No link confidence visibility
- ❌ 50% manual intervention time
- ❌ Technical users only

**After Admin Interface:**
- ✅ 0 pending suggestions (reviewed in UI)
- ✅ 100% link transparency
- ✅ <5% manual intervention time
- ✅ Non-technical users enabled

---

## TIMELINE

**Today (Nov 24):**
- [x] Complete audit
- [ ] Build Data Validation Dashboard
- [ ] Add validation API endpoints

**Tomorrow (Nov 25):**
- [ ] Build Email Link Manager
- [ ] Add link management endpoints
- [ ] Test validation workflow

**Nov 26-27:**
- [ ] Add bulk operations to emails page
- [ ] Build AI Suggestions dashboard
- [ ] Testing & polish

---

## CONTEXT PRESERVATION

**Why This Matters:**
User is frustrated with having to repeatedly explain context because:
1. CLI scripts require technical knowledge
2. No UI to see what AI has done
3. No visibility into data quality issues
4. Manual fixes require database knowledge

**This Admin Interface Will:**
1. Surface all AI decisions for human review
2. Show evidence/reasoning for every suggestion
3. Enable one-click approve/deny
4. Track all changes with audit trail
5. Let non-technical users manage data
6. Reduce "tell Claude the context again" cycles

---

## NEXT: START BUILDING

Starting with Priority 1: Data Validation Dashboard
