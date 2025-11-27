# Frontend Development Guide

**Bensley Operations Platform - Next.js Dashboard**

Complete guide to developing, extending, and maintaining the Next.js 15 frontend dashboard.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Development Setup](#development-setup)
4. [Key Patterns](#key-patterns)
5. [Adding Features](#adding-features)
6. [Component Library](#component-library)
7. [API Integration](#api-integration)
8. [Common Tasks](#common-tasks)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Tech Stack

### Core Framework
- **Next.js 15.1.3** - React framework with App Router
- **React 19** - UI library
- **TypeScript 5.x** - Type safety

### Styling
- **Tailwind CSS 3.x** - Utility-first CSS
- **shadcn/ui** - Component library built on Radix UI
- **Lucide React** - Icon library

### State & Data
- **TanStack Query (React Query) v5** - Server state management
- **React Hook Form** - Form handling
- **Zod** - Schema validation

### Utilities
- **date-fns** - Date manipulation
- **Recharts** - Data visualization
- **clsx + tailwind-merge** - Conditional styling

---

## Project Structure

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── (dashboard)/         # Dashboard layout group
│   │   │   ├── page.tsx         # Main dashboard (/)
│   │   │   ├── tracker/         # Proposal tracker (/tracker)
│   │   │   │   └── page.tsx
│   │   │   └── projects/        # Active projects (/projects)
│   │   │       └── page.tsx
│   │   ├── layout.tsx           # Root layout
│   │   └── globals.css          # Global styles
│   │
│   ├── components/              # React components
│   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── select.tsx
│   │   │   └── ... (40+ components)
│   │   ├── dashboard/           # Dashboard-specific components
│   │   │   ├── metric-card.tsx
│   │   │   ├── recent-activity.tsx
│   │   │   └── ...
│   │   └── proposals/           # Proposal-specific components
│   │       ├── proposal-table.tsx
│   │       ├── proposal-quick-edit-dialog.tsx
│   │       └── status-timeline.tsx
│   │
│   ├── lib/                     # Utilities and configurations
│   │   ├── api.ts              # API client functions
│   │   ├── types.ts            # TypeScript type definitions
│   │   ├── utils.ts            # Utility functions (cn, etc.)
│   │   └── providers.tsx       # React Query provider
│   │
│   └── hooks/                   # Custom React hooks (future)
│
├── public/                      # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

---

## Development Setup

### First Time Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at **http://localhost:3002**

### Available Scripts

```bash
npm run dev          # Start development server (port 3002)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler check
```

### Environment Variables

Create `.env.local` in the frontend directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Key Patterns

### 1. Server vs Client Components

**Next.js 15 uses Server Components by default.**

```tsx
// ✅ Server Component (default - no "use client")
// Can fetch data directly, but no hooks or interactivity
export default async function ProposalsPage() {
  const data = await fetch('http://localhost:8000/api/proposals');
  return <div>{/* ... */}</div>;
}

// ✅ Client Component (needs "use client")
// Can use hooks, state, event handlers
"use client";

import { useState } from "react";

export default function InteractiveComponent() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

**When to use Client Components:**
- Need React hooks (useState, useEffect, etc.)
- Event handlers (onClick, onChange, etc.)
- Browser-only APIs (localStorage, window, etc.)
- Third-party libraries that use hooks (React Query, forms, etc.)

**Current app pattern:** Most dashboard pages are Client Components because they use React Query and interactive UI.

### 2. React Query (TanStack Query)

**Setup:** Provider is in `src/lib/providers.tsx`

**Fetching Data:**

```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { getProposals } from "@/lib/api";

export default function ProposalsList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["proposals"],
    queryFn: getProposals,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data.map((proposal) => (
        <div key={proposal.project_code}>{proposal.project_name}</div>
      ))}
    </div>
  );
}
```

**Mutating Data:**

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateProposal } from "@/lib/api";

export default function EditProposalDialog({ proposal }) {
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (data) => updateProposal(proposal.project_code, data),
    onSuccess: () => {
      // Invalidate and refetch proposals
      queryClient.invalidateQueries({ queryKey: ["proposals"] });
    },
  });

  const handleSubmit = (formData) => {
    updateMutation.mutate(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button type="submit" disabled={updateMutation.isPending}>
        {updateMutation.isPending ? "Saving..." : "Save"}
      </button>
    </form>
  );
}
```

**Query Keys Pattern:**
```tsx
// List all proposals
["proposals"]

// Single proposal
["proposals", projectCode]

// Proposals with filters
["proposals", { status: "active", client: "BK-001" }]

// Status history for a proposal
["proposals", projectCode, "history"]
```

### 3. TypeScript Types

**All types are defined in `src/lib/types.ts`**

```typescript
export interface Proposal {
  project_code: string;
  project_name: string;
  client_name: string;
  current_status: string;
  current_remark?: string;
  project_value?: number;
  first_contact_date?: string;
  waiting_on?: string;
  next_steps?: string;
  created_at: string;
  updated_at: string;
}

export interface ProposalStatusHistory {
  id: number;
  project_code: string;
  old_status: string;
  new_status: string;
  changed_at: string;
  changed_by?: string;
  notes?: string;
}
```

**Using types:**

```tsx
import { Proposal } from "@/lib/types";

interface ProposalCardProps {
  proposal: Proposal;
  onEdit?: (proposal: Proposal) => void;
}

export function ProposalCard({ proposal, onEdit }: ProposalCardProps) {
  return <div>{proposal.project_name}</div>;
}
```

### 4. shadcn/ui Components

**Installing new components:**

```bash
npx shadcn@latest add button
npx shadcn@latest add dialog
npx shadcn@latest add select
```

This adds components to `src/components/ui/`

**Using components:**

```tsx
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function MyComponent() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Proposal</DialogTitle>
        </DialogHeader>
        {/* Content */}
      </DialogContent>
    </Dialog>
  );
}
```

**Available components in `src/components/ui/`:**
- button, input, select, textarea
- dialog, sheet, popover, dropdown-menu
- table, card, badge, separator
- form (with React Hook Form integration)
- And 40+ more...

### 5. Form Handling

**Pattern: React Hook Form + Zod (if needed)**

```tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

export function ProposalForm({ proposal, onSubmit }) {
  const [formData, setFormData] = useState({
    current_status: proposal?.current_status || "First Contact",
    project_value: proposal?.project_value || 0,
  });

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <Select
        value={formData.current_status}
        onValueChange={(value) => handleChange("current_status", value)}
      >
        {/* options */}
      </Select>

      <Input
        type="number"
        value={formData.project_value}
        onChange={(e) => handleChange("project_value", Number(e.target.value))}
      />

      <Button type="submit">Save</Button>
    </form>
  );
}
```

**CRITICAL PATTERN: Avoid infinite re-renders**

```tsx
// ❌ BAD - This causes infinite re-renders
const [formData, setFormData] = useState({...});

if (proposal) {
  setFormData({ current_status: proposal.current_status }); // Runs every render!
}

// ✅ GOOD - Use useEffect with dependencies
import { useEffect } from "react";

const [formData, setFormData] = useState({...});

useEffect(() => {
  if (proposal) {
    setFormData({ current_status: proposal.current_status });
  }
}, [proposal?.project_code]); // Only runs when proposal changes
```

**Reference:** See `src/components/proposals/proposal-quick-edit-dialog.tsx` for working example.

---

## Adding Features

### Adding a New Page

**1. Create page file:**

```bash
# Create new route at /dashboard/financials
frontend/src/app/(dashboard)/financials/page.tsx
```

**2. Implement the page:**

```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { getFinancialMetrics } from "@/lib/api";

export default function FinancialsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["financials"],
    queryFn: getFinancialMetrics,
  });

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Financial Dashboard</h1>
      {/* Content */}
    </div>
  );
}
```

**3. Add navigation link (if needed):**

Edit the layout or navigation component to add a link to `/financials`.

### Adding a New Component

**1. Create component file:**

```bash
frontend/src/components/financials/invoice-aging-chart.tsx
```

**2. Implement component:**

```tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

interface InvoiceAgingChartProps {
  data: Array<{ range: string; amount: number }>;
}

export function InvoiceAgingChart({ data }: InvoiceAgingChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Invoice Aging</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <XAxis dataKey="range" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="amount" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

**3. Use in page:**

```tsx
import { InvoiceAgingChart } from "@/components/financials/invoice-aging-chart";

export default function FinancialsPage() {
  const { data } = useQuery({...});

  return (
    <div>
      <InvoiceAgingChart data={data.invoiceAging} />
    </div>
  );
}
```

### Adding a New API Call

**1. Add function to `src/lib/api.ts`:**

```typescript
export async function getFinancialMetrics() {
  const response = await fetch(`${API_BASE_URL}/api/financial/metrics`);
  if (!response.ok) throw new Error("Failed to fetch financial metrics");
  return response.json();
}

export async function updateInvoice(invoiceId: string, data: Partial<Invoice>) {
  const response = await fetch(`${API_BASE_URL}/api/invoices/${invoiceId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to update invoice");
  return response.json();
}
```

**2. Add TypeScript types to `src/lib/types.ts`:**

```typescript
export interface Invoice {
  invoice_id: string;
  project_code: string;
  invoice_number: string;
  invoice_date: string;
  amount: number;
  status: "pending" | "paid" | "overdue";
  due_date: string;
}
```

**3. Use in component with React Query:**

```tsx
import { useQuery } from "@tanstack/react-query";
import { getFinancialMetrics } from "@/lib/api";
import { Invoice } from "@/lib/types";

export function FinancialMetrics() {
  const { data, isLoading, error } = useQuery<Invoice[]>({
    queryKey: ["financials"],
    queryFn: getFinancialMetrics,
  });

  // ...
}
```

---

## Component Library

### UI Components (shadcn/ui)

**Buttons:**
```tsx
import { Button } from "@/components/ui/button";

<Button variant="default">Default</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Cancel</Button>
<Button variant="ghost">Ghost</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
```

**Dialogs:**
```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

<Dialog>
  <DialogTrigger asChild>
    <Button>Open</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
      <DialogDescription>Description</DialogDescription>
    </DialogHeader>
    {/* Content */}
  </DialogContent>
</Dialog>
```

**Select Dropdowns:**
```tsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

<Select value={value} onValueChange={setValue}>
  <SelectTrigger>
    <SelectValue placeholder="Select status" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="active">Active</SelectItem>
    <SelectItem value="pending">Pending</SelectItem>
  </SelectContent>
</Select>
```

**Tables:**
```tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Project</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {proposals.map((p) => (
      <TableRow key={p.project_code}>
        <TableCell>{p.project_name}</TableCell>
        <TableCell>{p.current_status}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

**Cards:**
```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
  </CardHeader>
  <CardContent>
    <p>Card content goes here</p>
  </CardContent>
</Card>
```

---

## API Integration

### Current API Endpoints

**Base URL:** `http://localhost:8000`

**Proposals:**
- `GET /api/proposals` - List all proposals
- `GET /api/proposals/{code}` - Get single proposal
- `PUT /api/proposals/{code}` - Update proposal
- `POST /api/proposals` - Create proposal
- `DELETE /api/proposals/{code}` - Delete proposal
- `GET /api/proposals/{code}/history` - Status history

**Emails:**
- `GET /api/emails` - List emails
- `GET /api/emails/{id}` - Get email
- `GET /api/emails/project/{code}` - Emails for project

**Financial:**
- `GET /api/financial/metrics` - Dashboard metrics
- `GET /api/invoices` - List invoices
- `GET /api/invoices/{id}` - Get invoice

**See:** `http://localhost:8000/docs` for full API documentation.

### Error Handling

```tsx
import { useQuery } from "@tanstack/react-query";

export function MyComponent() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["proposals"],
    queryFn: getProposals,
    retry: 3,
    retryDelay: 1000,
  });

  if (isLoading) {
    return <div className="p-6">Loading...</div>;
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-red-600">Error: {error.message}</p>
        <Button onClick={() => refetch()}>Retry</Button>
      </div>
    );
  }

  return <div>{/* Success state */}</div>;
}
```

---

## Common Tasks

### Task 1: Add a Status Badge Component

```tsx
// src/components/proposals/status-badge.tsx
import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const getVariant = (status: string) => {
    switch (status) {
      case "Won":
        return "bg-green-100 text-green-800";
      case "Lost":
        return "bg-red-100 text-red-800";
      case "In Progress":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return <Badge className={getVariant(status)}>{status}</Badge>;
}
```

### Task 2: Format Currency

```tsx
// Add to src/lib/utils.ts
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

// Usage:
import { formatCurrency } from "@/lib/utils";

<p>{formatCurrency(proposal.project_value)}</p>
// Output: "$350,000"
```

### Task 3: Format Dates

```tsx
import { format } from "date-fns";

// Format date
const formattedDate = format(new Date(proposal.first_contact_date), "MMM d, yyyy");
// Output: "Nov 23, 2025"

// Relative time
import { formatDistanceToNow } from "date-fns";

const timeAgo = formatDistanceToNow(new Date(proposal.updated_at), {
  addSuffix: true,
});
// Output: "3 hours ago"
```

### Task 4: Conditional Styling with cn()

```tsx
import { cn } from "@/lib/utils";

<div
  className={cn(
    "p-4 rounded-lg border",
    isActive && "bg-blue-50 border-blue-200",
    isError && "bg-red-50 border-red-200"
  )}
>
  Content
</div>
```

---

## Troubleshooting

### Frontend Won't Start

```bash
# Check if port is in use
lsof -ti:3002

# Kill existing process
lsof -ti:3002 | xargs kill -9

# Clear cache and restart
rm -rf .next node_modules/.cache
npm run dev
```

### Build Errors

```bash
# Type check
npm run type-check

# Check for ESLint errors
npm run lint

# Clear everything and reinstall
rm -rf .next node_modules package-lock.json
npm install
npm run dev
```

### API Connection Issues

```bash
# Check if backend is running
curl http://localhost:8000/api/health

# If not, start backend
cd /path/to/project
python3 -m uvicorn backend.api.main:app --reload

# Check environment variables
cat frontend/.env.local
# Should have: NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Dropdown/Select Not Accepting Input

**Symptom:** User types in dropdown but value resets immediately.

**Cause:** State is being reset on every render (common mistake).

**Fix:** Use `useEffect` to control when state updates:

```tsx
// ❌ WRONG
if (proposal) {
  setFormData({ status: proposal.status });
}

// ✅ CORRECT
useEffect(() => {
  if (proposal) {
    setFormData({ status: proposal.status });
  }
}, [proposal?.id]);
```

**Reference:** See `src/components/proposals/proposal-quick-edit-dialog.tsx:56-67`

### React Query Not Refetching

```tsx
import { useQueryClient } from "@tanstack/react-query";

const queryClient = useQueryClient();

// After mutation, invalidate queries
queryClient.invalidateQueries({ queryKey: ["proposals"] });

// Or refetch specific query
queryClient.refetchQueries({ queryKey: ["proposals", projectCode] });
```

---

## Best Practices

### 1. Component Organization

```tsx
// ✅ Good: Small, focused components
export function ProposalCard({ proposal }) {
  return (
    <Card>
      <ProposalHeader proposal={proposal} />
      <ProposalBody proposal={proposal} />
      <ProposalActions proposal={proposal} />
    </Card>
  );
}

// ❌ Bad: Monolithic 500-line component
export function ProposalCard({ proposal }) {
  // 500 lines of code
}
```

### 2. TypeScript Usage

```tsx
// ✅ Good: Explicit types
interface ProposalCardProps {
  proposal: Proposal;
  onEdit?: (proposal: Proposal) => void;
  className?: string;
}

export function ProposalCard({ proposal, onEdit, className }: ProposalCardProps) {
  // ...
}

// ❌ Bad: Using `any`
export function ProposalCard({ proposal, onEdit }: any) {
  // ...
}
```

### 3. Loading States

```tsx
// ✅ Good: Skeleton loaders
if (isLoading) {
  return <ProposalCardSkeleton />;
}

// ❌ Bad: Generic spinner
if (isLoading) {
  return <div>Loading...</div>;
}
```

### 4. Error Boundaries

```tsx
// ✅ Good: Graceful error handling
if (error) {
  return (
    <Card>
      <CardContent>
        <p className="text-red-600">Failed to load proposals</p>
        <Button onClick={() => refetch()}>Try Again</Button>
      </CardContent>
    </Card>
  );
}
```

### 5. Performance

```tsx
// ✅ Good: Memoize expensive operations
import { useMemo } from "react";

const sortedProposals = useMemo(() => {
  return proposals.sort((a, b) => a.project_value - b.project_value);
}, [proposals]);

// ✅ Good: Virtualize long lists
import { useVirtualizer } from "@tanstack/react-virtual";
```

### 6. Accessibility

```tsx
// ✅ Good: Semantic HTML and ARIA labels
<button
  aria-label="Edit proposal BK-001"
  onClick={handleEdit}
>
  <Edit className="h-4 w-4" />
</button>

// ✅ Good: Keyboard navigation
<Dialog onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>Open</Button>
  </DialogTrigger>
  {/* Dialog handles Esc key and focus trap automatically */}
</Dialog>
```

---

## Resources

**Documentation:**
- [Next.js Docs](https://nextjs.org/docs)
- [React Docs](https://react.dev)
- [TanStack Query](https://tanstack.com/query/latest)
- [shadcn/ui](https://ui.shadcn.com)
- [Tailwind CSS](https://tailwindcss.com/docs)

**Project-Specific:**
- [Backend API Docs](http://localhost:8000/docs)
- [CURRENT_STATUS.md](CURRENT_STATUS.md)
- [README.md](README.md)

---

## Getting Help

**Common Issues:**
1. Check [Troubleshooting](#troubleshooting) section
2. Review [CURRENT_STATUS.md](CURRENT_STATUS.md) for known issues
3. Check backend logs: `tail -f /tmp/bensley_api.log`
4. Check frontend logs in browser console

**Code Patterns:**
- Review existing components in `src/components/`
- Check `src/lib/api.ts` for API call patterns
- Review `src/lib/types.ts` for type definitions

---

**Last Updated:** November 23, 2025

**Version:** 1.0.0 (Next.js 15.1.3)
