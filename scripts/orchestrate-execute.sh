#!/bin/bash

# =============================================================================
# MULTI-AGENT BUILDER
# =============================================================================
# Usage: ./scripts/orchestrate-execute.sh <feature> <issue_number>
#
# Run this AFTER plan is approved to execute the build.
# =============================================================================

set -e

FEATURE="${1:-proposals}"
ISSUE="${2:-356}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BRANCH="feat/${FEATURE}-${ISSUE}"

echo "=========================================="
echo "🔨 BUILD EXECUTOR"
echo "=========================================="
echo "Feature: $FEATURE"
echo "Issue: #$ISSUE"
echo "Branch: $BRANCH"
echo ""

# Create branch if it doesn't exist
cd "$REPO_ROOT"
git fetch origin main
git checkout main
git pull origin main
git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"

echo "📥 Fetching plan from Issue #$ISSUE..."
ISSUE_CONTENT=$(gh issue view "$ISSUE" --comments)

BUILD_PROMPT="You are the Builder Agent for the BDS Operations Platform.

Read these files first:
- CLAUDE.md for system context
- AGENTS.md for rules (FOLLOW THESE EXACTLY)

Here is the approved implementation plan:

$ISSUE_CONTENT

---

Your task: IMPLEMENT the plan above.

## Rules:
1. Work through tasks in priority order
2. Make small, focused commits
3. Reference #$ISSUE in every commit
4. Test each change before committing
5. If you find bugs, create new issues with gh issue create
6. Update the issue with progress after each major task

## Commit format:
feat($FEATURE): description #$ISSUE
fix($FEATURE): description #$ISSUE

## When done:
1. Push the branch
2. Create a PR with gh pr create
3. Comment on #$ISSUE that work is complete

GO - Start implementing now."

echo "🔨 Starting build..."
echo ""
echo "This will open an interactive Claude session to do the build."
echo "The agent will implement the plan and create commits."
echo ""

# Run Claude interactively for the build
claude -p "$BUILD_PROMPT"

echo ""
echo "=========================================="
echo "BUILD SESSION ENDED"
echo "=========================================="
echo ""
echo "Check the issue for updates: https://github.com/lukassherman27/Benlsey-Operating-System/issues/$ISSUE"
echo "Check for PR: gh pr list"
echo ""
