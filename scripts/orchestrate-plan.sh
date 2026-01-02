#!/bin/bash

# =============================================================================
# MULTI-AGENT PLANNER
# =============================================================================
# Usage: ./scripts/orchestrate-plan.sh <feature> <issue_number>
#
# Run this AFTER audits are complete to generate the implementation plan.
# =============================================================================

set -e

FEATURE="${1:-proposals}"
ISSUE="${2:-356}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=========================================="
echo "📝 IMPLEMENTATION PLANNER"
echo "=========================================="
echo "Feature: $FEATURE"
echo "Issue: #$ISSUE"
echo ""

# Get the issue content including comments
echo "📥 Fetching audit findings from Issue #$ISSUE..."
ISSUE_CONTENT=$(gh issue view "$ISSUE" --comments)

PLAN_PROMPT="You are the Lead Architect for the BDS Operations Platform.

Read these files first:
- CLAUDE.md for system context
- AGENTS.md for rules
- docs/roadmap.md for vision

Here are the audit findings for the $FEATURE feature:

$ISSUE_CONTENT

---

Your task: Create a detailed IMPLEMENTATION PLAN based on these audit findings.

The plan should include:

1. **Summary** - What we're building and why
2. **Priority Order** - What to build first, second, third
3. **Tasks Breakdown** - Specific tasks with acceptance criteria
4. **Technical Approach** - How to implement each major piece
5. **Files to Modify** - Exact files that need changes
6. **Testing Plan** - How to verify it works
7. **Risks** - What could go wrong

Output in this EXACT format:

# Implementation Plan: $FEATURE

## Summary
[2-3 sentences on what we're building]

## Priority Order
1. [Most important]
2. [Second]
3. [Third]
...

## Tasks

### Task 1: [Name]
**Priority:** P0/P1/P2
**Effort:** Small/Medium/Large
**Files:**
- [file path]
**Acceptance Criteria:**
- [ ] [criterion]
**Technical Approach:**
[How to implement]

### Task 2: [Name]
...

## Testing Plan
- [ ] [test case]

## Risks
- [risk and mitigation]

---
Ready for review. Reply APPROVED to proceed with build."

echo "🧠 Generating implementation plan..."
cd "$REPO_ROOT"

PLAN=$(claude -p "$PLAN_PROMPT" --output-format text 2>/dev/null || echo "Plan generation failed - run manually")

echo ""
echo "📤 Posting plan to Issue #$ISSUE..."

gh issue comment "$ISSUE" --body "# 📋 Implementation Plan

**Generated:** $(date)
**Feature:** $FEATURE

$PLAN

---

## To Proceed:
1. Review the plan above
2. Add any comments or adjustments
3. Reply with **APPROVED** to start the build phase
4. Then run: \`./scripts/orchestrate-execute.sh $FEATURE $ISSUE\`
"

echo ""
echo "=========================================="
echo "✅ PLAN POSTED"
echo "=========================================="
echo ""
echo "View at: https://github.com/lukassherman27/Benlsey-Operating-System/issues/$ISSUE"
echo ""
echo "Next: Review the plan, then run ./scripts/orchestrate-execute.sh $FEATURE $ISSUE"
echo ""
