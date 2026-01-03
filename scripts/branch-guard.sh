#!/bin/bash
# Branch Guard - Run before any commit
# Usage: source scripts/branch-guard.sh <expected-branch>

EXPECTED="$1"
CURRENT=$(git branch --show-current)

if [ -z "$EXPECTED" ]; then
    echo "❌ ERROR: No expected branch specified"
    echo "Usage: source scripts/branch-guard.sh feat/my-feature-123"
    return 1
fi

if [ "$CURRENT" != "$EXPECTED" ]; then
    echo ""
    echo "🚨🚨🚨 WRONG BRANCH 🚨🚨🚨"
    echo ""
    echo "Expected: $EXPECTED"
    echo "Actual:   $CURRENT"
    echo ""
    echo "Run: git checkout $EXPECTED"
    echo ""
    return 1
fi

echo "✅ Branch verified: $CURRENT"
