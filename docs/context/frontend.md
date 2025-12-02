# Frontend Context Bundle

**Owner:** Frontend Builder Agent
**Last Updated:** 2025-12-02
**Architecture:** Next.js 15, localhost:3002, 23 pages

---

## Quick Start

```bash
cd frontend && npm run dev
# Access: http://localhost:3002
```

---

## Architecture

```
frontend/
├── src/app/(dashboard)/     <- Dashboard pages (23 routes)
│   ├── page.tsx             <- Main dashboard
│   ├── admin/               <- Admin section
│   │   ├── page.tsx         <- Admin overview
│   │   ├── email-categories/page.tsx  <- Category management
│   │   ├── email-links/page.tsx       <- Email link review
│   │   ├── financial-entry/page.tsx   <- Financial data entry
│   │   ├── patterns/page.tsx          <- Learned patterns review (NEW)
│   │   ├── project-editor/page.tsx    <- Project editing
│   │   ├── suggestions/page.tsx       <- AI suggestion review (Enhanced)
│   │   └── validation/page.tsx        <- Data validation
│   ├── contacts/            <- Contact management (NEW)
│   ├── contracts/           <- Contracts list
│   ├── deliverables/        <- Deliverables tracker
│   ├── finance/             <- Finance page
│   ├── meetings/            <- Meetings list (NEW)
│   ├── projects/            <- Projects list + detail
│   │   ├── page.tsx
│   │   └── [projectCode]/
│   │       ├── page.tsx     <- Project detail
│   │       └── emails/page.tsx <- Project emails
│   ├── proposals/           <- Proposals
│   │   ├── page.tsx
│   │   └── [projectCode]/page.tsx <- Proposal detail
│   ├── query/               <- Natural language query
│   ├── rfis/                <- RFI tracker (NEW)
│   ├── system/              <- System status
│   ├── tasks/               <- Task management (NEW)
│   └── tracker/             <- Proposal tracker
├── src/lib/
│   ├── api.ts               <- API client (100+ endpoints)
│   └── types.ts             <- TypeScript types
├── src/components/
│   ├── ui/                  <- shadcn/ui components
│   ├── dashboard/           <- Dashboard widgets
│   ├── layout/              <- App shell, nav
│   ├── project/             <- Project components
│   └── suggestions/         <- Enhanced Review UI (NEW 2025-12-02)
│       ├── enhanced-review-card.tsx   <- Main split-pane layout
│       ├── ai-analysis-panel.tsx      <- Detected entities & actions
│       ├── user-input-panel.tsx       <- Notes, tags, patterns
│       ├── database-preview.tsx       <- SQL changes preview
│       └── correction-dialog.tsx      <- Wrong suggestion fix (multi-link, categories, quick actions)
└── package.json
```

---

## Page → API Endpoint Map

| Page | Primary API Endpoints | Status |
|------|----------------------|--------|
| `/` (Dashboard) | `/api/dashboard/kpis`, `/api/proposals/stats` | ✅ Working |
| `/tracker` | `/api/proposals`, `/api/proposals/stats` | ✅ Working |
| `/projects` | `/api/projects/active`, `/api/projects/{code}` | ✅ Working |
| `/projects/[code]` | `/api/projects/{code}`, `/api/projects/{code}/fee-breakdown`, `/api/projects/{code}/unified-timeline` | ✅ Working |
| `/projects/[code]/emails` | `/api/emails`, project filter | ✅ Working |
| `/proposals` | Redirect to `/tracker` | ✅ Working |
| `/proposals/[code]` | `/api/proposals/{code}` | ✅ Working |
| `/contacts` | `/api/contacts`, `/api/contacts/stats` | ✅ NEW |
| `/contracts` | `/api/contracts`, `/api/contracts/stats` | ✅ Working |
| `/deliverables` | `/api/deliverables`, `/api/deliverables/pm-workload` | ✅ Working |
| `/meetings` | `/api/meetings` | ✅ Working |
| `/rfis` | `/api/rfis` | ✅ Working |
| `/tasks` | `/api/tasks` | ✅ NEW |
| `/query` | `/api/query/chat`, `/api/query/ask` | ⚠️ Error display issue |
| `/finance` | `/api/invoices`, `/api/invoices/stats` | ✅ Working |
| `/system` | `/api/health` | ✅ Working |
| `/admin` | Overview page | ✅ Working |
| `/admin/suggestions` | `/api/suggestions`, `/api/suggestions/*/full-context`, `/api/suggestion-tags`, `/api/suggestions/*/save-feedback` | ✅ Enhanced Review UI |
| `/admin/patterns` | `/api/patterns`, `/api/patterns/stats` | ✅ NEW |
| `/admin/email-categories` | `/api/email-categories` | ✅ NEW |
| `/admin/email-links` | `/api/emails/links` | ✅ Working |
| `/admin/validation` | `/api/admin/validation` | ✅ Working |
| `/admin/financial-entry` | `/api/invoices` | ✅ Working |
| `/admin/project-editor` | `/api/projects` | ✅ Working |

---

## Backend Routers (28 Total)

```
backend/api/routers/
├── admin.py          # /api/admin/* (includes run-pipeline)
├── agent.py          # /api/agent/*
├── analytics.py      # /api/analytics/*
├── contacts.py       # /api/contacts/* (NEW)
├── context.py        # /api/context/*
├── contracts.py      # /api/contracts/*
├── dashboard.py      # /api/dashboard/*
├── deliverables.py   # /api/deliverables/*
├── documents.py      # /api/documents/*
├── email_categories.py # /api/email-categories/* (NEW)
├── emails.py         # /api/emails/* (includes scan-sent-proposals)
├── files.py          # /api/files/*
├── finance.py        # /api/finance/*
├── health.py         # /api/health
├── intelligence.py   # /api/intelligence/*
├── invoices.py       # /api/invoices/*
├── learning.py       # /api/learning/*
├── meetings.py       # /api/meetings/*
├── milestones.py     # /api/milestones/*
├── outreach.py       # /api/outreach/*
├── projects.py       # /api/projects/* (includes unified-timeline)
├── proposals.py      # /api/proposals/*
├── query.py          # /api/query/*
├── rfis.py           # /api/rfis/*
├── suggestions.py    # /api/suggestions/*
├── tasks.py          # /api/tasks/* (NEW)
├── training.py       # /api/training/*
└── transcripts.py    # /api/meeting-transcripts/*
```

---

## Component Library

Using shadcn/ui components:
- Button, Card, Table, Dialog
- Switch (newly added Nov 29)
- Input, Select, Textarea
- Tabs, Badge, Alert

---

## Common Patterns

### API Client Usage
```typescript
import { api } from '@/lib/api';

// GET request
const data = await api.get('/projects/active');

// POST request
const result = await api.post('/suggestions/approve', { id: 123 });
```

### Page Structure
```tsx
export default function PageName() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) return <LoadingSkeleton />;
  if (!data.length) return <EmptyState />;

  return <DataTable data={data} />;
}
```

---

## Files Changed Frequently

| File | Purpose | Watch For |
|------|---------|-----------|
| `src/lib/api.ts` | API client | New endpoints |
| `src/lib/types.ts` | TypeScript types | Type updates |
| `page.tsx` files | Page components | UI changes |
| `components/ui/*` | UI components | New components |

---

## Queries This Context Answers

- "What pages exist in the frontend?"
- "What API does page X use?"
- "How do I add a new page?"
- "What components are available?"
- "How do I run the frontend?"
