# Multi-Agent Orchestrator

Coordinates Claude, Codex, and Gemini agents for parallel work on the Bensley Operating System.

## Quick Start

```bash
# Check status
./scripts/orchestrator/orchestrate.sh status

# Run multi-agent audit
./scripts/orchestrator/orchestrate.sh audit proposals

# Initialize build workflow for an issue
./scripts/orchestrator/orchestrate.sh build 356

# Clean up
./scripts/orchestrator/orchestrate.sh clean
```

## Alias (Optional)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
alias orc="/path/to/Benlsey-Operating-System/scripts/orchestrator/orchestrate.sh"
```

Then use: `orc status`, `orc audit system`, etc.

## Commands

| Command | Description |
|---------|-------------|
| `status` | Show available agents, active worktrees, session status |
| `audit <area>` | Generate audit prompts for all agents |
| `build <issue>` | Initialize build workflow for a GitHub issue |
| `clean` | Remove context files and prune worktrees |
| `help` | Show help message |

## Audit Areas

- `system` - Full system audit
- `proposals` - Proposal management code
- `emails` - Email processing and linking
- `projects` - Project management
- `frontend` - Next.js frontend
- `backend` - FastAPI backend

## How It Works

1. **Audit Phase**: Each agent gets a role-specific prompt
   - Claude: Code quality, structure, implementation
   - Codex: Security, vulnerabilities, data protection
   - Gemini: Architecture, best practices, research

2. **Parallel Work**: Agents work in separate terminals
   - Prompts are generated in `.claude/orchestrator/context/findings/`
   - Agents write output to the same directory

3. **Consolidation**: After all agents finish
   - Run `./scripts/orchestrator/orchestrate.sh consolidate audit`
   - Merged findings appear in `.claude/orchestrator/context/consolidated/`

## File Structure

```
scripts/orchestrator/
  orchestrate.sh       # Main entry point
  lib/
    agent-launcher.sh  # Agent management functions
    context-manager.sh # Context sharing functions
  README.md            # This file

.claude/orchestrator/
  context/
    findings/          # Each agent's raw output
    consolidated/      # Merged findings
    agent-status.json  # Session tracking
    current-goal.md    # Active goal
  prompts/
    audit-claude.md    # Claude's audit template
    audit-codex.md     # Codex's audit template
    audit-gemini.md    # Gemini's audit template
```

## Agent Roles

| Agent | Focus | Strengths |
|-------|-------|-----------|
| Claude | Code Quality | Deep code understanding, refactoring |
| Codex | Security | Vulnerability detection, best practices |
| Gemini | Architecture | Research, system design, documentation |
