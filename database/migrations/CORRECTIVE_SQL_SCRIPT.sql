-- ============================================================================
-- CORRECTIVE SQL SCRIPT: Update Database to Match PDF
-- Date: November 14, 2025
-- Source: Project Status as of 10 Nov 25 (Updated).pdf
-- ============================================================================

-- WARNING: This script will modify the bensley_master.db database
-- BACKUP THE DATABASE BEFORE RUNNING THIS SCRIPT

-- ============================================================================
-- PART 1: UPDATE MISMATCHED PROJECTS (PDF > DB)
-- These projects show higher totals in PDF than database
-- ============================================================================

BEGIN TRANSACTION;

-- 1. 19 BK-018 - Villa Project in Ahmedabad, India
--    PDF: $1,900,000 (LA: 475k + Arch: 665k + ID: 760k)
--    DB:  $1,140,000
--    Difference: +$760,000
UPDATE projects
SET total_fee_usd = 1900000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee corrected from $1,140,000 to $1,900,000 per Nov 2025 status report. Includes Landscape ($475k), Architectural ($665k), and Interior Design ($760k) disciplines.'
WHERE project_code = '19 BK-018';

-- 2. 22 BK-013 - Tel Aviv High Rise Project in Israel
--    PDF: $4,155,000 (LA Phase 1: 400k + ID Phase 1: 2,600k + Monthly DD/CD: 1,155k)
--    DB:  $3,000,000
--    Difference: +$1,155,000
UPDATE projects
SET total_fee_usd = 4155000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee corrected from $3,000,000 to $4,155,000 per Nov 2025 status report. Includes Phase 1 work ($3M) plus additional Design Development and Construction Documents monthly fees ($1,155k for 10 months @ $115,500/month).'
WHERE project_code = '22 BK-013';

-- 3. 22 BK-095 - Wynn Al Marjan Island Project
--    PDF: $3,775,000 (Indian Brasserie: 831k + Modern Med: 831k + Day Club: 1,663k + Night Club: 450k)
--    DB:  $1,662,500
--    Difference: +$2,112,500
--    Note: This excludes 25 BK-039 Additional Service ($250k) which is a separate project code
UPDATE projects
SET total_fee_usd = 3775000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee corrected from $1,662,500 to $3,775,000 per Nov 2025 status report. Includes Indian Brasserie #473 ($831,250), Modern Mediterranean #477 ($831,250), Day Club #650 ($1,662,500), and Night Club ($450,000). Note: Additional Service Design Fee ($250k) tracked separately as 25 BK-039.'
WHERE project_code = '22 BK-095';

-- 4. 25 BK-039 - Wynn Al Marjan Island Project - Additional Service Design Fee
--    PDF: $250,000
--    DB:  $0 or NULL
--    Difference: +$250,000
UPDATE projects
SET total_fee_usd = 250000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee set to $250,000 per Nov 2025 status report. This is an additional service design fee for the Wynn Al Marjan Island Project, tracked separately from 22 BK-095.'
WHERE project_code = '25 BK-039';

-- 5. 23 BK-028 - Proscenium Penthouse in Manila, Philippines
--    PDF: $1,797,520 (Main project: 1,400k + Mural: 397,520)
--    DB:  $1,400,000
--    Difference: +$397,520
UPDATE projects
SET total_fee_usd = 1797520.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee corrected from $1,400,000 to $1,797,520 per Nov 2025 status report. Includes Interior Design ($1,400,000) plus Mural work for 60th & 62nd floors ($397,520).'
WHERE project_code = '23 BK-028';

-- 6. 23 BK-093 - 25 Downtown Mumbai, India (Art Deco Residential Project)
--    PDF: $3,250,000 (LA: 1M + ID: 1.5M + Redesign: 750k)
--    DB:  $1,000,000
--    Difference: +$2,250,000
UPDATE projects
SET total_fee_usd = 3250000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee corrected from $1,000,000 to $3,250,000 per Nov 2025 status report. Includes Landscape Architectural ($1,000,000), Interior Design ($1,500,000), and Redesign of Design Development Drawing ($750,000).'
WHERE project_code = '23 BK-093';

