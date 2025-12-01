# Agent 2: Frontend Dashboard Development

**Role:** Build dashboard components and pages for the BDS Operations Platform
**Owner:** All files in `frontend/src/`
**Do NOT touch:** `backend/`, `voice_transcriber/`, `scripts/`, database files

---

## Context

You are building React/Next.js 15 components with TypeScript. The frontend uses:
- **Framework:** Next.js 15 (App Router)
- **Styling:** Tailwind CSS + shadcn/ui components
- **State:** React Query for API calls
- **Location:** `frontend/src/`

**Read these files FIRST:**
1. `CLAUDE.md` - Project context
2. `.claude/CODEBASE_INDEX.md` - Where things live
3. `frontend/src/app/(dashboard)/page.tsx` - Main dashboard structure
4. `frontend/src/components/dashboard/` - Existing widgets

---

## Your Tasks (Priority Order)

### P0: Unified Timeline Component (Do First)

**Wait for:** Agent 1 to complete `/api/projects/{code}/unified-timeline` endpoint

**Create file:** `frontend/src/components/project/unified-timeline.tsx`

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Mail, Mic, AlertCircle, DollarSign, Flag,
  ChevronDown, ChevronRight, Calendar
} from "lucide-react";
import { useState } from "react";
import { format } from "date-fns";

interface TimelineEvent {
  type: "email" | "meeting" | "rfi" | "invoice" | "milestone";
  date: string;
  title: string;
  summary: string;
  data: Record<string, any>;
  id: number;
}

interface UnifiedTimelineProps {
  projectCode: string;
  limit?: number;
}

const EVENT_ICONS = {
  email: Mail,
  meeting: Mic,
  rfi: AlertCircle,
  invoice: DollarSign,
  milestone: Flag,
};

const EVENT_COLORS = {
  email: "bg-blue-100 text-blue-700 border-blue-200",
  meeting: "bg-purple-100 text-purple-700 border-purple-200",
  rfi: "bg-orange-100 text-orange-700 border-orange-200",
  invoice: "bg-green-100 text-green-700 border-green-200",
  milestone: "bg-gray-100 text-gray-700 border-gray-200",
};

