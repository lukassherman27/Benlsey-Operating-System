"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertCircle, Clock, CheckCircle, ExternalLink, AlertTriangle } from "lucide-react";
import { differenceInDays, format } from "date-fns";

interface RFI {
  rfi_id: number;
  project_code: string | null;
  project_title: string | null;
  rfi_number: string | null;
  subject: string | null;
  date_sent: string | null;
  date_due: string | null;
  status: string;
  priority: string;
  days_open: number | null;
  days_overdue: number | null;
  is_overdue: number;
}

interface RFIResponse {
  total: number;
  rfis: RFI[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function RFITrackerWidget() {
  const { data, isLoading, error } = useQuery<RFIResponse>({
    queryKey: ["rfis-open"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/rfis`);
      if (!res.ok) throw new Error("Failed to fetch RFIs");
      return res.json();
    },
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });

  if (isLoading) {
    return <RFISkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-orange-500" />
            Open RFIs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Error loading RFIs</p>
        </CardContent>
      </Card>
    );
  }

  const rfis = data?.rfis || [];
  const overdueCount = rfis.filter((rfi) => rfi.is_overdue === 1).length;
  const highPriorityCount = rfis.filter((rfi) => rfi.priority === "high").length;

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
          {highPriorityCount > 0 && (
            <Badge className="bg-amber-500">{highPriorityCount} high priority</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {rfis.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
            <p>No open RFIs</p>
            <p className="text-xs mt-1">All requests have been addressed</p>
          </div>
        ) : (
          <div className="space-y-3">
            {rfis.slice(0, 10).map((rfi) => {
              const dueDate = rfi.date_due ? new Date(rfi.date_due) : null;
              const isOverdue = rfi.is_overdue === 1;
              const daysUntilDue = dueDate ? differenceInDays(dueDate, new Date()) : null;

              return (
                <div
                  key={rfi.rfi_id}
                  className={`p-3 rounded-lg border ${
                    isOverdue
                      ? "bg-red-50 border-red-200"
                      : daysUntilDue !== null && daysUntilDue <= 1
                      ? "bg-yellow-50 border-yellow-200"
                      : "bg-gray-50 border-gray-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-sm truncate">
                          {rfi.subject || "Untitled RFI"}
                        </p>
                        {rfi.priority === "high" && (
                          <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0" />
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {rfi.project_code}
                        {rfi.rfi_number && ` - ${rfi.rfi_number}`}
                      </p>
                      {rfi.project_title && (
                        <p className="text-xs text-blue-600 mt-0.5 truncate">
                          {rfi.project_title}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {dueDate && (
                        <span
                          className={`text-xs flex items-center gap-1 ${
                            isOverdue ? "text-red-600 font-medium" : "text-muted-foreground"
                          }`}
                        >
                          <Clock className="h-3 w-3" />
                          {isOverdue
                            ? `${rfi.days_overdue || Math.abs(daysUntilDue!)}d overdue`
                            : daysUntilDue === 0
                            ? "Due today"
                            : daysUntilDue === 1
                            ? "Due tomorrow"
                            : `${daysUntilDue}d left`}
                        </span>
                      )}
                      <Badge
                        variant={rfi.priority === "high" ? "default" : "outline"}
                        className={`text-xs ${
                          rfi.priority === "high" ? "bg-amber-500 hover:bg-amber-600" : ""
                        }`}
                      >
                        {rfi.priority}
                      </Badge>
                    </div>
                  </div>
                  {rfi.days_open && rfi.days_open > 3 && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Open for {rfi.days_open} days
                    </p>
                  )}
                </div>
              );
            })}
            {rfis.length > 10 && (
              <p className="text-xs text-center text-muted-foreground pt-2">
                + {rfis.length - 10} more RFIs
              </p>
            )}
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
