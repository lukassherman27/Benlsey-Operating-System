#!/bin/bash
# ============================================================================
# MULTI-AGENT LAUNCHER
# Usage: ./launch_agent.sh <agent> <issue_number> [--review <pr_number>]
#
# Examples:
#   ./launch_agent.sh claude 370           # Claude works on issue #370
#   ./launch_agent.sh codex 370 --review 371  # Codex reviews PR #371 for issue #370
# ============================================================================

set -e

AGENT="$1"
ISSUE="$2"
REVIEW_MODE=false
PR_NUMBER=""

# Parse --review flag
if [ "$3" = "--review" ]; then
    REVIEW_MODE=true
    PR_NUMBER="$4"
    if [ -z "$PR_NUMBER" ]; then
        echo "Error: --review requires a PR number"
        echo "Usage: ./launch_agent.sh <agent> <issue> --review <pr_number>"
        exit 1
    fi
fi

# Validate inputs
if [ -z "$AGENT" ] || [ -z "$ISSUE" ]; then
    echo ""
    echo "Usage: ./launch_agent.sh <agent> <issue_number> [--review <pr_number>]"
    echo ""
    echo "Agents: claude, codex"
    echo ""
    echo "Examples:"
    echo "  ./launch_agent.sh claude 370              # Work on issue #370"
    echo "  ./launch_agent.sh codex 370 --review 371  # Review PR #371"
    echo ""
    exit 1
fi

# Normalize agent name
AGENT_LOWER=$(echo "$AGENT" | tr '[:upper:]' '[:lower:]')

# Set agent identity
case "$AGENT_LOWER" in
    claude)
        GIT_NAME="Claude"
        GIT_EMAIL="noreply@anthropic.com"
        LABEL="agent:claude"
        ;;
    codex)
        GIT_NAME="Codex"
        GIT_EMAIL="noreply@openai.com"
        LABEL="agent:codex"
        ;;
    *)
        echo "Unknown agent: $AGENT"
        echo "Valid agents: claude, codex"
        exit 1
        ;;
esac

# Verify clean worktree
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo "ERROR: Working directory is not clean."
    echo "Commit or stash your changes first:"
    echo "  git stash"
    echo ""
    git status --short
    exit 1
fi

# Get issue info
echo "Fetching issue #$ISSUE..."
ISSUE_TITLE=$(gh issue view "$ISSUE" --json title -q .title 2>/dev/null || echo "")

if [ -z "$ISSUE_TITLE" ]; then
    echo "Error: Issue #$ISSUE not found"
    exit 1
fi

# ============================================================================
# REVIEW MODE
# ============================================================================
if [ "$REVIEW_MODE" = true ]; then
    echo ""
    echo "=============================================="
    echo "  REVIEW MODE: $GIT_NAME reviewing PR #$PR_NUMBER"
    echo "=============================================="
    echo ""

    # Check out the PR
    echo "Checking out PR #$PR_NUMBER..."
    gh pr checkout "$PR_NUMBER"

    # Don't change git author in review mode
    echo ""
    echo "Review commands:"
    echo "  gh pr diff $PR_NUMBER                    # See changes"
    echo "  gh pr view $PR_NUMBER                    # View PR details"
    echo "  gh pr review $PR_NUMBER --comment -b 'Your feedback'  # Comment"
    echo "  gh pr review $PR_NUMBER --approve        # Approve"
    echo "  gh pr review $PR_NUMBER --request-changes -b 'Issues'  # Request changes"
    echo ""

    # Show PR context
    echo "--- PR CONTEXT ---"
    gh pr view "$PR_NUMBER" --json title,body -q '"Title: " + .title + "\n\nBody:\n" + .body' | head -30
    echo ""
    echo "--- FILES CHANGED ---"
    gh pr diff "$PR_NUMBER" --stat
    echo ""

    exit 0
fi

# ============================================================================
# WORK MODE
# ============================================================================

# Generate branch name
BRANCH_SLUG=$(echo "$ISSUE_TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 ]//g' | tr ' ' '-' | cut -c1-30)
BRANCH_NAME="feat/${AGENT_LOWER}-${BRANCH_SLUG}-${ISSUE}"

echo ""
echo "=============================================="
echo "  LAUNCHING: $GIT_NAME"
echo "  ISSUE: #$ISSUE - $ISSUE_TITLE"
echo "  BRANCH: $BRANCH_NAME"
echo "=============================================="
echo ""

# 1. Ensure hooks are configured
if [ -d ".githooks" ]; then
    git config core.hooksPath .githooks
fi

# 2. Fetch latest and create/switch to branch
echo "Preparing branch..."
git fetch origin

# Check if branch exists locally or remotely
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
    echo "Switching to existing local branch..."
    git checkout "$BRANCH_NAME"
    git pull origin "$BRANCH_NAME" 2>/dev/null || true
elif git show-ref --verify --quiet "refs/remotes/origin/$BRANCH_NAME" 2>/dev/null; then
    echo "Checking out existing remote branch..."
    git checkout -b "$BRANCH_NAME" "origin/$BRANCH_NAME"
else
    echo "Creating new branch from main..."
    git checkout -b "$BRANCH_NAME" origin/main
fi

# 3. Set git author for this agent
git config user.name "$GIT_NAME"
git config user.email "$GIT_EMAIL"

# 4. Set EXPECTED_BRANCH for hook enforcement
export EXPECTED_BRANCH="$BRANCH_NAME"

# 5. Add agent label to issue
echo "Adding label to issue..."
gh issue edit "$ISSUE" --add-label "$LABEL" 2>/dev/null || true

# 6. Print context for the agent
echo ""
echo "=============================================="
echo "  READY FOR $GIT_NAME"
echo "=============================================="
echo ""
echo "Branch: $BRANCH_NAME"
echo "Author: $GIT_NAME <$GIT_EMAIL>"
echo "Issue: #$ISSUE"
echo ""
echo "IMPORTANT: Run this in your shell to enforce branch:"
echo "  export EXPECTED_BRANCH=$BRANCH_NAME"
echo ""
echo "When done:"
echo "  git push -u origin $BRANCH_NAME"
echo "  gh pr create --title \"feat: $ISSUE_TITLE\" --body \"Fixes #$ISSUE\""
echo ""

# 7. Fetch issue body for context
echo "--- ISSUE CONTEXT ---"
gh issue view "$ISSUE" --json body -q .body | head -50
echo ""
echo "--- END CONTEXT ---"
echo ""
