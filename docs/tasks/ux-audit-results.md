# UX Audit Results

**Audited By:** UX Architect Agent
**Date:** 2025-11-28
**Scope:** All dashboard pages, admin pages, design system

---

## Executive Summary

The current UI has **functional foundations** but suffers from **significant inconsistency** across pages. Each page appears to have been built independently, with different styling approaches, color palettes, and component patterns.

**Priority Action:** Frontend builders must standardize all pages using the updated `design-system.ts` tokens before adding any new features.

---

## Audit Table

| Page | Typography | Colors | States | Issues |
|------|------------|--------|--------|--------|
| `/` Dashboard | Partial | Mixed | Partial | Uses ds.* + inline |
| `/tracker` Proposals | Good | Mixed | Good | Gradient cards violate B&W rule |
| `/projects` Active | Mixed | Mixed | Basic | Manual classes + ds.* mixing |
| `/finance` | Basic | Good | Basic | Inline styling, no design system |
| `/suggestions` | Mixed | Good | Good | Good structure, inconsistent cards |
| `/admin/validation` | Basic | Good | Basic | No design system usage |
| `/admin/intelligence` | Basic | Good | Basic | No design system usage |

---

## Critical Issues by Category

### 1. Color Inconsistencies (HIGH PRIORITY)

**Problem:** Multiple pages use different color approaches. The "80% grayscale + 20% purposeful color" rule is not followed.

| Page | Issue | Fix |
|------|-------|-----|
| `globals.css` | Primary color is purple (`251 77% 53%`) not teal | Update CSS variables to use teal |
| `/` Dashboard | Uses `bg-blue-600` for buttons | Use `ds.buttons.primary` (teal) |
| `/tracker` | Hero card uses indigo-purple gradient | Replace with grayscale card + teal accent |
| `/finance` | Inline `colorClasses` object | Use `ds.status.*` tokens |
| All admin pages | Basic gray with colored borders | Use `ds.badges.*` for status |

**Files to Update:**
- `frontend/src/app/globals.css:12-13` - Change primary to teal HSL
- `frontend/src/app/(dashboard)/page.tsx:52-58` - Replace blue button
- `frontend/src/app/(dashboard)/tracker/page.tsx:258-286` - Replace gradient cards
- `frontend/src/app/(dashboard)/finance/page.tsx:123-128` - Use design system colors

### 2. Typography Inconsistencies (MEDIUM PRIORITY)

**Problem:** Pages mix manual Tailwind classes with design system tokens.

| Page | Good | Bad |
|------|------|-----|
| Dashboard | Uses `ds.typography.*` | N/A |
| Projects | N/A | Manual `text-3xl font-bold`, `text-lg text-slate-600` |
| Finance | N/A | All inline: `text-3xl font-bold`, `text-muted-foreground` |
| Admin pages | N/A | All inline: `text-2xl font-bold`, `text-gray-600` |

**Fix:** Replace all manual typography classes with `ds.typography.*` tokens.

### 3. Card Styling Inconsistencies (MEDIUM PRIORITY)

**Problem:** Different border-radius, padding, and shadow patterns across pages.

| Page | Current | Should Be |
|------|---------|-----------|
| Dashboard | `ds.borderRadius.card` | Keep |
| Projects | `rounded-3xl` (24px) | `ds.cards.default` (12px) |
| Finance | `rounded-lg` (8px) | `ds.cards.default` (12px) |
| Suggestions | `border hover:border-slate-300` | `ds.cards.interactive` |
| Admin validation | `rounded-lg p-6 bg-white shadow-sm` | `ds.cards.default` |

### 4. Loading State Inconsistencies (HIGH PRIORITY)

**Problem:** Mixed approaches - spinners, text, and skeleton loaders.

| Page | Current | Should Be |
|------|---------|-----------|
| Dashboard KPIs | "Loading..." text | Skeleton with `animate-pulse` |
| Proposals | Skeleton components | Keep (correct) |
| Projects | "Loading..." text | Skeleton |
| Suggestions | `Loader2` spinner | Skeleton |
| Admin pages | "Loading..." text | Skeleton |

**Rule:** NEVER use spinners. ALWAYS use skeleton loaders matching content shape.

### 5. Empty State Inconsistencies (MEDIUM PRIORITY)

**Problem:** Boring, unhelpful empty states. Missing Bensley personality.