export function UnifiedTimeline({ projectCode, limit = 20 }: UnifiedTimelineProps) {
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const { data, isLoading, error } = useQuery({
    queryKey: ["unified-timeline", projectCode, typeFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (typeFilter !== "all") params.set("types", typeFilter);

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/projects/${encodeURIComponent(projectCode)}/unified-timeline?${params}`
      );
      if (!res.ok) throw new Error("Failed to fetch timeline");
      return res.json();
    },
  });

  const toggleExpanded = (eventId: string) => {
    const newExpanded = new Set(expandedEvents);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedEvents(newExpanded);
  };

  if (isLoading) {
    return <TimelineSkeleton />;
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <p className="text-red-600">Failed to load timeline</p>
        </CardContent>
      </Card>
    );
  }

  const events: TimelineEvent[] = data?.events || [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Project Timeline
        </CardTitle>
        <div className="flex gap-2">
          {["all", "email", "meeting", "rfi", "invoice"].map((type) => (
            <Badge
              key={type}
              variant={typeFilter === type ? "default" : "outline"}
              className="cursor-pointer capitalize"
              onClick={() => setTypeFilter(type)}
            >
              {type}
            </Badge>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">
            No events found for this project
          </p>
        ) : (
          <div className="space-y-4">
            {events.map((event) => {
              const Icon = EVENT_ICONS[event.type] || Mail;
              const colorClass = EVENT_COLORS[event.type] || EVENT_COLORS.email;
              const eventKey = `${event.type}-${event.id}`;
              const isExpanded = expandedEvents.has(eventKey);

              return (
                <div
                  key={eventKey}
                  className={`border rounded-lg p-4 ${colorClass} transition-all duration-200 hover:shadow-md`}
                >
                  <div
                    className="flex items-start gap-3 cursor-pointer"
                    onClick={() => toggleExpanded(eventKey)}
                  >
                    <div className="mt-1">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </div>
                    <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-medium truncate">{event.title}</p>
                        <span className="text-xs opacity-75 flex-shrink-0">
                          {format(new Date(event.date), "MMM d, yyyy h:mm a")}
                        </span>
                      </div>
                      <p className="text-sm opacity-90 mt-1 line-clamp-2">
                        {event.summary}
                      </p>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-current/20">
                      <EventDetails event={event} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EventDetails({ event }: { event: TimelineEvent }) {
  switch (event.type) {
    case "meeting":
      return (
        <div className="space-y-3">
          <div>
            <p className="text-xs font-medium opacity-75">Full Summary</p>
            <p className="text-sm">{event.data.summary}</p>
          </div>
          {event.data.key_points && (
            <div>
              <p className="text-xs font-medium opacity-75">Key Points</p>
              <ul className="list-disc list-inside text-sm">
                {JSON.parse(event.data.key_points || "[]").map((point: string, i: number) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
          )}
          {event.data.action_items && (
            <div>
              <p className="text-xs font-medium opacity-75">Action Items</p>
              <ul className="list-disc list-inside text-sm">
                {JSON.parse(event.data.action_items || "[]").map((item: any, i: number) => (
                  <li key={i}>
                    {item.task}
                    {item.owner && <span className="opacity-75"> - {item.owner}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="flex gap-4 text-xs opacity-75">
            <span>Type: {event.data.meeting_type}</span>
            <span>Confidence: {Math.round((event.data.match_confidence || 0) * 100)}%</span>
          </div>
        </div>
      );

    case "email":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs">
            <span><strong>From:</strong> {event.data.sender_email}</span>
            <span><strong>To:</strong> {event.data.recipient_email}</span>
          </div>
          {event.data.body_preview && (
            <p className="text-sm whitespace-pre-wrap">{event.data.body_preview}</p>
          )}
        </div>
      );

    case "rfi":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs">
            <span><strong>Status:</strong> {event.data.status}</span>
            <span><strong>Due:</strong> {event.data.date_due || "Not set"}</span>
            <span><strong>Priority:</strong> {event.data.priority || "Normal"}</span>
          </div>
          {event.data.description && (
            <p className="text-sm">{event.data.description}</p>
          )}
        </div>
      );

    case "invoice":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs">
            <span><strong>Amount:</strong> ${event.data.amount?.toLocaleString()}</span>
            <span><strong>Status:</strong> {event.data.paid ? "Paid" : "Outstanding"}</span>
            <span><strong>Invoice #:</strong> {event.data.invoice_number}</span>
          </div>
        </div>
      );

    default:
      return (
        <pre className="text-xs overflow-auto">
          {JSON.stringify(event.data, null, 2)}
        </pre>
      );
  }
}

function TimelineSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-6 w-40 bg-gray-200 rounded animate-pulse" />
      </CardHeader>
      <CardContent className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-gray-100 rounded animate-pulse" />
        ))}
      </CardContent>
    </Card>
  );
}
```

---

### P0: Meeting Transcript Viewer (Do Second)

**Create file:** `frontend/src/components/project/transcript-viewer.tsx`

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Mic, Clock, Users, Target, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { format } from "date-fns";

interface TranscriptViewerProps {
  transcriptId: number;
  compact?: boolean;
}

export function TranscriptViewer({ transcriptId, compact = false }: TranscriptViewerProps) {
  const [showFullTranscript, setShowFullTranscript] = useState(false);

  const { data: transcript, isLoading } = useQuery({
    queryKey: ["transcript", transcriptId],
    queryFn: async () => {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/meeting-transcripts/${transcriptId}`
      );
      if (!res.ok) throw new Error("Failed to fetch transcript");
      return res.json();
    },
  });

  if (isLoading) {
    return <TranscriptSkeleton />;
  }

  if (!transcript) {
    return null;
  }

  const keyPoints = JSON.parse(transcript.key_points || "[]");
  const actionItems = JSON.parse(transcript.action_items || "[]");
  const participants = JSON.parse(transcript.participants || "[]");

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5 text-purple-600" />
            {transcript.audio_filename}
          </CardTitle>
          <div className="flex gap-2">
            <Badge variant="outline">{transcript.meeting_type}</Badge>
            <Badge
              variant={transcript.match_confidence > 0.7 ? "default" : "secondary"}
            >
              {Math.round((transcript.match_confidence || 0) * 100)}% match
            </Badge>
          </div>
        </div>
        <div className="flex gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            {transcript.processed_date && format(new Date(transcript.processed_date), "MMM d, yyyy")}
          </span>
          {transcript.detected_project_code && (
            <span>Project: {transcript.detected_project_code}</span>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Summary */}
        <div>
          <h4 className="font-medium mb-2">Summary</h4>
          <p className="text-sm text-muted-foreground">{transcript.summary}</p>
        </div>

        {/* Participants */}
        {participants.length > 0 && (
          <div>
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Users className="h-4 w-4" />
              Participants
            </h4>
            <div className="flex flex-wrap gap-2">
              {participants.map((p: any, i: number) => (
                <Badge key={i} variant="outline">
                  {typeof p === "string" ? p : p.name}
                  {p.type && <span className="ml-1 opacity-50">({p.type})</span>}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Key Points */}
        {keyPoints.length > 0 && (
          <div>
            <h4 className="font-medium mb-2">Key Points</h4>
            <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
              {keyPoints.map((point: string, i: number) => (
                <li key={i}>{point}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Items */}
        {actionItems.length > 0 && (
          <div>
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Target className="h-4 w-4" />
              Action Items ({actionItems.length})
            </h4>
            <div className="space-y-2">
              {actionItems.map((item: any, i: number) => (
                <div
                  key={i}
                  className="flex items-start gap-2 p-2 bg-orange-50 border border-orange-200 rounded"
                >
                  <input type="checkbox" className="mt-1" />
                  <div>
                    <p className="text-sm font-medium">{item.task}</p>
                    <p className="text-xs text-muted-foreground">
                      {item.owner && <span>Owner: {item.owner}</span>}
                      {item.deadline && <span> • Due: {item.deadline}</span>}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Full Transcript Toggle */}
        {!compact && transcript.transcript && (
          <div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFullTranscript(!showFullTranscript)}
              className="w-full"
            >
              {showFullTranscript ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-2" />
                  Hide Full Transcript
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-2" />
                  Show Full Transcript
                </>
              )}
            </Button>
            {showFullTranscript && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg max-h-96 overflow-y-auto">
                <pre className="text-sm whitespace-pre-wrap font-sans">
                  {transcript.transcript}
                </pre>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TranscriptSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="h-20 bg-gray-100 rounded animate-pulse" />
        <div className="h-16 bg-gray-100 rounded animate-pulse" />
      </CardContent>
    </Card>
  );
}
```

---

### P1: RFI Tracker Widget

**Create file:** `frontend/src/components/dashboard/rfi-tracker-widget.tsx`

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertCircle, Clock, CheckCircle, ExternalLink } from "lucide-react";
import { format, differenceInDays } from "date-fns";

export function RFITrackerWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ["rfis-open"],
    queryFn: async () => {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/rfis?status=open&limit=10`
      );
      if (!res.ok) throw new Error("Failed to fetch RFIs");
      return res.json();
    },
  });

  if (isLoading) {
    return <RFISkeleton />;
  }

  const rfis = data?.rfis || [];
  const overdueCount = rfis.filter((rfi: any) => {
    if (!rfi.date_due) return false;
    return new Date(rfi.date_due) < new Date();
  }).length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-orange-500" />
          Open RFIs
        </CardTitle>
        <div className="flex gap-2">
          <Badge variant="outline">{rfis.length} open</Badge>
          {overdueCount > 0 && (
            <Badge variant="destructive">{overdueCount} overdue</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {rfis.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
            <p>No open RFIs</p>
          </div>
        ) : (
          <div className="space-y-3">
            {rfis.map((rfi: any) => {
              const dueDate = rfi.date_due ? new Date(rfi.date_due) : null;
              const isOverdue = dueDate && dueDate < new Date();
              const daysUntilDue = dueDate ? differenceInDays(dueDate, new Date()) : null;

              return (
                <div
                  key={rfi.rfi_id}
                  className={`p-3 rounded-lg border ${
                    isOverdue
                      ? "bg-red-50 border-red-200"
                      : daysUntilDue !== null && daysUntilDue <= 3
                      ? "bg-yellow-50 border-yellow-200"
                      : "bg-gray-50 border-gray-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">
                        {rfi.subject || "Untitled RFI"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {rfi.project_code}
                        {rfi.rfi_number && ` • #${rfi.rfi_number}`}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {dueDate && (
                        <span
                          className={`text-xs flex items-center gap-1 ${
                            isOverdue ? "text-red-600" : "text-muted-foreground"
                          }`}
                        >
                          <Clock className="h-3 w-3" />
                          {isOverdue
                            ? `${Math.abs(daysUntilDue!)}d overdue`
                            : `${daysUntilDue}d left`}
                        </span>
                      )}
                      <Button size="sm" variant="ghost" className="h-6 w-6 p-0">
                        <ExternalLink className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RFISkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
      </CardHeader>
      <CardContent className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
        ))}
      </CardContent>
    </Card>
  );
}
```

---

### P1: Milestones Widget

**Create file:** `frontend/src/components/dashboard/milestones-widget.tsx`

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Flag, Calendar, CheckCircle } from "lucide-react";
import { format, differenceInDays } from "date-fns";

export function MilestonesWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ["milestones-upcoming"],
    queryFn: async () => {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/milestones?upcoming_days=14&limit=10`
      );
      if (!res.ok) throw new Error("Failed to fetch milestones");
      return res.json();
    },
  });

  if (isLoading) {
    return <MilestonesSkeleton />;
  }

  const milestones = data?.milestones || [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Flag className="h-5 w-5 text-blue-500" />
          Upcoming Milestones
        </CardTitle>
        <Badge variant="outline">{milestones.length} in 14 days</Badge>
      </CardHeader>
      <CardContent>
        {milestones.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Calendar className="h-12 w-12 mx-auto mb-2 text-gray-400" />
            <p>No upcoming milestones</p>
            <p className="text-xs mt-1">
              (Milestone dates may need to be added)
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {milestones.map((milestone: any) => {
              const dueDate = milestone.planned_date
                ? new Date(milestone.planned_date)
                : null;
              const daysUntil = dueDate
                ? differenceInDays(dueDate, new Date())
                : null;

              return (
                <div
                  key={milestone.milestone_id}
                  className={`p-3 rounded-lg border ${
                    daysUntil !== null && daysUntil <= 3
                      ? "bg-orange-50 border-orange-200"
                      : "bg-gray-50 border-gray-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm">
                        {milestone.milestone_name || milestone.phase}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {milestone.project_code}
                      </p>
                    </div>
                    {dueDate && (
                      <Badge
                        variant={daysUntil! <= 3 ? "default" : "outline"}
                        className="flex-shrink-0"
                      >
                        {format(dueDate, "MMM d")}
                      </Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MilestonesSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-6 w-40 bg-gray-200 rounded animate-pulse" />
      </CardHeader>
      <CardContent className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
        ))}
      </CardContent>
    </Card>
  );
}
```

---

### P2: Integrate into Projects Page

**Edit file:** `frontend/src/app/(dashboard)/projects/page.tsx`

Add the new widgets to the projects page:

```typescript
import { RFITrackerWidget } from "@/components/dashboard/rfi-tracker-widget";
import { MilestonesWidget } from "@/components/dashboard/milestones-widget";

// In the page layout, add a sidebar or row with:
<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
  <RFITrackerWidget />
  <MilestonesWidget />
</div>
```

---

### P2: Add Unified Timeline to Project Detail

**Edit file:** `frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx`

```typescript
import { UnifiedTimeline } from "@/components/project/unified-timeline";

// Add to the page:
<UnifiedTimeline projectCode={projectCode} />
```

---

## File Structure Reference

```
frontend/src/
├── app/
│   └── (dashboard)/
│       ├── page.tsx              # Main dashboard
│       ├── tracker/page.tsx      # Proposal tracker (done)
│       ├── projects/
│       │   ├── page.tsx          # Projects list (edit)
│       │   └── [projectCode]/page.tsx  # Project detail (edit)
│       └── finance/page.tsx      # Finance (has hardcoded values)
├── components/
│   ├── dashboard/
│   │   ├── rfi-tracker-widget.tsx    # NEW
│   │   ├── milestones-widget.tsx     # NEW
│   │   └── ... existing widgets
│   ├── project/
│   │   ├── unified-timeline.tsx      # NEW
│   │   └── transcript-viewer.tsx     # NEW
│   └── ui/                           # shadcn components (don't edit)
└── lib/
    └── api.ts                    # API helpers (if needed)
```

---

## Testing

```bash
# Run dev server
cd frontend && npm run dev

# Open http://localhost:3002

# Test each component renders without errors
# Check browser console for API errors
```

---

## When You're Done

1. Test all components with real API data
2. Ensure no TypeScript errors (`npm run build`)
3. Update `.claude/CODEBASE_INDEX.md` with new components
4. Tell coordinator that frontend is ready for deployment

---

## Do NOT

- Touch backend files
- Modify shadcn/ui components in `components/ui/`
- Add new npm packages without asking
- Change the API URL structure

---

**Estimated Time:** 10-12 hours total
**Start:** Wait for Agent 1's meeting transcript API, then begin
**Checkpoint:** After unified-timeline component works
