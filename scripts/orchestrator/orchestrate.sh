#!/bin/bash
# ============================================================================
# MULTI-AGENT ORCHESTRATOR
#
# Usage:
#   ./scripts/orchestrator/orchestrate.sh <command> [args]
#
# Commands:
#   audit <area>         Run multi-agent audit (system, proposals, emails, etc.)
#   build <issue>        Full build workflow for an issue
#   consolidate <type>   Merge findings from all agents
#   status               Check current orchestration status
#   clean                Clean up worktrees and context
#
# Examples:
#   orc audit system
#   orc build 356
#   orc consolidate audit
#   orc status
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONTEXT_DIR="$PROJECT_ROOT/.claude/orchestrator/context"
PROMPTS_DIR="$PROJECT_ROOT/.claude/orchestrator/prompts"

# Source library functions
source "$SCRIPT_DIR/lib/agent-launcher.sh" 2>/dev/null || true
source "$SCRIPT_DIR/lib/context-manager.sh" 2>/dev/null || true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}▶${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

check_cli_available() {
    local cli="$1"
    if command -v "$cli" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

ensure_context_dirs() {
    mkdir -p "$CONTEXT_DIR/findings"
    mkdir -p "$CONTEXT_DIR/consolidated"
}

get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# ============================================================================
# COMMAND: STATUS
# ============================================================================

cmd_status() {
    print_header "ORCHESTRATOR STATUS"

    # Check available CLIs
    echo "Available Agents:"
    if check_cli_available "claude"; then
        print_success "Claude CLI"
    else
        print_error "Claude CLI (not installed)"
    fi

    if check_cli_available "codex"; then
        print_success "Codex CLI"
    else
        print_warning "Codex CLI (not installed)"
    fi

    if check_cli_available "gemini"; then
        print_success "Gemini CLI"
    else
        print_warning "Gemini CLI (not installed)"
    fi

    echo ""

    # Check for active session
    if [ -f "$CONTEXT_DIR/agent-status.json" ]; then
        echo "Current Session:"
        cat "$CONTEXT_DIR/agent-status.json" | python3 -m json.tool 2>/dev/null || cat "$CONTEXT_DIR/agent-status.json"
    else
        echo "No active session."
    fi

    echo ""

    # Check for worktrees
    echo "Active Worktrees:"
    git worktree list 2>/dev/null | grep -v "$(pwd)" || echo "  (none)"

    echo ""

    # Check for pending findings
    echo "Pending Findings:"
    ls -la "$CONTEXT_DIR/findings/" 2>/dev/null || echo "  (none)"

    echo ""
}

# ============================================================================
# COMMAND: AUDIT
# ============================================================================

cmd_audit() {
    local area="${1:-system}"

    print_header "MULTI-AGENT AUDIT: $area"

    ensure_context_dirs

    local session_id="audit-$area-$(date +%Y%m%d-%H%M%S)"
    local timestamp=$(get_timestamp)

    # Create session status
    cat > "$CONTEXT_DIR/agent-status.json" <<EOF
{
  "session_id": "$session_id",
  "command": "audit",
  "area": "$area",
  "started_at": "$timestamp",
  "phase": "audit",
  "agents": {}
}
EOF

    print_step "Session: $session_id"
    echo ""

    # Determine which agents to run
    local agents_to_run=()

    if check_cli_available "claude"; then
        agents_to_run+=("claude")
    fi
    if check_cli_available "codex"; then
        agents_to_run+=("codex")
    fi
    if check_cli_available "gemini"; then
        agents_to_run+=("gemini")
    fi

    if [ ${#agents_to_run[@]} -eq 0 ]; then
        print_error "No agent CLIs available. Install claude, codex, or gemini."
        exit 1
    fi

    print_step "Running audit with: ${agents_to_run[*]}"
    echo ""

    # Generate prompts for each agent
    for agent in "${agents_to_run[@]}"; do
        generate_audit_prompt "$agent" "$area" > "$CONTEXT_DIR/findings/${agent}-audit-prompt.md"
        print_step "Generated prompt for $agent"
    done

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "NEXT STEPS:"
    echo ""
    echo "1. Open separate terminals for each agent"
    echo ""

    for agent in "${agents_to_run[@]}"; do
        local prompt_file="$CONTEXT_DIR/findings/${agent}-audit-prompt.md"
        local output_file="$CONTEXT_DIR/findings/${agent}-audit-${area}.md"

        echo "   $(echo $agent | tr '[:lower:]' '[:upper:]'):"
        echo "   $agent < $prompt_file > $output_file"
        echo ""
    done

    echo "2. When all agents complete, run:"
    echo "   ./scripts/orchestrator/orchestrate.sh consolidate audit"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
}

generate_audit_prompt() {
    local agent="$1"
    local area="$2"
    local issue="${3:-0}"
    local branch="${4:-main}"
    local worktree="${5:-$PROJECT_ROOT}"

    local template_file="$PROMPTS_DIR/audit-${agent}.md"

    if [ -f "$template_file" ]; then
        # Use template file with variable substitution
        sed -e "s|{{ISSUE}}|$issue|g" \
            -e "s|{{BRANCH}}|$branch|g" \
            -e "s|{{WORKTREE}}|$worktree|g" \
            -e "s|{{AREA}}|$area|g" \
            "$template_file"
    else
        # Fallback inline prompt
        local role=""
        case "$agent" in
            claude)
                role="Code Quality Auditor"
                ;;
            codex)
                role="Security Auditor"
                ;;
            gemini)
                role="Architecture Auditor"
                ;;
        esac

        cat <<EOF
# Audit Task: $area

You are the ${role} for the Bensley Operating System.

## Required Context
- Issue: #$issue
- Branch: $branch
- Must read first: CLAUDE.md, AGENTS.md, docs/roadmap.md

## Output (MANDATORY)
Post a GitHub comment to issue #$issue using:
gh issue comment $issue --body "## ${agent^} Audit Findings ..."

## Rules
- Audit only. No code changes.
- GitHub is source of truth.
- Post findings to GitHub before exiting.

## Focus
Audit the $area area thoroughly and document your findings.
EOF
    fi
}

# ============================================================================
# COMMAND: BUILD
# ============================================================================

cmd_build() {
    local issue="$1"

    if [ -z "$issue" ]; then
        print_error "Usage: orchestrate.sh build <issue_number>"
        exit 1
    fi

    print_header "BUILD WORKFLOW: Issue #$issue"

    # Verify issue exists
    local issue_title=$(gh issue view "$issue" --json title -q .title 2>/dev/null || echo "")
    if [ -z "$issue_title" ]; then
        print_error "Issue #$issue not found"
        exit 1
    fi

    print_step "Issue: #$issue - $issue_title"
    echo ""

    ensure_context_dirs

    local session_id="build-$issue-$(date +%Y%m%d-%H%M%S)"
    local timestamp=$(get_timestamp)

    # Create session status
    cat > "$CONTEXT_DIR/agent-status.json" <<EOF
{
  "session_id": "$session_id",
  "command": "build",
  "issue": $issue,
  "issue_title": "$issue_title",
  "started_at": "$timestamp",
  "phase": "planning",
  "agents": {}
}
EOF

    # Set current goal
    cat > "$CONTEXT_DIR/current-goal.md" <<EOF
# Current Goal

**Issue:** #$issue - $issue_title
**Session:** $session_id
**Started:** $timestamp

## Objective
Complete the implementation of Issue #$issue

## Workflow
1. Audit current state
2. Research best practices
3. Create implementation plan
4. Build (parallel agents)
5. Cross-review
6. Merge

## Status
Phase: planning
EOF

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "BUILD WORKFLOW INITIALIZED"
    echo ""
    echo "Session: $session_id"
    echo "Goal saved to: $CONTEXT_DIR/current-goal.md"
    echo ""
    echo "NEXT STEPS:"
    echo ""
    echo "1. Run audit first:"
    echo "   ./scripts/orchestrator/orchestrate.sh audit proposals"
    echo ""
    echo "2. Review consolidated findings"
    echo ""
    echo "3. Use launch_agent.sh to start building:"
    echo "   ./launch_agent.sh claude $issue"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
}

# ============================================================================
# COMMAND: CONSOLIDATE
# ============================================================================

cmd_consolidate() {
    local type="${1:-audit}"

    print_header "CONSOLIDATE FINDINGS: $type"

    # Get session ID from current session
    local session_id=""
    if [ -f "$CONTEXT_DIR/agent-status.json" ]; then
        session_id=$(python3 -c "import json; print(json.load(open('$CONTEXT_DIR/agent-status.json')).get('session_id', ''))" 2>/dev/null || echo "")
    fi

    if [ -z "$session_id" ]; then
        print_error "No active session found. Run 'orc audit <area>' first."
        exit 1
    fi

    print_step "Session: $session_id"
    echo ""

    # Check for findings
    local findings_count=0
    for agent in claude codex gemini; do
        local finding_file="$CONTEXT_DIR/findings/${agent}-${type}-*.md"
        if ls $finding_file 1>/dev/null 2>&1; then
            findings_count=$((findings_count + 1))
            print_success "Found findings from $agent"
        else
            print_warning "No findings from $agent"
        fi
    done

    if [ $findings_count -eq 0 ]; then
        print_error "No findings to consolidate."
        exit 1
    fi

    echo ""

    # Create consolidated output
    local output_file="$CONTEXT_DIR/consolidated/${type}-summary-$(date +%Y%m%d-%H%M%S).md"
    local timestamp=$(get_timestamp)

    cat > "$output_file" << EOF
# Consolidated ${type^} Summary

**Session:** $session_id
**Generated:** $timestamp
**Agents:** $findings_count

---

EOF

    # Append each agent's findings
    for agent in claude codex gemini; do
        local finding_pattern="$CONTEXT_DIR/findings/${agent}-${type}-*.md"
        local finding_file=$(ls $finding_pattern 2>/dev/null | head -1)

        if [ -f "$finding_file" ]; then
            cat >> "$output_file" << EOF

## ${agent^} Findings

$(cat "$finding_file")

---

EOF
            print_step "Added ${agent} findings"
        fi
    done

    echo ""
    print_success "Consolidated report: $output_file"
    echo ""

    # Update session phase
    if [ -f "$CONTEXT_DIR/agent-status.json" ]; then
        python3 << EOF
import json
with open('$CONTEXT_DIR/agent-status.json', 'r') as f:
    data = json.load(f)
data['phase'] = 'consolidated'
with open('$CONTEXT_DIR/agent-status.json', 'w') as f:
    json.dump(data, f, indent=2)
EOF
    fi

    echo "View report:"
    echo "  cat $output_file"
    echo ""
}

# ============================================================================
# COMMAND: CLEAN
# ============================================================================

cmd_clean() {
    print_header "CLEANUP"

    print_step "Removing context files..."
    rm -rf "$CONTEXT_DIR/findings/"*
    rm -rf "$CONTEXT_DIR/consolidated/"*
    rm -f "$CONTEXT_DIR/agent-status.json"
    rm -f "$CONTEXT_DIR/current-goal.md"

    print_step "Removing orphan worktrees..."
    git worktree prune 2>/dev/null || true

    print_success "Cleanup complete"
}

# ============================================================================
# COMMAND: HELP
# ============================================================================

cmd_help() {
    cat <<EOF

MULTI-AGENT ORCHESTRATOR
========================

Coordinates Claude, Codex, and Gemini agents for parallel work.

USAGE:
  ./scripts/orchestrator/orchestrate.sh <command> [args]

COMMANDS:
  audit <area>      Run multi-agent audit
                    Areas: system, proposals, emails, projects, frontend, backend

  build <issue>     Initialize build workflow for an issue
                    Creates session, sets goal, guides through phases

  consolidate       Merge findings from all agents into single report
                    Run after agents complete their audits

  status            Show current session status, available agents, worktrees

  clean             Remove context files and prune worktrees

  help              Show this help message

EXAMPLES:
  orc audit system
  orc audit proposals
  orc consolidate audit
  orc build 356
  orc status
  orc clean

ALIAS:
  Add to your ~/.bashrc or ~/.zshrc:
  alias orc="$PROJECT_ROOT/scripts/orchestrator/orchestrate.sh"

EOF
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    cd "$PROJECT_ROOT"

    local command="${1:-help}"
    shift || true

    case "$command" in
        audit)
            cmd_audit "$@"
            ;;
        build)
            cmd_build "$@"
            ;;
        consolidate)
            cmd_consolidate "$@"
            ;;
        status)
            cmd_status "$@"
            ;;
        clean)
            cmd_clean "$@"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "Unknown command: $command"
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