| Page | Current | Should Be |
|------|---------|-----------|
| Proposals | Icon + "No proposals found" + action | Good structure, add Bensley copy |
| Projects | "No active projects found" (text only) | Add icon + Bensley copy + action |
| Suggestions | Icon + "No pending suggestions" | Use `bensleyVoice.emptyStates.suggestions` |
| Admin pages | "No {items} found" (text only) | Add icon + Bensley copy + action |

### 6. Button Styling Inconsistencies (MEDIUM PRIORITY)

**Problem:** Different button colors and styles across pages.

| Location | Current | Should Be |
|----------|---------|-----------|
| Dashboard | `bg-blue-600` | `ds.buttons.primary` (teal) |
| Finance | Various outlines | `ds.buttons.*` variants |
| Suggestions | `bg-emerald-600` approve button | `ds.buttons.primary` |
| Admin pages | `bg-green-600` approve, red borders | `ds.buttons.*` variants |

### 7. Status Badge Inconsistencies (HIGH PRIORITY)

**Problem:** Multiple definitions of status colors across different files.

| File | Pattern | Issue |
|------|---------|-------|
| `tracker/page.tsx` | `STATUS_COLORS` object | Custom colors |
| `projects/page.tsx` | `StatusBadge` component | Different colors |
| `suggestions/page.tsx` | `getConfidenceColor()` | Inline function |
| Admin pages | Inline conditional classes | No consistency |

**Fix:** All status indicators must use `ds.badges.*` or `ds.status.*` tokens.

---

## Page-by-Page Fix List

### Dashboard (`/`)

**File:** `frontend/src/app/(dashboard)/page.tsx`

- [ ] Line 52-58: Replace `bg-blue-600` with `ds.buttons.primary`
- [ ] Update KPI loading states to use skeleton loaders
- [ ] Verify all cards use `ds.cards.*` tokens

### Proposal Tracker (`/tracker`)

**File:** `frontend/src/app/(dashboard)/tracker/page.tsx`

- [ ] Lines 258-286: Remove gradient backgrounds from metric cards
- [ ] Replace with `ds.cards.default` + subtle status-colored borders
- [ ] Line 52-67: Move `STATUS_COLORS` to design system or use `ds.badges.*`
- [ ] Line 63-67: Move `getActivityColor` to design system (already added)

### Active Projects (`/projects`) ✅ COMPLETED

**File:** `frontend/src/app/(dashboard)/projects/page.tsx`

- [x] Line 122: Replace `bg-gradient-to-b` with solid `bg-slate-50`
- [x] Line 128: Replace manual typography with `ds.typography.pageTitle`
- [x] Line 158: Replace `rounded-3xl` with `ds.cards.default`
- [x] Update all inline typography classes
- [x] Replace loading text with skeleton loaders
- [x] Add Bensley voice to empty states

**Also completed:**
- [x] `frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx` - Detail page
- [x] `frontend/src/app/(dashboard)/projects/[projectCode]/emails/page.tsx` - Emails page

### Finance (`/finance`)

**File:** `frontend/src/app/(dashboard)/finance/page.tsx`

- [ ] Import and use design system tokens
- [ ] Replace all inline color definitions with `ds.status.*`
- [ ] Replace `rounded-lg` cards with `ds.cards.default`
- [ ] Update typography to use `ds.typography.*`
- [ ] Add skeleton loaders

### Suggestions (`/suggestions`)

**File:** `frontend/src/app/(dashboard)/suggestions/page.tsx`

- [ ] Line 122: Replace `bg-gradient-to-b` with solid color
- [ ] Line 210-216: Replace `getConfidenceColor` with design system helper
- [ ] Replace `Loader2` spinner with skeleton loader
- [ ] Use `bensleyVoice.emptyStates.suggestions` for empty state

### Admin Validation (`/admin/validation`)

**File:** `frontend/src/app/(dashboard)/admin/validation/page.tsx`

- [ ] Import design system tokens
- [ ] Replace all inline styling with `ds.*` tokens
- [ ] Add skeleton loaders
- [ ] Add Bensley voice empty states
- [ ] Standardize button colors

### Admin Intelligence (`/admin/intelligence`)

**File:** `frontend/src/app/(dashboard)/admin/intelligence/page.tsx`

