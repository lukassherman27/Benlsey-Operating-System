# Bensley Design System

**Single Source of Truth for UI Consistency**

> **Philosophy:** 80% grayscale foundation + 20% purposeful color accents.
> If you can't explain WHY a color is there, it should be grayscale.

---

## Quick Reference

**Design System File:** `frontend/src/lib/design-system.ts`

```typescript
import { ds, colors, bensleyVoice, getLoadingMessage } from '@/lib/design-system';
```

---

## Color Philosophy

Bill Bensley is a maximalist designer who hates boring interiors. But this is an internal ops tool - it needs to work, not just look pretty.

**The Balance:**
- **75% Clean & Functional** - Black/white bones, clear hierarchy
- **25% Bensley Character** - Playful copy, cheeky moments, personality

### Foundation Colors (80% of UI)

| Name      | Hex       | Usage                           |
|-----------|-----------|--------------------------------|
| Black     | `#0A0A0A` | Primary text, headers          |
| Charcoal  | `#1A1A1A` | Secondary text, body content   |
| Graphite  | `#333333` | Tertiary elements              |
| Silver    | `#666666` | Muted text, captions           |
| Platinum  | `#999999` | Disabled, placeholders         |
| Pearl     | `#E5E5E5` | Borders, dividers              |
| Snow      | `#F5F5F5` | Subtle backgrounds, hover      |
| White     | `#FFFFFF` | Cards, main background         |

### Accent Colors (20% of UI)

**Color = Information.** These ONLY appear when they MEAN something.

| Color   | Hex       | When to Use                        |
|---------|-----------|-----------------------------------|
| Teal    | `#0D9488` | Primary actions, buttons, links    |
| Emerald | `#059669` | Success: Paid, complete, healthy   |
| Amber   | `#D97706` | Warning: Needs attention, 30-60d   |
| Red     | `#DC2626` | Danger: Overdue, critical, error   |
| Blue    | `#2563EB` | Info: Informational, neutral status|

---

## Typography

### Page Structure

```typescript
ds.typography.pageTitle      // Page headers: text-3xl font-bold text-slate-900
ds.typography.sectionHeader  // Sections: text-2xl font-semibold text-slate-900
ds.typography.cardHeader     // Card titles: text-xl font-semibold text-slate-900
```

### Content Text

```typescript
ds.typography.body           // Default: text-base
ds.typography.bodySmall      // Supporting: text-sm text-slate-600
ds.typography.caption        // Captions: text-sm text-slate-500
ds.typography.label          // Labels: text-xs uppercase tracking-wide
```

### Metrics & Numbers

```typescript
ds.typography.metric         // Large numbers: text-2xl font-bold tabular-nums
ds.typography.metricLabel    // Number labels: text-sm font-medium text-slate-500
```

---

## Components

### Cards

```typescript
// Default card
<div className={ds.cards.default}>
  // bg-white border border-slate-200 rounded-xl shadow-sm

// Clickable card
<div className={ds.cards.interactive}>
  // Adds hover states
```

### Tables

```typescript
// Table header row
<thead className={ds.tables.header}>
  // bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500

// Table body
<tbody className={ds.tables.divider}>
  // divide-y divide-slate-100

// Table row
<tr className={ds.tables.row}>
  // hover:bg-slate-50 transition-colors

// Number cells (right-aligned, monospace)
<td className={ds.tables.cellNumber}>
  // text-right font-mono tabular-nums
```

### Buttons

```typescript
// Primary action (Teal)
<button className={ds.buttons.primary}>
  // bg-teal-600 text-white hover:bg-teal-700

// Secondary
<button className={ds.buttons.secondary}>
  // bg-slate-50 text-slate-700 border border-slate-200

// Ghost (minimal)
<button className={ds.buttons.ghost}>
  // text-slate-700 hover:bg-slate-50

// Danger (outlined, not filled)
<button className={ds.buttons.danger}>
  // text-red-600 border border-red-200 hover:bg-red-50
```

### Status Badges

Badges are the **primary place for color** in the UI.

```typescript
ds.badges.default   // Neutral: bg-slate-50 text-slate-700
ds.badges.success   // Paid/Complete: bg-emerald-50 text-emerald-700
ds.badges.warning   // Attention: bg-amber-50 text-amber-700
ds.badges.danger    // Overdue: bg-red-50 text-red-700
ds.badges.info      // Info: bg-blue-50 text-blue-700
```

### Inputs

```typescript
// Default input
<input className={ds.inputs.default} />
  // Focus: ring-2 ring-teal-500

// Error state
<input className={ds.inputs.error} />
  // ring-2 ring-red-500 border-red-500
```

---

## Status Colors (Semantic)

Use `ds.status` for consistent status styling:

```typescript
// Success state
<div className={cn(ds.status.success.bg, ds.status.success.border, ds.status.success.text)}>
  // bg-emerald-50 border-emerald-200 text-emerald-700

// Warning state
<div className={cn(ds.status.warning.bg, ds.status.warning.border, ds.status.warning.text)}>
  // bg-amber-50 border-amber-200 text-amber-700
```

---

## Helper Functions

### Get Aging Color

```typescript
import { getAgingColor } from '@/lib/design-system';

const aging = getAgingColor(45); // days
// Returns: { bg: 'bg-amber-50', text: 'text-amber-700', label: 'Aging' }
```

| Days     | Label    | Color  |
|----------|----------|--------|
| 0-30     | Current  | Slate  |
| 31-60    | Aging    | Amber  |
| 61-90    | Overdue  | Orange |
| 90+      | Critical | Red    |

