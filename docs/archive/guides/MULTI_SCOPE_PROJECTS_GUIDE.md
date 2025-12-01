# Multi-Scope Projects Implementation Guide

## Problem

Some projects have **multiple distinct scopes/areas** within a single contract, each with their own fee breakdowns:

### Examples:

1. **Wynn Marjan (22 BK-095)** - 4 separate scopes:
   - Indian Brasserie at Casino level ($831,250)
   - Modern Mediterranean Restaurant on Casino Level ($831,250)
   - Day Club on B2 Level including Dynamic outdoor Bar/swim up Bar ($1,662,500)
   - Interior Design for Night Club ($450,000)
   - **Each scope has full phase breakdown**: Mobilization, Concept, DD, CD, CA

2. **Art Deco Residential (23 BK-093)** - 2 areas:
   - Sale Center (with phases)
   - Main Tower Block (with phases)

3. **Simpler projects** (Capella Ubud, Mandarin Oriental Bali):
   - Just general Architecture/Landscape/Interior disciplines
   - No scope subdivision needed

4. **Special categories**:
   - Proscenium Manila (23 BK-028): "Artwork" category for mural work

---

## Solution: Add "Scope" Field

### Database Changes

**Migration 027** adds a `scope` column to `project_fee_breakdown` table:

```sql
ALTER TABLE project_fee_breakdown ADD COLUMN scope TEXT;
UPDATE project_fee_breakdown SET scope = 'general' WHERE scope IS NULL;
```

### Breakdown ID Format

**OLD FORMAT:**
```
{project_code}_{discipline}_{phase}
Example: 24-BK-021_landscape_mobilization
```

**NEW FORMAT:**
```
{project_code}_{scope}_{discipline}_{phase}
Example: 22-BK-095_indian-brasserie_landscape_mobilization
```

---

## How to Handle Each Project Type

### Type 1: Multi-Scope Projects (Wynn Marjan)

For projects with distinct areas/scopes, create **separate breakdowns for each scope**:

**Example: Wynn Marjan Indian Brasserie**
- Scope: `indian-brasserie`
- breakdown_id: `22-BK-095_indian-brasserie_landscape_mobilization`
- breakdown_id: `22-BK-095_indian-brasserie_landscape_concept-design`
- breakdown_id: `22-BK-095_indian-brasserie_landscape_design-development`
- ... (and so on for each phase and discipline)

**Wynn Marjan Day Club**
- Scope: `day-club`
- breakdown_id: `22-BK-095_day-club_landscape_mobilization`
- ... (and so on)

This allows invoice I22-156 to be linked to multiple breakdowns:
- Entry 1: Linked to `22-BK-095_indian-brasserie_landscape_mobilization`
- Entry 2: Linked to `22-BK-095_day-club_landscape_mobilization`
- Entry 3: Linked to `22-BK-095_mediterranean-restaurant_landscape_mobilization`

### Type 2: Simple Projects (Capella Ubud, Mandarin Bali)

For projects with just general disciplines, use scope = `general`:

**Example: Capella Ubud**
- Scope: `general`
- breakdown_id: `24-BK-021_general_landscape_mobilization`
- breakdown_id: `24-BK-021_general_architecture_mobilization`
- breakdown_id: `24-BK-021_general_interior_mobilization`

### Type 3: Area-Based Projects (Art Deco)

For projects split by building area, use descriptive scope names:

**Example: Art Deco Residential**
- Scope 1: `sale-center`
  - `23-BK-093_sale-center_architecture_concept-design`
  - `23-BK-093_sale-center_architecture_design-development`

- Scope 2: `main-tower-block`
  - `23-BK-093_main-tower-block_architecture_concept-design`
  - `23-BK-093_main-tower-block_architecture_design-development`

### Type 4: Special Categories (Artwork)

For unique disciplines like artwork, treat as regular discipline:

