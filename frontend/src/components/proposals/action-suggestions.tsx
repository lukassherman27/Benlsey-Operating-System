"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Zap,
  Mail,
  Calendar,
  Phone,
  FileText,
  ChevronRight,
  Sparkles,
  Clock,
} from "lucide-react";

interface ActionItem {
  id: string;
  priority: number;
  type: "email" | "meeting" | "call" | "document" | "update";
  title: string;
  reason: string;
  cta: string;
  ctaAction?: () => void;
}

interface ActionSuggestionsProps {
  actions: ActionItem[];
  className?: string;
}

const actionIcons = {
  email: Mail,
  meeting: Calendar,
  call: Phone,
  document: FileText,
  update: Clock,
};

const actionColors = {
  email: "bg-blue-100 text-blue-700",
  meeting: "bg-purple-100 text-purple-700",
  call: "bg-green-100 text-green-700",
  document: "bg-amber-100 text-amber-700",
  update: "bg-slate-100 text-slate-700",
};

export function ActionSuggestions({
  actions,
  className,
}: ActionSuggestionsProps) {
  if (actions.length === 0) {
    return null;
  }

  // Sort by priority (lower number = higher priority)
  const sortedActions = [...actions].sort((a, b) => a.priority - b.priority);

  return (
    <div
      className={cn(
        "rounded-xl border border-teal-200 bg-gradient-to-br from-teal-50 to-white p-4",
        className
      )}
    >
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-lg bg-teal-100">
          <Zap className="h-4 w-4 text-teal-700" />
        </div>
        <h3 className="font-semibold text-slate-800">Suggested Actions</h3>
        <Badge variant="outline" className="text-xs text-teal-700 border-teal-300">
          <Sparkles className="h-3 w-3 mr-1" />
          AI
        </Badge>
      </div>

      <div className="space-y-3">
        {sortedActions.map((action, index) => {
          const Icon = actionIcons[action.type] || Clock;
          const colorClass = actionColors[action.type] || actionColors.update;

          return (
            <div
              key={action.id}
              className={cn(
                "group p-3 rounded-lg border bg-white hover:shadow-sm transition-all",
                index === 0 && "border-teal-300 shadow-sm"
              )}
            >
              <div className="flex items-start gap-3">
                {/* Priority Number + Icon */}
                <div className="flex flex-col items-center gap-1">
                  <span
                    className={cn(
                      "text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center",
                      index === 0
                        ? "bg-teal-600 text-white"
                        : "bg-slate-200 text-slate-600"
                    )}
                  >
                    {index + 1}
                  </span>
                  <div className={cn("p-1.5 rounded-lg", colorClass)}>
                    <Icon className="h-3.5 w-3.5" />
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-slate-800">
                    {action.title}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">{action.reason}</p>
                </div>

                {/* CTA */}
                <Button
                  size="sm"
                  variant={index === 0 ? "default" : "ghost"}
                  className={cn(
                    "shrink-0 text-xs",
                    index === 0 && "bg-teal-600 hover:bg-teal-700"
                  )}
                  onClick={action.ctaAction}
                >
                  {action.cta}
                  <ChevronRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Helper function to generate action suggestions from proposal data
export function generateActionSuggestions(proposal: {
  project_code: string;
  ball_in_court?: string | null;
  days_since_contact?: number | null;
  waiting_for?: string | null;
  next_action?: string | null;
  status?: string | null;
  primary_contact_name?: string | null;
  primary_contact_email?: string | null;
}): ActionItem[] {
  const actions: ActionItem[] = [];
  const days = proposal.days_since_contact ?? 0;
  const ballInCourt = (proposal.ball_in_court || "mutual").toLowerCase();

  // Priority 1: Follow-up if ball is with us and overdue
  if (ballInCourt === "us" && days > 7) {
    actions.push({
      id: "follow-up-email",
      priority: 1,
      type: "email",
      title: `Send follow-up email${proposal.primary_contact_name ? ` to ${proposal.primary_contact_name}` : ""}`,
      reason: `${days} days since last contact`,
      cta: "Draft Email",
    });
  }

  // Priority 2: Schedule meeting if waiting for response
  if (ballInCourt === "them" && days > 10) {
    actions.push({
      id: "schedule-meeting",
      priority: 2,
      type: "meeting",
      title: "Schedule check-in meeting",
      reason: proposal.waiting_for || "Awaiting client response",
      cta: "Schedule",
    });
  }

  // Priority 3: Quick check-in call
  if (days > 14 && days < 30) {
    actions.push({
      id: "check-in-call",
      priority: 3,
      type: "call",
      title: "Quick phone check-in",
      reason: "Re-establish communication cadence",
      cta: "Log Call",
    });
  }

  // Priority 4: Update proposal status
  if (days > 30 || proposal.status === "stalled") {
    actions.push({
      id: "update-status",
      priority: 4,
      type: "update",
      title: "Review and update proposal status",
      reason: days > 30 ? "Over a month without contact" : "Marked as stalled",
      cta: "Update",
    });
  }

  // Priority 5: Document next steps
  if (!proposal.next_action) {
    actions.push({
      id: "document-next",
      priority: 5,
      type: "document",
      title: "Define clear next steps",
      reason: "No next action documented",
      cta: "Add Steps",
    });
  }

  return actions.slice(0, 4); // Limit to top 4 actions
}
