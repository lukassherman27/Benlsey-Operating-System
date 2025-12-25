"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Clock, ChevronDown, ChevronUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ProposalTrackerItem } from "@/lib/types";

interface PriorityBannerProps {
  proposals: ProposalTrackerItem[];
  onFilterOverdue: () => void;
  onFilterMyMove: () => void;
}

export function PriorityBanner({ proposals, onFilterOverdue, onFilterMyMove }: PriorityBannerProps) {
  const router = useRouter();
  const [expanded, setExpanded] = useState(true);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Filter overdue items (action_due is past)
  const overdueItems = proposals.filter((p) => {
    if (!p.action_due) return false;
    const dueDate = new Date(p.action_due);
    return dueDate < today &&
      !["Contract Signed", "Lost", "Declined", "Dormant"].includes(p.current_status);
  });

  // Filter "Your Move" items (Bill's items that aren't overdue)
  const myMoveItems = proposals.filter((p) => {
    if (!p.action_owner) return false;
    const isOverdue = p.action_due && new Date(p.action_due) < today;
    return p.action_owner === "bill" &&
      !isOverdue &&
      !["Contract Signed", "Lost", "Declined", "Dormant"].includes(p.current_status);
  });

  // Don't show banner if nothing needs attention
  if (overdueItems.length === 0 && myMoveItems.length === 0) {
    return null;
  }

  const getDaysOverdue = (dueDate: string) => {
    const due = new Date(dueDate);
    const diff = Math.floor((today.getTime() - due.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  return (
    <Card className="border-0 bg-gradient-to-r from-slate-50 to-slate-100 shadow-sm">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            Today&apos;s Priorities
          </h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="h-6 px-2"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>

        {expanded && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Overdue Section */}
            <div
              className={cn(
                "rounded-lg border-l-4 p-3 bg-white",
                overdueItems.length > 0 ? "border-l-red-500" : "border-l-slate-200"
              )}
            >
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className={cn(
                  "h-4 w-4",
                  overdueItems.length > 0 ? "text-red-500" : "text-slate-400"
                )} />
                <span className="text-sm font-semibold text-slate-700">
                  Overdue ({overdueItems.length})
                </span>
              </div>

              {overdueItems.length === 0 ? (
                <p className="text-sm text-slate-500">All caught up!</p>
              ) : (
                <div className="space-y-2">
                  {overdueItems.slice(0, 3).map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between text-sm cursor-pointer hover:bg-slate-50 rounded p-1 -m-1"
                      onClick={() => router.push(`/proposals/${encodeURIComponent(item.project_code)}`)}
                    >
                      <div className="truncate flex-1">
                        <span className="font-medium text-slate-900">{item.project_name}</span>
                      </div>
                      <span className="text-red-600 font-medium text-xs ml-2 whitespace-nowrap">
                        {getDaysOverdue(item.action_due!)}d late
                      </span>
                    </div>
                  ))}
                  {overdueItems.length > 3 && (
                    <Button
                      variant="link"
                      size="sm"
                      className="h-auto p-0 text-red-600"
                      onClick={onFilterOverdue}
                    >
                      View all {overdueItems.length} overdue
                    </Button>
                  )}
                </div>
              )}
            </div>

            {/* Your Move Section */}
            <div
              className={cn(
                "rounded-lg border-l-4 p-3 bg-white",
                myMoveItems.length > 0 ? "border-l-amber-500" : "border-l-slate-200"
              )}
            >
              <div className="flex items-center gap-2 mb-2">
                <Clock className={cn(
                  "h-4 w-4",
                  myMoveItems.length > 0 ? "text-amber-500" : "text-slate-400"
                )} />
                <span className="text-sm font-semibold text-slate-700">
                  Your Move ({myMoveItems.length})
                </span>
              </div>

              {myMoveItems.length === 0 ? (
                <p className="text-sm text-slate-500">Nothing pending for you</p>
              ) : (
                <div className="space-y-2">
                  {myMoveItems.slice(0, 3).map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between text-sm cursor-pointer hover:bg-slate-50 rounded p-1 -m-1"
                      onClick={() => router.push(`/proposals/${encodeURIComponent(item.project_code)}`)}
                    >
                      <div className="truncate flex-1">
                        <span className="font-medium text-slate-900">{item.project_name}</span>
                      </div>
                      <span className="text-amber-600 text-xs ml-2 truncate max-w-[120px]">
                        {item.action_needed || "Needs action"}
                      </span>
                    </div>
                  ))}
                  {myMoveItems.length > 3 && (
                    <Button
                      variant="link"
                      size="sm"
                      className="h-auto p-0 text-amber-600"
                      onClick={onFilterMyMove}
                    >
                      View all {myMoveItems.length} items
                    </Button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