**Example: Proscenium Manila**
- Scope: `general`
- Discipline: `artwork`
- breakdown_id: `23-BK-028_general_artwork_mobilization`

---

## Implementation Steps

### Step 1: Run Migration
```bash
sqlite3 database/bensley_master.db < database/migrations/027_add_scope_to_breakdowns.sql
```

### Step 2: Regenerate All Breakdown IDs
```bash
python3 fix_breakdown_ids_with_scope.py
```

This script:
- Updates all existing `breakdown_id` values to include scope
- Updates all `invoice.breakdown_id` references to match
- Defaults to `scope = 'general'` for existing records

### Step 3: Create Multi-Scope Breakdowns

For projects like Wynn Marjan, manually create the separate scope breakdowns:

```bash
python3 create_wynn_marjan_scopes.py
```

(Script to be created - will insert 4 sets of breakdowns for the 4 scopes)

### Step 4: Link Invoices to Correct Scopes

Update the 67 unlinked invoices to link to correct breakdown_ids:

**For Wynn Marjan (20 invoices):**
- Manually parse descriptions to extract scope information
- Create separate invoice entries for each scope
- Link each to correct `breakdown_id`

**For Installments (19 invoices):**
- Create special "Installment" breakdown category
- Link all installment invoices to this breakdown

---

## Frontend Changes Needed

### 1. Add Scope Selector (Step 2 - Phase Breakdown)

```tsx
<div className="col-span-4">
  <Label>Scope/Area (Optional)</Label>
  <Input
    value={currentPhase.scope || "general"}
    onChange={(e) => setCurrentPhase({ ...currentPhase, scope: e.target.value })}
    placeholder="e.g., 'indian-brasserie', 'sale-center', or leave as 'general'"
  />
  <p className="text-xs text-gray-500 mt-1">
    For multi-scope projects, specify the area/scope this fee breakdown applies to
  </p>
</div>
```

### 2. Update Phase Interface

```tsx
interface PhaseEntry {
  id: string;
  scope: string;          // NEW: 'general', 'indian-brasserie', etc.
  discipline: string;
  phase: string;
  phase_fee_usd: number;
  percentage_of_total: number;
}
```

### 3. Update breakdown_id Generation

```tsx
const generateBreakdownId = (projectCode: string, scope: string, discipline: string, phase: string) => {
  const cleanProject = projectCode.replace(/\s+/g, '-');
  const cleanScope = slugify(scope || 'general');
  const cleanDiscipline = slugify(discipline);
  const cleanPhase = slugify(phase);

  return `${cleanProject}_${cleanScope}_${cleanDiscipline}_${cleanPhase}`;
};
```

### 4. Group Phases by Scope in Display

```tsx
// Group phases by scope for better visualization
const phasesByScope = phases.reduce((acc, phase) => {
  const scope = phase.scope || 'general';
  if (!acc[scope]) acc[scope] = [];
  acc[scope].push(phase);
  return acc;
}, {} as Record<string, PhaseEntry[]>);

// Display grouped by scope
{Object.entries(phasesByScope).map(([scope, scopePhases]) => (
  <div key={scope} className="mb-6">
    <h3 className="font-semibold text-lg mb-3 capitalize">
      {scope === 'general' ? 'General Scope' : scope.replace(/-/g, ' ')}
    </h3>
    <div className="space-y-2">
      {scopePhases.map(phase => (
        <PhaseCard key={phase.id} phase={phase} />
      ))}
    </div>
  </div>
))}
```

---

## Backend API Changes

### Update CreatePhaseFeeRequest

```python
class CreatePhaseFeeRequest(BaseModel):
    """Request to create a new phase fee breakdown"""
    project_code: str
    scope: Optional[str] = Field(default="general", description="Scope/area this breakdown applies to")
    discipline: str
    phase: str
    phase_fee_usd: float
    percentage_of_total: Optional[float] = None
```

### Update Phase Fee Creation

