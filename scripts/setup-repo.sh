#!/bin/bash
# Repository setup script - RUN THIS FIRST IN ANY NEW CLONE/WORKTREE
# Usage: ./scripts/setup-repo.sh

set -e

echo "Setting up Bensley Operating System repository..."
echo ""

# 1. Configure git to use tracked hooks
echo "1. Configuring git hooks..."
git config core.hooksPath .githooks
echo "   Hooks path set to .githooks/"

# 2. Verify we're not on main (warn only)
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ]; then
    echo ""
    echo "   WARNING: You're on main. Create a feature branch before working:"
    echo "   git checkout -b feat/your-feature-123"
fi

# 3. Install Python dependencies (if backend exists)
if [ -f "backend/requirements.txt" ]; then
    echo ""
    echo "2. Backend dependencies available at backend/requirements.txt"
    echo "   Run: pip install -r backend/requirements.txt"
fi

# 4. Install Node dependencies (if frontend exists)
if [ -f "frontend/package.json" ]; then
    echo ""
    echo "3. Frontend dependencies available at frontend/package.json"
    echo "   Run: cd frontend && npm install"
fi

echo ""
echo "Setup complete!"
echo ""
echo "IMPORTANT FOR AGENTS:"
echo "  - Never commit directly to main (blocked by hook)"
echo "  - Set EXPECTED_BRANCH env var before working:"
echo "    export EXPECTED_BRANCH=feat/my-feature-123"
echo "  - Or use worktrees for parallel work"
echo ""