-- 7. 23 BK-050 - Ultra Luxury Beach Resort Hotel and Residence, Bodrum, Turkey
--    PDF: $4,650,000 (Main project: 4,370k + Additional payments: 280k)
--    DB:  $4,370,000
--    Difference: +$280,000
UPDATE projects
SET total_fee_usd = 4650000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee corrected from $4,370,000 to $4,650,000 per Nov 2025 status report. Includes main project phases ($4,370,000) plus additional payments ($280,000).'
WHERE project_code = '23 BK-050';

-- 8. 24 BK-018 - Luang Prabang Heritage Arcade and Hotel, Laos
--    PDF: $1,450,000 (LA: 360k + Arch: 510k + ID: 580k)
--    DB:  $225,000
--    Difference: +$1,225,000
UPDATE projects
SET total_fee_usd = 1450000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee corrected from $225,000 to $1,450,000 per Nov 2025 status report. Includes Landscape Architectural ($360,000), Architectural ($510,000), and Interior Design ($580,000) disciplines.'
WHERE project_code = '24 BK-018';

-- 9. 25 BK-040 - The Ritz Carlton Reserve, Nusa Dua, Bali - Branding Consultancy Service
--    PDF: $125,000
--    DB:  $0 or NULL
--    Difference: +$125,000
UPDATE projects
SET total_fee_usd = 125000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee set to $125,000 per Nov 2025 status report. This is for Branding Consultancy Service (5 steps: Market Analysis, Positioning, Experience Blueprint, Collateral, and Brand Consultancy), tracked separately from main project 25 BK-033.'
WHERE project_code = '25 BK-040';

COMMIT;

-- ============================================================================
-- PART 2: INVESTIGATE MISMATCHED PROJECTS (DB > PDF)
-- These projects show HIGHER totals in database than PDF
-- DO NOT RUN THESE UPDATES WITHOUT MANUAL VERIFICATION
-- ============================================================================

-- WARNING: These updates are commented out for safety
-- Investigate WHY the database shows higher amounts before making changes

-- 1. 20 BK-047 - Audley Square House-Communal Spa
--    PDF: $148,000 (showing only Nov-Dec 2025 installments: 5 months @ $8k + future 9 months @ $12k)
--    DB:  $834,078
--    Difference: -$686,078 (DB HIGHER)
--    INVESTIGATION NEEDED: Is DB showing full contract history? Is PDF showing only remaining payments?
--
-- Potential explanation: The PDF may be showing only the current renewal period
-- The database may contain the full historical contract value
-- DO NOT UPDATE until verified with finance/contracts team

/*
UPDATE projects
SET total_fee_usd = 148000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee changed from $834,078 to $148,000 - REQUIRES VERIFICATION'
WHERE project_code = '20 BK-047';
*/

-- 2. 24 BK-021 - Capella Hotel and Resort, Ubud Bali (Extension of Capella Ubud)
--    PDF: $345,000
--    DB:  $750,000
--    Difference: -$405,000 (DB HIGHER)
--    INVESTIGATION NEEDED: Is this showing the extension only? Is there a main project code?
--
-- Potential explanation: Database may contain full project value, PDF may show extension only
-- There may be separate project codes for original vs extension work
-- DO NOT UPDATE until verified

/*
UPDATE projects
SET total_fee_usd = 345000.00,
    updated_at = CURRENT_TIMESTAMP,
    notes = COALESCE(notes || ' | ', '') || 'Updated 2025-11-14: Total fee changed from $750,000 to $345,000 - REQUIRES VERIFICATION'
WHERE project_code = '24 BK-021';
*/

-- ============================================================================
-- PART 3: ADD MISSING PROJECTS
-- These projects appear in PDF but not in database
-- ============================================================================

-- NOTE: These INSERT statements are incomplete - need to add client_id and other required fields
-- Get client information first, then add full project details

