#!/bin/bash
# ============================================================================
# AGENT LAUNCHER LIBRARY
#
# Functions to launch and manage Claude, Codex, and Gemini agents.
# Sourced by orchestrate.sh
# ============================================================================

AGENT_LAUNCHER_VERSION="1.0.0"

# ============================================================================
# WORKTREE MANAGEMENT
# ============================================================================

create_worktree() {
    local agent="$1"
    local issue="$2"
    local base_branch="${3:-main}"

    local worktree_name="bds-${agent}-${issue}"
    local worktree_path="$(dirname "$PROJECT_ROOT")/$worktree_name"
    local branch_name="feat/${agent}-${issue}"

    # Check if worktree already exists
    if [ -d "$worktree_path" ]; then
        echo "$worktree_path"
        return 0
    fi

    # Create worktree
    cd "$PROJECT_ROOT"
    git fetch origin "$base_branch" 2>/dev/null || true
    git worktree add -b "$branch_name" "$worktree_path" "origin/$base_branch" 2>/dev/null || \
        git worktree add "$worktree_path" "$branch_name" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "$worktree_path"
        return 0
    else
        return 1
    fi
}

remove_worktree() {
    local agent="$1"
    local issue="$2"

    local worktree_name="bds-${agent}-${issue}"
    local worktree_path="$(dirname "$PROJECT_ROOT")/$worktree_name"

    if [ -d "$worktree_path" ]; then
        cd "$PROJECT_ROOT"
        git worktree remove "$worktree_path" --force 2>/dev/null || rm -rf "$worktree_path"
    fi
}

list_active_worktrees() {
    cd "$PROJECT_ROOT"
    git worktree list | grep -v "$(pwd)" | grep "bds-"
}

# ============================================================================
# AGENT DETECTION
# ============================================================================

detect_available_agents() {
    local agents=()

    if command -v claude >/dev/null 2>&1; then
        agents+=("claude")
    fi

    if command -v codex >/dev/null 2>&1; then
        agents+=("codex")
    fi

    if command -v gemini >/dev/null 2>&1; then
        agents+=("gemini")
    fi

    echo "${agents[@]}"
}

is_agent_available() {
    local agent="$1"
    command -v "$agent" >/dev/null 2>&1
}

# ============================================================================
# AGENT LAUNCHING
# ============================================================================

launch_agent_with_prompt() {
    local agent="$1"
    local prompt_file="$2"
    local output_file="$3"
    local worktree_path="$4"

    if [ ! -f "$prompt_file" ]; then
        echo "Error: Prompt file not found: $prompt_file" >&2
        return 1
    fi

    local prompt=$(cat "$prompt_file")

    case "$agent" in
        claude)
            if [ -n "$worktree_path" ]; then
                cd "$worktree_path"
            fi
            # Claude can read the prompt from stdin or file
            echo "$prompt" | claude --print > "$output_file" 2>&1
            ;;
        codex)
            if [ -n "$worktree_path" ]; then
                cd "$worktree_path"
            fi
            echo "$prompt" | codex > "$output_file" 2>&1
            ;;
        gemini)
            # Gemini might not need worktree for research
            echo "$prompt" | gemini > "$output_file" 2>&1
            ;;
        *)
            echo "Error: Unknown agent: $agent" >&2
            return 1
            ;;
    esac

    return $?
}

generate_launch_command() {
    local agent="$1"
    local prompt_file="$2"
    local output_file="$3"
    local worktree_path="$4"

    local cmd=""

    case "$agent" in
        claude)
            if [ -n "$worktree_path" ]; then
                cmd="cd $worktree_path && cat $prompt_file | claude --print > $output_file"
            else
                cmd="cat $prompt_file | claude --print > $output_file"
            fi
            ;;
        codex)
            if [ -n "$worktree_path" ]; then
                cmd="cd $worktree_path && cat $prompt_file | codex > $output_file"
            else
                cmd="cat $prompt_file | codex > $output_file"
            fi
            ;;
        gemini)
            cmd="cat $prompt_file | gemini > $output_file"
            ;;
    esac

    echo "$cmd"
}

# ============================================================================
# STATUS TRACKING
# ============================================================================

update_agent_status() {
    local agent="$1"
    local status="$2"
    local session_id="$3"

    local status_file="$CONTEXT_DIR/agent-status.json"

    if [ ! -f "$status_file" ]; then
        return 1
    fi

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Use Python to update JSON (more reliable than jq which may not be installed)
    python3 << EOF
import json
import sys

try:
    with open('$status_file', 'r') as f:
        data = json.load(f)

    if 'agents' not in data:
        data['agents'] = {}

    data['agents']['$agent'] = {
        'status': '$status',
        'updated_at': '$timestamp'
    }

    with open('$status_file', 'w') as f:
        json.dump(data, f, indent=2)
except Exception as e:
    print(f"Error updating status: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

get_agent_status() {
    local agent="$1"
    local status_file="$CONTEXT_DIR/agent-status.json"

    if [ ! -f "$status_file" ]; then
        echo "unknown"
        return
    fi

    python3 << EOF
import json
try:
    with open('$status_file', 'r') as f:
        data = json.load(f)
    status = data.get('agents', {}).get('$agent', {}).get('status', 'unknown')
    print(status)
except:
    print('unknown')
EOF
}