```python
@app.post("/api/phase-fees")
async def create_phase_fee(request: CreatePhaseFeeRequest):
    # Generate breakdown_id with scope
    breakdown_id = generate_breakdown_id(
        request.project_code,
        request.scope or "general",
        request.discipline,
        request.phase
    )

    cursor.execute("""
        INSERT INTO project_fee_breakdown (
            breakdown_id, project_code, scope, discipline, phase,
            phase_fee_usd, percentage_of_total
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (breakdown_id, request.project_code, request.scope, request.discipline,
          request.phase, request.phase_fee_usd, request.percentage_of_total))
```

---

## Fixing the 67 Unlinked Invoices

### Category 1: Installments (19 invoices)

Create special "Installment" breakdown:

```python
# Create installment breakdown for each project with installment payments
for project_code in ['19 BK-095', '24 BK-012', '24 BK-017', '24 BK-018']:
    breakdown_id = f"{project_code}_general_installment_monthly-payment"
    cursor.execute("""
        INSERT INTO project_fee_breakdown (breakdown_id, project_code, scope, discipline, phase)
        VALUES (?, ?, 'general', 'installment', 'monthly-payment')
    """, (breakdown_id, project_code))

    # Link all installment invoices for this project
    cursor.execute("""
        UPDATE invoices
        SET breakdown_id = ?
        WHERE project_code = ? AND description LIKE '%installment%'
    """, (breakdown_id, project_code))
```

### Category 2: Wynn Marjan (20 invoices)

1. **Create 4 scope breakdowns** (indian-brasserie, mediterranean-restaurant, day-club, night-club)
2. **Manually map invoices** based on Excel data to correct scopes
3. **Split invoices** that cover multiple scopes into separate entries

### Category 3: Artwork Category (2 invoices - Manila)

```python
breakdown_id = "23-BK-028_general_artwork_concept-design"
cursor.execute("""
    INSERT INTO project_fee_breakdown (breakdown_id, project_code, scope, discipline, phase)
    VALUES (?, '23 BK-028', 'general', 'artwork', 'concept-design')
""", (breakdown_id,))

# Link artwork invoices
cursor.execute("""
    UPDATE invoices
    SET breakdown_id = ?
    WHERE project_code = '23 BK-028' AND description LIKE '%artwork%'
""", (breakdown_id,))
```

### Category 4: Other Data Quality Issues (remaining invoices)

Manually review and fix descriptions, then re-run linking script.

---

## Benefits of This Approach

1. **Flexible**: Accommodates both simple and complex project structures
2. **Backward Compatible**: Existing simple projects use `scope = 'general'`
3. **Clear Hierarchy**: Project → Scope → Discipline → Phase
4. **Scalable**: Easy to add more scopes to existing projects
5. **Accurate Tracking**: Each invoice entry links to specific scope/discipline/phase combination

---

## Next Steps

1. ✅ Create migration 027
2. ✅ Create fix_breakdown_ids_with_scope.py script
3. ⏳ Run migration and fix script
4. ⏳ Create script to generate Wynn Marjan 4-scope breakdowns
5. ⏳ Create script to handle installment invoices
6. ⏳ Update frontend to support scope field
7. ⏳ Update backend API with scope parameter
8. ⏳ Manually fix remaining 48 problematic invoices
9. ⏳ Test with all project types

---

## Testing Checklist

- [ ] Simple project (Capella Ubud) - all invoices link correctly with `scope = 'general'`
- [ ] Multi-scope project (Wynn Marjan) - 4 scopes, each with phases, invoices link correctly
- [ ] Area-based project (Art Deco) - 2 areas, phases link correctly
- [ ] Special category (Manila Artwork) - artwork invoices link correctly
- [ ] Installment payments - all link to installment breakdown
- [ ] Frontend scope selector works
- [ ] Can create new multi-scope project
- [ ] Can edit existing multi-scope project
- [ ] All 253 invoices have breakdown_id
