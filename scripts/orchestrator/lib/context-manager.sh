#!/bin/bash
# ============================================================================
# CONTEXT MANAGER LIBRARY
#
# Functions to manage shared context between agents.
# Sourced by orchestrate.sh
# ============================================================================

CONTEXT_MANAGER_VERSION="1.0.0"

# ============================================================================
# CONTEXT INITIALIZATION
# ============================================================================

init_context() {
    local session_id="$1"
    local command="$2"

    mkdir -p "$CONTEXT_DIR/findings"
    mkdir -p "$CONTEXT_DIR/consolidated"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "$CONTEXT_DIR/agent-status.json" << EOF
{
  "session_id": "$session_id",
  "command": "$command",
  "started_at": "$timestamp",
  "phase": "init",
  "agents": {}
}
EOF
}

# ============================================================================
# FINDINGS MANAGEMENT
# ============================================================================

save_finding() {
    local agent="$1"
    local type="$2"
    local content="$3"
    local session_id="$4"

    local filename="${agent}-${type}-${session_id}.md"
    local filepath="$CONTEXT_DIR/findings/$filename"

    echo "$content" > "$filepath"
    echo "$filepath"
}

get_finding() {
    local agent="$1"
    local type="$2"
    local session_id="$3"

    local filename="${agent}-${type}-${session_id}.md"
    local filepath="$CONTEXT_DIR/findings/$filename"

    if [ -f "$filepath" ]; then
        cat "$filepath"
    fi
}

list_findings() {
    local session_id="$1"

    if [ -n "$session_id" ]; then
        ls "$CONTEXT_DIR/findings/" 2>/dev/null | grep "$session_id"
    else
        ls "$CONTEXT_DIR/findings/" 2>/dev/null
    fi
}

# ============================================================================
# CONSOLIDATION
# ============================================================================

consolidate_findings() {
    local type="$1"
    local session_id="$2"
    local output_file="$CONTEXT_DIR/consolidated/${type}-summary-${session_id}.md"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "$output_file" << EOF
# Consolidated ${type^} Summary

**Session:** $session_id
**Generated:** $timestamp

---

EOF

    # Append each agent's findings
    for agent in claude codex gemini; do
        local finding_file="$CONTEXT_DIR/findings/${agent}-${type}-${session_id}.md"

        if [ -f "$finding_file" ]; then
            cat >> "$output_file" << EOF

## ${agent^} Findings

$(cat "$finding_file")

---

EOF
        fi
    done

    echo "$output_file"
}

# ============================================================================
# GOAL MANAGEMENT
# ============================================================================

set_current_goal() {
    local issue="$1"
    local title="$2"
    local session_id="$3"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "$CONTEXT_DIR/current-goal.md" << EOF
# Current Goal

**Issue:** #$issue - $title
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
}

get_current_goal() {
    if [ -f "$CONTEXT_DIR/current-goal.md" ]; then
        cat "$CONTEXT_DIR/current-goal.md"
    else
        echo "No goal set"
    fi
}

update_goal_phase() {
    local phase="$1"

    if [ -f "$CONTEXT_DIR/current-goal.md" ]; then
        sed -i.bak "s/^Phase: .*/Phase: $phase/" "$CONTEXT_DIR/current-goal.md"
        rm -f "$CONTEXT_DIR/current-goal.md.bak"
    fi
}

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

get_session_id() {
    if [ -f "$CONTEXT_DIR/agent-status.json" ]; then
        python3 << EOF
import json
try:
    with open('$CONTEXT_DIR/agent-status.json', 'r') as f:
        data = json.load(f)
    print(data.get('session_id', ''))
except:
    pass
EOF
    fi
}

get_session_phase() {
    if [ -f "$CONTEXT_DIR/agent-status.json" ]; then
        python3 << EOF
import json
try:
    with open('$CONTEXT_DIR/agent-status.json', 'r') as f:
        data = json.load(f)
    print(data.get('phase', 'unknown'))
except:
    print('unknown')
EOF
    fi
}

set_session_phase() {
    local phase="$1"
    local status_file="$CONTEXT_DIR/agent-status.json"

    if [ -f "$status_file" ]; then
        python3 << EOF
import json
try:
    with open('$status_file', 'r') as f:
        data = json.load(f)
    data['phase'] = '$phase'
    with open('$status_file', 'w') as f:
        json.dump(data, f, indent=2)
except Exception as e:
    print(f"Error: {e}")
EOF
    fi
}

# ============================================================================
# CLEANUP
# ============================================================================

clean_context() {
    rm -rf "$CONTEXT_DIR/findings/"*
    rm -rf "$CONTEXT_DIR/consolidated/"*
    rm -f "$CONTEXT_DIR/agent-status.json"
    rm -f "$CONTEXT_DIR/current-goal.md"
}

clean_old_sessions() {
    local days="${1:-7}"

    # Remove findings older than N days
    find "$CONTEXT_DIR/findings" -type f -mtime +"$days" -delete 2>/dev/null
    find "$CONTEXT_DIR/consolidated" -type f -mtime +"$days" -delete 2>/dev/null
}
