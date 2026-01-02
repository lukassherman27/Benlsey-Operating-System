#!/bin/bash

# =============================================================================
# 🚀 BUILD FEATURE - Master Orchestrator
# =============================================================================
#
# One command to rule them all. This orchestrates the entire multi-agent
# build process for any feature.
#
# Usage:
#   ./scripts/build-feature.sh <feature_name> [phase]
#
# Examples:
#   ./scripts/build-feature.sh proposals          # Full flow: audit → plan → build
#   ./scripts/build-feature.sh proposals audit    # Just run audits
#   ./scripts/build-feature.sh proposals plan     # Just create plan
#   ./scripts/build-feature.sh proposals build    # Just run build
#
# =============================================================================

set -e

FEATURE="${1:-proposals}"
PHASE="${2:-all}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# -----------------------------------------------------------------------------
# STEP 0: Create or find the issue
# -----------------------------------------------------------------------------

create_or_find_issue() {
    print_header "🎫 ISSUE SETUP"

    # Check if there's an existing open issue for this feature
    EXISTING=$(gh issue list --state open --search "$FEATURE" --json number,title --jq '.[0].number' 2>/dev/null || echo "")

    if [ -n "$EXISTING" ] && [ "$EXISTING" != "null" ]; then
        echo "Found existing issue: #$EXISTING"
        read -p "Use this issue? (y/n): " USE_EXISTING
        if [ "$USE_EXISTING" = "y" ]; then
            ISSUE="$EXISTING"
            print_success "Using Issue #$ISSUE"
            return
        fi
    fi

    # Create new issue
    echo "Creating new issue for $FEATURE..."
    ISSUE=$(gh issue create \
        --title "[BUILD] $FEATURE - Multi-Agent Build" \
        --body "# Multi-Agent Build: $FEATURE

## Status: 🔄 In Progress

## Workflow
- [ ] Audits complete
- [ ] Plan approved
- [ ] Build complete
- [ ] PR merged

## Audit Findings
*Pending...*

## Implementation Plan
*Pending...*

## Build Log
*Pending...*

---
*Created by build-feature.sh*" \
        --label "enhancement" \
        | grep -oE '[0-9]+$')

    print_success "Created Issue #$ISSUE"
}

# -----------------------------------------------------------------------------
# PHASE 1: AUDITS
# -----------------------------------------------------------------------------

run_audits() {
    print_header "🔍 PHASE 1: RUNNING AUDITS"

    mkdir -p "$REPO_ROOT/.claude/audits"

    echo "Running 4 parallel audits..."
    echo "  • UX Audit"
    echo "  • Code Audit"
    echo "  • Data Audit"
    echo "  • API Audit"
    echo ""

    # UX Audit
    (
        claude -p "Audit the $FEATURE feature UX. Check frontend/src/app/(dashboard)/ for relevant pages. What works? What's confusing? What's missing? Output as markdown with headers: What Works, UX Issues, Missing Features, Quick Wins." \
            --output-format text > "$REPO_ROOT/.claude/audits/${FEATURE}_ux.md" 2>/dev/null
    ) &

    # Code Audit
    (
        claude -p "Audit the $FEATURE feature code quality. Check backend/api/routers/ and frontend components. Look for: security issues, bugs, performance problems, dead code. Output as markdown with headers: Security Issues, Bugs, Performance, Code Quality, Recommendations." \
            --output-format text > "$REPO_ROOT/.claude/audits/${FEATURE}_code.md" 2>/dev/null
    ) &

    # Data Audit
    (
        claude -p "Audit the $FEATURE data using MCP database access. Check record counts, data quality, null fields, orphaned records. Output as markdown with headers: Record Counts, Data Quality Issues, Missing Data, Recommendations." \
            --output-format text > "$REPO_ROOT/.claude/audits/${FEATURE}_data.md" 2>/dev/null
    ) &

    # API Audit
    (
        claude -p "Audit the $FEATURE API endpoints in backend/api/routers/. Check authentication, validation, error handling, response consistency. Output as markdown with headers: Endpoints Reviewed, Auth Gaps, Validation Issues, Missing Endpoints, Recommendations." \
            --output-format text > "$REPO_ROOT/.claude/audits/${FEATURE}_api.md" 2>/dev/null
    ) &

    # Wait for all
    wait

    print_success "All audits complete"

    # Combine and post
    echo "Posting findings to Issue #$ISSUE..."

    COMBINED="# 🔍 Automated Audit Results

**Feature:** $FEATURE
**Timestamp:** $(date)

---

## UX Audit
$(cat "$REPO_ROOT/.claude/audits/${FEATURE}_ux.md" 2>/dev/null || echo "Failed")

---

## Code Audit
$(cat "$REPO_ROOT/.claude/audits/${FEATURE}_code.md" 2>/dev/null || echo "Failed")

---

## Data Audit
$(cat "$REPO_ROOT/.claude/audits/${FEATURE}_data.md" 2>/dev/null || echo "Failed")

---

## API Audit
$(cat "$REPO_ROOT/.claude/audits/${FEATURE}_api.md" 2>/dev/null || echo "Failed")

---

**Next:** Review findings, then reply APPROVED or add comments."

    gh issue comment "$ISSUE" --body "$COMBINED"

    print_success "Findings posted to Issue #$ISSUE"
}

# -----------------------------------------------------------------------------
# PHASE 2: PLAN
# -----------------------------------------------------------------------------

create_plan() {
    print_header "📋 PHASE 2: CREATING PLAN"

    echo "Generating implementation plan based on audits..."

    ISSUE_CONTENT=$(gh issue view "$ISSUE" --comments)

    PLAN=$(claude -p "Based on these audit findings, create an implementation plan for $FEATURE:

$ISSUE_CONTENT

Output a detailed plan with: Summary, Priority Order, Tasks (with files, acceptance criteria, effort), Testing Plan, Risks." \
        --output-format text 2>/dev/null || echo "Plan generation failed")

    gh issue comment "$ISSUE" --body "# 📋 Implementation Plan

$PLAN

---

**Next:** Review plan, reply APPROVED to proceed with build."

    print_success "Plan posted to Issue #$ISSUE"
}

# -----------------------------------------------------------------------------
# PHASE 3: BUILD
# -----------------------------------------------------------------------------

run_build() {
    print_header "🔨 PHASE 3: BUILDING"

    BRANCH="feat/${FEATURE}-${ISSUE}"

    cd "$REPO_ROOT"
    git checkout main
    git pull origin main
    git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"

    echo "Branch: $BRANCH"
    echo ""
    echo "Starting interactive build session..."
    echo "The agent will implement the plan."
    echo ""

    ISSUE_CONTENT=$(gh issue view "$ISSUE" --comments)

    claude -p "You are the Builder. Implement this plan:

$ISSUE_CONTENT

Rules:
- Small commits with #$ISSUE reference
- Test before committing
- Create issues for bugs found
- When done: push branch, create PR, comment on issue

GO."
}

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

print_header "🚀 BUILD FEATURE: $FEATURE"

cd "$REPO_ROOT"

case "$PHASE" in
    audit|audits)
        read -p "Enter issue number (or press Enter to create new): " ISSUE
        if [ -z "$ISSUE" ]; then
            create_or_find_issue
        fi
        run_audits
        ;;
    plan)
        read -p "Enter issue number: " ISSUE
        create_plan
        ;;
    build)
        read -p "Enter issue number: " ISSUE
        run_build
        ;;
    all|*)
        create_or_find_issue
        run_audits
        echo ""
        read -p "Review audits at Issue #$ISSUE. Press Enter when ready for plan..." _
        create_plan
        echo ""
        read -p "Review plan at Issue #$ISSUE. Press Enter when approved to build..." _
        run_build
        ;;
esac

print_header "🏁 DONE"
echo "Issue: https://github.com/lukassherman27/Benlsey-Operating-System/issues/$ISSUE"
echo ""
