# Documentation Directory

All project documentation organized by type.

## Structure

```
docs/
├── architecture/   # System design and architecture docs
├── guides/         # How-to guides and tutorials
├── planning/       # Roadmaps, plans, and specs
├── reports/        # Audit reports and analysis
├── sessions/       # Session summaries (temporary)
├── agents/         # AI agent documentation and prompts
├── prompts/        # Claude prompts for specific tasks
├── dashboard/      # Dashboard-specific docs
└── archive/        # Old/completed docs
```

## What Goes Where

| Type | Folder | Examples |
|------|--------|----------|
| System design | `architecture/` | SYSTEM_ARCHITECTURE_MAP.md |
| How-to docs | `guides/` | GETTING_STARTED.md, DEPLOYMENT_GUIDE.md |
| Future plans | `planning/` | Feature specs, migration plans |
| Analysis results | `reports/` | Audit reports, data quality reports |
| Daily work logs | `sessions/` | SESSION_SUMMARY_*.md |
| AI/Claude docs | `agents/`, `prompts/` | Agent specs, prompt templates |
| Completed work | `archive/` | *_COMPLETE.md, *_FIXED.md |

## Naming Conventions

- Use SCREAMING_SNAKE_CASE for document names
- Include date for time-sensitive docs: `SESSION_SUMMARY_2025-11-24.md`
- Use descriptive suffixes: `*_GUIDE.md`, `*_PLAN.md`, `*_REPORT.md`

## Archiving

Move to `archive/` when:
- A feature is complete (*_COMPLETE.md)
- A bug is fixed (*_FIXED.md)
- A session is over (SESSION_*.md older than 2 weeks)
- A plan is superseded

## Root-Level Docs

Only these docs should stay at project root:
- `README.md` - Project overview
- `CLAUDE.md` - AI context (required)
- `2_MONTH_MVP_PLAN.md` - Current roadmap
- `DATABASE_MIGRATION_SUMMARY.md` - Critical reference
