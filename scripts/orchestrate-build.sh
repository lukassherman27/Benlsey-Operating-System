#!/bin/bash

# =============================================================================
# MULTI-AGENT BUILD ORCHESTRATOR
# =============================================================================
# Usage: ./scripts/orchestrate-build.sh <feature> <issue_number>
# Example: ./scripts/orchestrate-build.sh proposals 356
#
# This script:
# 1. Creates audit tasks for multiple agents
# 2. Runs them in parallel
# 3. Collects findings to the GitHub issue
# 4. Waits for human approval
# 5. Runs the build agent
# =============================================================================

set -e

FEATURE="${1:-proposals}"
ISSUE="${2:-356}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=========================================="
echo "🚀 MULTI-AGENT BUILD ORCHESTRATOR"
echo "=========================================="
echo "Feature: $FEATURE"
echo "Issue: #$ISSUE"
echo "Repo: $REPO_ROOT"
echo ""

# -----------------------------------------------------------------------------
# AUDIT PROMPTS
# -----------------------------------------------------------------------------

UX_AUDIT_PROMPT="You are a UX Auditor for the BDS Operations Platform.

Read these files:
- CLAUDE.md for system context
- AGENTS.md for rules

Your task: Audit the $FEATURE feature from a USER EXPERIENCE perspective.

Check:
1. frontend/src/app/(dashboard)/tracker/page.tsx (or relevant page)
2. What can the user do?
3. What's confusing?
4. What's missing?
5. What quick wins would help?

Output your findings in this EXACT format (no other text):

## UX Audit Findings

### What Works Well:
- [list items]

### UX Issues Found:
- [list items]

### Missing Features:
- [list items]

### Quick Wins:
- [list items]

### Recommendations:
- [list items]"

CODE_AUDIT_PROMPT="You are a Code Quality Auditor for the BDS Operations Platform.

Read these files:
- CLAUDE.md for system context
- AGENTS.md for rules

Your task: Audit the $FEATURE feature for CODE QUALITY and SECURITY.

Check:
1. backend/api/routers/proposals.py (or relevant router)
2. Related services in backend/services/
3. Frontend components

Audit for:
- Authentication/authorization gaps
- SQL injection risks
- Error handling
- Performance (N+1 queries)
- Dead code
- Missing validation
- TypeScript errors

Output your findings in this EXACT format (no other text):

## Code Audit Findings

### Security Issues:
- [list or 'None found']

### Bugs Found:
- [list or 'None found']

### Performance Concerns:
- [list or 'None found']

### Code Quality Issues:
- [list items]

### Technical Debt:
- [list items]

### Recommendations:
- [list items]"

DATA_AUDIT_PROMPT="You are a Data Auditor for the BDS Operations Platform.

You have MCP access to the database. Use mcp__bensley-db__read_query to check data.

Your task: Audit the $FEATURE data quality and completeness.

Check:
1. How many records exist?
2. Data completeness (null fields, missing relationships)
3. Data quality issues
4. Orphaned records

Output your findings in this EXACT format (no other text):

## Data Audit Findings

### Record Counts:
- [entity]: [count]

### Data Quality Issues:
- [list items]

### Missing Data:
- [list items]

### Recommendations:
- [list items]"

API_AUDIT_PROMPT="You are an API Auditor for the BDS Operations Platform.

Your task: Audit the $FEATURE API endpoints.

Check backend/api/routers/ for relevant files.

For each endpoint, verify:
1. Does it have authentication?
2. Does it validate input?
3. Does it handle errors?
4. Is the response format consistent?
5. Is it documented?

Output your findings in this EXACT format (no other text):

## API Audit Findings

### Endpoints Reviewed:
- [list endpoints]

### Authentication Gaps:
- [list or 'None']

### Validation Issues:
- [list or 'None']

### Error Handling Issues:
- [list or 'None']

### Missing Endpoints:
- [list or 'None']

### Recommendations:
- [list items]"

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

run_audit() {
    local audit_name="$1"
    local prompt="$2"
    local output_file="$REPO_ROOT/.claude/audits/${FEATURE}_${audit_name}.md"

    echo "🔍 Running $audit_name audit..."

    # Run Claude in headless mode
    cd "$REPO_ROOT"
    claude -p "$prompt" --output-format text > "$output_file" 2>/dev/null || {
        echo "⚠️  $audit_name audit failed, continuing..."
        echo "Audit failed - check manually" > "$output_file"
    }

    echo "✅ $audit_name audit complete"
}

post_to_issue() {
    local title="$1"
    local content="$2"

    gh issue comment "$ISSUE" --body "# $title

$content

---
*Posted by orchestrate-build.sh at $(date)*"
}

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

# Create audits directory
mkdir -p "$REPO_ROOT/.claude/audits"

echo ""
echo "📋 STEP 1: Running parallel audits..."
echo "----------------------------------------"

# Run audits in parallel using background processes
run_audit "ux" "$UX_AUDIT_PROMPT" &
PID_UX=$!

run_audit "code" "$CODE_AUDIT_PROMPT" &
PID_CODE=$!

run_audit "data" "$DATA_AUDIT_PROMPT" &
PID_DATA=$!

run_audit "api" "$API_AUDIT_PROMPT" &
PID_API=$!

# Wait for all audits to complete
echo "⏳ Waiting for audits to complete..."
wait $PID_UX $PID_CODE $PID_DATA $PID_API

echo ""
echo "📤 STEP 2: Posting findings to Issue #$ISSUE..."
echo "----------------------------------------"

# Combine and post findings
COMBINED_FINDINGS=""

for audit_type in ux code data api; do
    file="$REPO_ROOT/.claude/audits/${FEATURE}_${audit_type}.md"
    if [ -f "$file" ]; then
        COMBINED_FINDINGS+="
---

$(cat "$file")
"
    fi
done

# Post combined findings
gh issue comment "$ISSUE" --body "# 🔍 Automated Audit Results

**Feature:** $FEATURE
**Audits Run:** UX, Code, Data, API
**Timestamp:** $(date)

$COMBINED_FINDINGS

---

## Next Steps
1. Review findings above
2. Reply with 'APPROVED' to proceed with build
3. Or add comments for adjustments needed
"

echo ""
echo "=========================================="
echo "✅ AUDITS COMPLETE"
echo "=========================================="
echo ""
echo "Findings posted to: https://github.com/lukassherman27/Benlsey-Operating-System/issues/$ISSUE"
echo ""
echo "Next steps:"
echo "1. Review the audit findings on the issue"
echo "2. Run: ./scripts/orchestrate-build.sh build $FEATURE $ISSUE"
echo "   (after you're satisfied with the audits)"
echo ""