### Get Activity Color

```typescript
import { getActivityColor } from '@/lib/design-system';

const activity = getActivityColor(10); // days since last activity
// Returns: { bg: 'bg-amber-50', text: 'text-amber-700', label: 'Needs attention' }
```

| Days  | Label           | Color   |
|-------|-----------------|---------|
| 0-7   | Active          | Emerald |
| 8-14  | Needs attention | Amber   |
| 14+   | Stalled         | Red     |

---

## Bensley Voice & Copy

### Where Personality Lives

- Page titles and section headers
- Empty state messages
- Loading messages
- Tooltips and helper text
- Success/error toasts
- 404 and error pages

### Where to Stay Serious

- Data tables (numbers must be scannable)
- Forms (don't confuse users)
- Navigation (people need to find things)
- Critical alerts (don't joke about overdue invoices)

### Empty States

```typescript
import { bensleyVoice } from '@/lib/design-system';

// In a component:
<p>{bensleyVoice.emptyStates.proposals}</p>
// "The pipeline's looking thirsty. Time to make some calls?"
```

| Page        | Message                                                    |
|-------------|------------------------------------------------------------|
| Proposals   | "The pipeline's looking thirsty. Time to make some calls?" |
| Suggestions | "All caught up! The AI is having a tea break."             |
| Emails      | "Every email has a home. Impressive."                      |
| Invoices    | "Nothing overdue. Someone's been doing their job."         |
| Search      | "Couldn't find that. Try different words, or blame the intern." |
| Projects    | "Suspiciously quiet. Is everyone on holiday?"              |

### Loading Messages

```typescript
import { getLoadingMessage } from '@/lib/design-system';

// Rotate randomly:
<p>{getLoadingMessage()}</p>
// "Waking up the elephants..."
// "Consulting the design gods..."
// etc.
```

### Success/Error Toasts

```typescript
// Success
toast.success(bensleyVoice.successMessages.saved);
// "Saved. The cloud remembers everything."

// Error
toast.error(bensleyVoice.errorMessages.network);
// "The internet gremlins are at it again. Check your connection."
```

---

## Chart Colors

All charts must use the same palette:

```typescript
import { chartColors } from '@/lib/design-system';

chartColors.primary   // #3B82F6 - blue-500: Primary metric
chartColors.success   // #22C55E - green-500: Positive/Paid
chartColors.warning   // #F59E0B - amber-500: Warning/Aging
chartColors.danger    // #EF4444 - red-500: Danger/Overdue
chartColors.neutral   // #94A3B8 - slate-400: Neutral/Other
```

---

## State Standards

### Every Component Needs These States

1. **Loading:** Skeleton animation, same shape as content (never spinners)
2. **Empty:** Icon + heading + description + primary action button
3. **Error:** Error message + "Try Again" button
4. **Success:** Brief confirmation (toast, not modal)

### Loading Skeleton Example

```tsx
{isLoading ? (
  <div className="space-y-3">
    {[1, 2, 3].map((i) => (
      <div key={i} className="flex gap-4 animate-pulse">
        <div className="h-12 w-24 bg-slate-200 rounded" />
        <div className="h-12 flex-1 bg-slate-200 rounded" />
      </div>
    ))}
  </div>
) : (
  // ... content
)}
```

### Empty State Example

```tsx
<div className="py-16 text-center">
  <FileText className="mx-auto h-16 w-16 text-slate-300 mb-4" />
  <p className={ds.typography.cardHeader}>
    {bensleyVoice.emptyStates.proposals}
  </p>
  <p className="text-slate-500 mt-2">
    Proposals will appear here once created
  </p>
  <Button className={ds.buttons.primary + " mt-4"}>
    Create Proposal
  </Button>
</div>
```

---

## DO and DON'T

### DO

- Use `ds.typography.*` for all text styling
- Use `ds.status.*` for status-colored elements
- Use `ds.badges.*` for status indicators
- Use `ds.tables.*` for all table styling
- Use skeleton loaders (not spinners)
- Use Bensley voice for empty/loading states
- Keep data tables grayscale (color only in status badges)

### DON'T

- Use color without semantic meaning
- Use gradients for cards or backgrounds
- Use spinners for loading states
- Write boring empty states ("No data found")
- Mix manual Tailwind classes with design system tokens
- Use `rounded-full` for data badges (only decorative)
- Add hover states to cards that aren't clickable

---

## Migration Checklist

When updating a page to use the design system:

- [ ] Import `ds` from `@/lib/design-system`
- [ ] Replace typography classes with `ds.typography.*`
- [ ] Replace card styling with `ds.cards.*`
- [ ] Replace table styling with `ds.tables.*`
- [ ] Replace button styling with `ds.buttons.*`
- [ ] Replace status colors with `ds.badges.*` or `ds.status.*`
- [ ] Replace inline loading text with `getLoadingMessage()`
- [ ] Replace boring empty states with `bensleyVoice.emptyStates.*`
- [ ] Ensure skeleton loaders (not spinners)
- [ ] Remove any decorative gradients
- [ ] Verify color is only used where it has meaning

---

## Files Reference

| File | Purpose |
|------|---------|
| `frontend/src/lib/design-system.ts` | All design tokens |
| `frontend/tailwind.config.ts` | Tailwind customization |
| `frontend/src/app/globals.css` | CSS variables |
| `docs/guides/DESIGN_SYSTEM.md` | This document |

---

**Last Updated:** 2025-11-28
**Owner:** UX Architect Agent
