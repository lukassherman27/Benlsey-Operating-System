"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { AlertTriangle, Clock, CheckCircle, Mail, ArrowRight } from "lucide-react";

interface NextActionCardProps {
  actionNeeded: string | null;
  actionDue: string | null;
  actionOwner: string | null;
  projectCode: string;
  primaryContactEmail?: string | null;
}

export function NextActionCard({
  actionNeeded,
  actionDue,
  actionOwner,
  primaryContactEmail,
}: NextActionCardProps) {
  if (!actionNeeded) {
    return null;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const dueDate = actionDue ? new Date(actionDue) : null;
  const isOverdue = dueDate && dueDate < today;
  const isDueSoon = dueDate && !isOverdue &&
    (dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24) <= 3;

  const getDaysLabel = () => {
    if (!dueDate) return null;
    const diffDays = Math.ceil((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return `${Math.abs(diffDays)} days overdue`;
    if (diffDays === 0) return "Due today";
    if (diffDays === 1) return "Due tomorrow";
    return `Due in ${diffDays} days`;
  };

  const handleDraftEmail = () => {
    if (primaryContactEmail) {
      window.location.href = `mailto:${primaryContactEmail}`;
    }
  };

  return (
    <Card
      className={cn(
        "border-2 shadow-md",
        isOverdue ? "border-red-300 bg-red-50/50" :
        isDueSoon ? "border-amber-300 bg-amber-50/50" :
        "border-blue-200 bg-blue-50/30"
      )}
    >
      <CardContent className="p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2">
              {isOverdue ? (
                <AlertTriangle className="h-5 w-5 text-red-500" />
              ) : isDueSoon ? (
                <Clock className="h-5 w-5 text-amber-500" />
              ) : (
                <CheckCircle className="h-5 w-5 text-blue-500" />
              )}
              <span
                className={cn(
                  "text-xs font-semibold uppercase tracking-wide",
                  isOverdue ? "text-red-600" :
                  isDueSoon ? "text-amber-600" :
                  "text-blue-600"
                )}
              >
                Next Action
              </span>
            </div>

            <p className={cn(
              "text-lg font-medium",
              isOverdue ? "text-red-900" :
              isDueSoon ? "text-amber-900" :
              "text-slate-900"
            )}>
              {actionNeeded}
            </p>

            <div className="flex items-center gap-4 text-sm">
              {dueDate && (
                <span
                  className={cn(
                    "font-medium",
                    isOverdue ? "text-red-600" :
                    isDueSoon ? "text-amber-600" :
                    "text-slate-500"
                  )}
                >
                  {getDaysLabel()} ({dueDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })})
                </span>
              )}
              {actionOwner && (
                <span className="text-slate-400">
                  Owner: {actionOwner.charAt(0).toUpperCase() + actionOwner.slice(1)}
                </span>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            {primaryContactEmail && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleDraftEmail}
                className={cn(
                  isOverdue ? "border-red-300 text-red-700 hover:bg-red-100" :
                  isDueSoon ? "border-amber-300 text-amber-700 hover:bg-amber-100" :
                  "border-blue-300 text-blue-700 hover:bg-blue-100"
                )}
              >
                <Mail className="h-4 w-4 mr-2" />
                Draft Email
              </Button>
            )}
            <Button
              size="sm"
              className={cn(
                isOverdue ? "bg-red-600 hover:bg-red-700" :
                isDueSoon ? "bg-amber-600 hover:bg-amber-700" :
                "bg-blue-600 hover:bg-blue-700"
              )}
            >
              Mark Done
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
