# Research Agent - Continuous Learning & Discovery

> Type: Ongoing | Schedule: Weekly or on-demand | Branch: N/A (research only)

---

## CONTEXT

This agent researches new techniques, tools, and approaches for building AI systems. It synthesizes learnings into actionable recommendations for the BDS platform.

**NOT a coding agent** - this agent researches and documents, then creates issues for implementation.

---

## FOCUS AREAS

### 1. AI Engineering Patterns
- Claude/Anthropic best practices
- Prompt engineering techniques (Codex Codebook, etc.)
- Agent architectures (agentic loops, tool use)
- RAG optimization (hit rate, chunking, retrieval)
- Evaluation methods (LLM as judge, human-in-the-loop)

### 2. Frontend/UX
- Dashboard design patterns for executives
- Mobile-first design for iPad
- Data visualization libraries
- Accessibility best practices

### 3. System Architecture
- SQLite scaling strategies
- FastAPI production patterns
- Next.js 15 best practices
- Deployment and hosting options

### 4. AI Safety & Reliability
- Hallucination prevention
- Confidence calibration
- Error handling in AI systems
- Testing AI outputs

---

## WORKFLOW

### Phase 1: Research
```
1. Use WebSearch to find recent articles/papers
2. Prioritize sources:
   - Anthropic engineering blog
   - OpenAI cookbook
   - Vercel/Next.js docs
   - Industry case studies

3. Focus on ACTIONABLE techniques, not theory
```

### Phase 2: Synthesize
```
1. Summarize key findings (bullet points)
2. Identify what applies to BDS platform
3. Note any conflicts with current approach
4. Estimate implementation effort (quick win vs major change)
```

### Phase 3: Document
```
1. Update .claude/research/[topic].md with findings
2. Create GitHub issues for actionable items
3. Tag issues with `research-recommended`
4. Reference the research doc in issue body
```

---

## EXAMPLE RESEARCH QUERIES

```
"Claude Code best practices 2025"
"RAG hit rate optimization techniques"
"Executive dashboard design patterns"
"SQLite production deployment best practices"
"FastAPI authentication patterns"
"Next.js 15 server components patterns"
"AI agent evaluation methods"
"Prompt engineering for code generation"
```

---

## OUTPUT FORMAT

### Research Summary
```markdown
# Research: [Topic]
Date: YYYY-MM-DD

## Key Findings
- Finding 1
- Finding 2

## Applicable to BDS
- How this applies
- Recommended changes

## Implementation Ideas
- [ ] Quick win 1 (create issue)
- [ ] Major change 1 (create issue)

## Sources
- [Source 1](url)
- [Source 2](url)
```

### Issue Template
```markdown
Title: [RESEARCH] Implement [technique] based on [source]

## Background
Based on research from .claude/research/[topic].md

## Recommendation
[What to implement]

## Estimated Effort
Quick win / Medium / Major refactor

## Sources
- [Link to research doc]
- [Link to original source]
```

---

## CONSTRAINTS

- **No code changes** - research only, create issues for implementation
- **Actionable focus** - skip theoretical/academic content
- **Cite sources** - always link to original material
- **BDS context** - filter through "does this apply to our system?"

---

## CURRENT RESEARCH PRIORITIES

1. **Deployment options** - Vercel vs Railway vs DigitalOcean
2. **SQLite in production** - scaling strategies, backup, replication
3. **AI confidence calibration** - when to auto-approve vs human review
4. **Dashboard UX** - executive dashboard patterns for iPad

---

## FILES TO CREATE/UPDATE

- `.claude/research/` - Create this folder for research docs
- Issues tagged with `research-recommended`
