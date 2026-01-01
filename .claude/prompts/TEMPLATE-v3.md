# Agent Prompt Template v3.0

> Based on Anthropic's [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) and [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)

---

## Template Structure

```markdown
# [Agent Name] - [Task Description]

> Issue: #[number] | Priority: [P0/P1/P2] | Branch: [branch-pattern]

---

## CONTEXT

[Brief business context - why this matters]

---

## PHASE 1: UNDERSTAND (Research First)

Before writing ANY code, gather context:

### Required Research
```bash
# [Specific commands to run]
```

### Questions to Answer
1. [Question 1]
2. [Question 2]
3. [Question 3]

### Files to Read
- `path/to/file1.py` - [what to look for]
- `path/to/file2.tsx` - [what to look for]

**STOP HERE** until you understand the current state. Document what you found.

---

## PHASE 2: THINK HARD (Planning)

Now that you understand the codebase, plan your approach.

### Design Decisions
[What decisions need to be made? List alternatives.]

### Web Research (if needed)
```
Search: "[specific search query]"
```

### Write Your Plan
Before implementing, write a brief plan:
1. Step 1
2. Step 2
3. Step 3

**Think through edge cases and potential issues.**

---

## PHASE 3: IMPLEMENT

### Implementation Steps
[Ordered list of what to build]

### Code Guidelines
- [Specific patterns to follow]
- [Errors to avoid]
- [Style requirements]

### Files to Modify/Create
| File | Action | Purpose |
|------|--------|---------|
| `path/to/file.py` | Modify | [purpose] |

---

## PHASE 4: VERIFY

### Testing Checklist
- [ ] [Test 1]
- [ ] [Test 2]
- [ ] [Test 3]

### Verification Commands
```bash
# [Commands to verify the implementation]
```

### Success Criteria
- [Criterion 1]
- [Criterion 2]

---

## PHASE 5: COMPLETE

### Commit Format
```bash
git commit -m "type(scope): description #[issue]"
```

### Create PR
```bash
gh pr create --title "[Title]" --body "[Body with context]"
```

### Cross-Issue Check
After completing, check if changes affect other open issues.

---

## CONSTRAINTS

- [Constraint 1 - what NOT to do]
- [Constraint 2]
- [Constraint 3]

---

## RESOURCES

- [Link to relevant docs]
- [Link to existing patterns]
```

---

## Key Principles (From Anthropic Research)

### 1. Research Before Implementation
> "Ask Claude to read relevant files... without immediately requesting code. This deliberate pause allows Claude to gather context."

Always include PHASE 1 with specific files to read and questions to answer.

### 2. Think Hard Before Coding
> "Use specific trigger words ('think,' 'think hard,' 'think harder') to allocate increasing computational budgets for deliberation."

Include explicit planning phase. Ask agent to "think through" before implementing.

### 3. Verification Loops
> "Code agents specifically: Leverage automated testing as feedback."

Always include PHASE 4 with concrete verification steps.

### 4. Context Management
> "Keep content concise and iterate on effectiveness like any production prompt."

Keep prompts focused. Don't overload with unnecessary context.

### 5. Ground Truth Feedback
> "Agents gain 'ground truth' from environment feedback at each step."

Include commands that give concrete feedback (tests, linting, type checking).

---

## Anti-Patterns to Avoid

1. **Jumping to code** - Never skip Phase 1
2. **Vague instructions** - Be specific about files, queries, patterns
3. **Missing verification** - Always include test commands
4. **No success criteria** - Define what "done" looks like
5. **Over-constraining** - Let the agent think, don't micromanage

---

## Example Usage

See actual agent prompts in:
- `.claude/prompts/data-cleanup-agent.md`
- `.claude/prompts/executive-dashboard-agent.md`
- `.claude/prompts/rbac-agent.md`