- [ ] Import design system tokens
- [ ] Replace all inline styling with `ds.*` tokens
- [ ] Add skeleton loaders
- [ ] Add Bensley voice empty states
- [ ] Standardize button colors

---

## globals.css Fix Required

**File:** `frontend/src/app/globals.css`

Current primary color is purple:
```css
--primary: 251 77% 53%;
```

Should be teal:
```css
--primary: 173 80% 40%; /* teal-600 equivalent */
--primary-foreground: 0 0% 100%;
```

---

## Priority Order for Frontend Builders

1. **P0 (This Sprint):**
   - Update `globals.css` primary color to teal
   - Replace all gradient cards with grayscale
   - Standardize status badges across all pages
   - Replace spinners with skeleton loaders

2. **P1 (Next Sprint):**
   - Migrate all typography to `ds.typography.*`
   - Migrate all cards to `ds.cards.*`
   - Add Bensley voice to all empty/loading states

3. **P2 (Polish):**
   - Unify all admin pages with consistent layout
   - Add missing component states (error, partial)
   - Remove all inline color definitions

---

## Verification Checklist

After fixes are applied, verify:

- [ ] All pages use `ds.typography.*` for text
- [ ] All cards use `ds.cards.*` for styling
- [ ] All tables use `ds.tables.*` for styling
- [ ] All buttons use `ds.buttons.*` variants
- [ ] All status indicators use `ds.badges.*`
- [ ] All loading states use skeleton (no spinners)
- [ ] All empty states have icon + Bensley copy + action
- [ ] No decorative gradients remain
- [ ] Primary action color is teal throughout
- [ ] Charts use `chartColors` consistently

---

**Next Step:** Frontend builders should pick up their respective task packs and use this audit + the design system guide to standardize their pages.

---

## Handoff Notes

### Frontend Builder 2 - Projects (Agent 3) ✅

**Completed By:** Frontend Builder 2 Agent
**Date:** 2025-11-28

#### Files Changed

1. **`frontend/src/app/globals.css`**
   - Verified primary color is teal (168 76% 36%)
   - Updated sidebar-primary and sidebar-ring to teal (from purple)

2. **`frontend/src/app/(dashboard)/projects/page.tsx`**
   - Added `ds` and `bensleyVoice` imports
   - Removed gradient background (`bg-gradient-to-b` → `bg-slate-50`)
   - Fixed page title to use `ds.typography.pageTitle`
   - Fixed all cards from `rounded-3xl` to `ds.cards.default`
   - Fixed table header to use `ds.tables.*` tokens
   - Added skeleton loader for loading state (5 rows)
   - Added Bensley voice empty state with `FolderOpen` icon
   - Fixed `StatusBadge` component to use `ds.badges.*`

3. **`frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx`**
   - Added `ds` and `bensleyVoice` imports
   - Removed gradient background
   - Fixed error state card styling
   - Fixed page header typography
   - Added skeleton loader for loading state
   - Fixed section headers to use `ds.typography.sectionHeader`
   - Fixed all cards from `rounded-3xl` to `ds.cards.default`
   - Fixed `FinancialCard` component to use design system
   - Fixed `InvoicesByDiscipline` card styling
   - Added Bensley voice empty state for invoices

4. **`frontend/src/app/(dashboard)/projects/[projectCode]/emails/page.tsx`**
   - Added `ds` and `bensleyVoice` imports
   - Fixed background to use `bg-slate-50`
   - Added skeleton loaders for loading state
   - Fixed error state with design system styling
   - Fixed page header typography
   - Fixed stats cards to use `ds.cards.default`
   - Added Bensley voice empty state

#### What Works
- ✅ All projects pages use design system tokens
- ✅ No more `rounded-3xl` (all cards use `rounded-xl`)
- ✅ Typography is consistent using `ds.typography.*`
- ✅ Status badges use `ds.badges.*`
- ✅ Loading states use skeleton loaders (no spinners)
- ✅ Empty states have icon + Bensley copy
- ✅ No decorative gradients remain
- ✅ Build passes with no errors

#### Verification
```bash
cd frontend && npm run build
# ✓ Compiled successfully
```

#### Outstanding Items (Not in scope)
- Progress bar gradients kept (functional, not decorative)
- Some inline status colors in invoice phase headers kept for UX clarity
- Table number alignment not changed (already right-aligned)