-- Projects to add:
-- 1. 24 BK-033: Renovation Work for Three of Four Seasons Properties ($1,500,000)
-- 2. 24 BK-058: Luxury Resort Development at Fenfushi Island, Raa Atoll, Maldives ($2,990,000)
-- 3. 25 BK-015: Shinta Mani Mustang, Nepal (Extension Work) - Hotels #1 and #2 ($300,000)
-- 4. 25 BK-017: TARC's Luxury Branded Residence Project in New Delhi ($3,000,000)

-- Template for adding (fill in client_id and other fields):
/*
INSERT INTO projects (
    project_code,
    project_title,
    total_fee_usd,
    status,
    notes,
    date_created
) VALUES (
    '24 BK-033',
    'Renovation Work for Three of Four Seasons Properties',
    1500000.00,
    'Active',
    'Added 2025-11-14 from Nov 2025 status report. Monthly fee contract: THB 48,000,000 or USD 1,500,000. Mobilization: THB 8,400,000, Monthly: THB 1,100,000 for 36 months.',
    '2025-04-01'
);
*/

-- ============================================================================
-- PART 4: VERIFICATION QUERIES
-- Run these to verify the updates
-- ============================================================================

-- Check updated projects
SELECT
    project_code,
    project_title,
    total_fee_usd,
    updated_at,
    notes
FROM projects
WHERE project_code IN (
    '19 BK-018',
    '22 BK-013',
    '22 BK-095',
    '25 BK-039',
    '23 BK-028',
    '23 BK-093',
    '23 BK-050',
    '24 BK-018',
    '25 BK-040'
)
ORDER BY project_code;

-- Calculate new total after updates
SELECT
    COUNT(*) as project_count,
    SUM(total_fee_usd) as total_fees
FROM projects
WHERE project_code IN (
    -- All 30 extracted PDF projects
    '20 BK-047', '19 BK-018', '22 BK-013', '22 BK-046', '22 BK-095',
    '25 BK-039', '23 BK-009', '23 BK-028', '23 BK-088', '25 BK-030',
    '25 BK-018', '23 BK-071', '23 BK-096', '23 BK-067', '23 BK-080',
    '23 BK-093', '23 BK-089', '23 BK-050', '24 BK-021', '24 BK-018',
    '24 BK-029', '19 BK-052', '24 BK-077', '24 BK-074', '25 BK-015',
    '25 BK-017', '25 BK-033', '25 BK-040'
    -- Note: '24 BK-033' and '24 BK-058' not in database yet
);

-- ============================================================================
-- SUMMARY OF CHANGES
-- ============================================================================

/*
EXECUTED UPDATES (Part 1):
- 19 BK-018: $1,140,000 → $1,900,000 (+$760,000)
- 22 BK-013: $3,000,000 → $4,155,000 (+$1,155,000)
- 22 BK-095: $1,662,500 → $3,775,000 (+$2,112,500)
- 25 BK-039: $0 → $250,000 (+$250,000)
- 23 BK-028: $1,400,000 → $1,797,520 (+$397,520)
- 23 BK-093: $1,000,000 → $3,250,000 (+$2,250,000)
- 23 BK-050: $4,370,000 → $4,650,000 (+$280,000)
- 24 BK-018: $225,000 → $1,450,000 (+$1,225,000)
- 25 BK-040: $0 → $125,000 (+$125,000)

TOTAL INCREASE: +$8,555,020

PENDING INVESTIGATION (Part 2):
- 20 BK-047: DB=$834,078 vs PDF=$148,000 (-$686,078) - DO NOT UPDATE
- 24 BK-021: DB=$750,000 vs PDF=$345,000 (-$405,000) - DO NOT UPDATE

TO BE ADDED (Part 3):
- 24 BK-033: $1,500,000 (Four Seasons renovation)
- 24 BK-058: $2,990,000 (Fenfushi Maldives)
- 25 BK-015: $300,000 (Shinta Mani Mustang)
- 25 BK-017: $3,000,000 (TARC Delhi - different from 24 BK-017)

STILL MISSING: ~$16.3M in projects not yet extracted from PDF
*/

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================
