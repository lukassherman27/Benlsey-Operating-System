"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { AlertCircle, Clock, CheckCircle, AlertTriangle, X, User, FileText, Calendar, ChevronRight } from "lucide-react";
import { differenceInDays, format } from "date-fns";

interface RFI {
  rfi_id: number;
  project_code: string | null;
  project_title: string | null;
  rfi_number: string | null;
  subject: string | null;
  description?: string | null;
  date_sent: string | null;
  date_due: string | null;
  status: string;
  priority: string;
  days_open: number | null;
  days_overdue: number | null;
  is_overdue: number;
  assigned_pm?: string | null;
}

interface RFIResponse {
  total: number;
  rfis: RFI[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function RFITrackerWidget() {
  const [selectedRFI, setSelectedRFI] = useState<RFI | null>(null);
  const [checklist, setChecklist] = useState({
    reviewed: false,
    responseDrafted: false,
    responseSent: false,
  });

  const { data, isLoading, error } = useQuery<RFIResponse>({
    queryKey: ["rfis-open"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/rfis`);
      if (!res.ok) throw new Error("Failed to fetch RFIs");
      return res.json();
    },
    refetchInterval: 5 * 60 * 1000,
  });

  const openRFIDetail = (rfi: RFI) => {
    setSelectedRFI(rfi);
    // Reset checklist when opening a new RFI
    setChecklist({
      reviewed: false,
      responseDrafted: false,
      responseSent: false,
    });
  };

  const closeRFIDetail = () => {
    setSelectedRFI(null);
  };

  const allChecked = checklist.reviewed && checklist.responseDrafted && checklist.responseSent;

  if (isLoading) {
    return <RFISkeleton />;
  }

  if (error) {
    return (
      <Card className="h-full">
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
    <>
      <Card className="h-full">
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
            <div className="space-y-2">
              {rfis.slice(0, 8).map((rfi) => {
                const dueDate = rfi.date_due ? new Date(rfi.date_due) : null;
                const isOverdue = rfi.is_overdue === 1;
                const daysUntilDue = dueDate ? differenceInDays(dueDate, new Date()) : null;

                return (
                  <div
                    key={rfi.rfi_id}
                    onClick={() => openRFIDetail(rfi)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                      isOverdue
                        ? "bg-red-50 border-red-200 hover:border-red-300"
                        : daysUntilDue !== null && daysUntilDue <= 1
                        ? "bg-yellow-50 border-yellow-200 hover:border-yellow-300"
                        : "bg-gray-50 border-gray-200 hover:border-gray-300"
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
                        <p className="text-xs text-blue-600 font-medium mt-0.5">
                          {rfi.project_title || rfi.project_code}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {rfi.project_code}
                          {rfi.rfi_number && ` • ${rfi.rfi_number}`}
                        </p>
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
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      </div>
                    </div>
                  </div>
                );
              })}
              {rfis.length > 8 && (
                <p className="text-xs text-center text-muted-foreground pt-2">
                  + {rfis.length - 8} more RFIs
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* RFI Detail Modal */}
      <Dialog open={!!selectedRFI} onOpenChange={() => closeRFIDetail()}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-orange-500" />
              RFI Details
            </DialogTitle>
          </DialogHeader>

          {selectedRFI && (
            <div className="space-y-4">
              {/* Project Info */}
              <div className="bg-slate-50 rounded-lg p-4">
                <p className="text-sm text-slate-500">Project</p>
                <p className="font-semibold text-lg">
                  {selectedRFI.project_title || "Unknown Project"}
                </p>
                <p className="text-sm text-slate-600">{selectedRFI.project_code}</p>
              </div>

              {/* RFI Subject */}
              <div>
                <p className="text-sm text-slate-500 mb-1">Subject</p>
                <p className="font-medium">{selectedRFI.subject || "No subject"}</p>
              </div>

              {/* RFI Content/Description */}
              {selectedRFI.description && (
                <div>
                  <p className="text-sm text-slate-500 mb-1">Description</p>
                  <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg">
                    {selectedRFI.description}
                  </p>
                </div>
              )}

              {/* Dates and Status */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500 mb-1 flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    Date Sent
                  </p>
                  <p className="text-sm font-medium">
                    {selectedRFI.date_sent
                      ? format(new Date(selectedRFI.date_sent), "MMM d, yyyy")
                      : "—"}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1 flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    Due Date
                  </p>
                  <p className={`text-sm font-medium ${selectedRFI.is_overdue ? "text-red-600" : ""}`}>
                    {selectedRFI.date_due
                      ? format(new Date(selectedRFI.date_due), "MMM d, yyyy")
                      : "—"}
                    {selectedRFI.is_overdue === 1 && " (Overdue)"}
                  </p>
                </div>
              </div>

              {/* Assigned PM */}
              {selectedRFI.assigned_pm && (
                <div>
                  <p className="text-sm text-slate-500 mb-1 flex items-center gap-1">
                    <User className="h-3.5 w-3.5" />
                    Assigned Project Manager
                  </p>
                  <p className="text-sm font-medium">{selectedRFI.assigned_pm}</p>
                </div>
              )}

              {/* Priority and Status Badges */}
              <div className="flex gap-2">
                <Badge
                  variant={selectedRFI.priority === "high" ? "default" : "outline"}
                  className={selectedRFI.priority === "high" ? "bg-amber-500" : ""}
                >
                  {selectedRFI.priority} priority
                </Badge>
                <Badge variant="outline">{selectedRFI.status}</Badge>
                {selectedRFI.days_open && (
                  <Badge variant="secondary">Open {selectedRFI.days_open} days</Badge>
                )}
              </div>

              {/* To-Do Checklist */}
              <div className="border-t pt-4">
                <p className="text-sm font-semibold mb-3">Action Checklist</p>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <Checkbox
                      checked={checklist.reviewed}
                      onCheckedChange={(checked) =>
                        setChecklist((prev) => ({ ...prev, reviewed: !!checked }))
                      }
                    />
                    <span className={checklist.reviewed ? "line-through text-slate-400" : ""}>
                      Reviewed RFI content
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <Checkbox
                      checked={checklist.responseDrafted}
                      onCheckedChange={(checked) =>
                        setChecklist((prev) => ({ ...prev, responseDrafted: !!checked }))
                      }
                    />
                    <span className={checklist.responseDrafted ? "line-through text-slate-400" : ""}>
                      Response drafted
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <Checkbox
                      checked={checklist.responseSent}
                      onCheckedChange={(checked) =>
                        setChecklist((prev) => ({ ...prev, responseSent: !!checked }))
                      }
                    />
                    <span className={checklist.responseSent ? "line-through text-slate-400" : ""}>
                      Response sent to client
                    </span>
                  </label>
                </div>

                {allChecked && (
                  <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-700 flex items-center gap-2">
                      <CheckCircle className="h-4 w-4" />
                      All tasks complete! Ready to mark RFI as resolved.
                    </p>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={closeRFIDetail}
                >
                  Close
                </Button>
                {allChecked && (
                  <Button className="flex-1 bg-green-600 hover:bg-green-700">
                    Mark as Resolved
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

function RFISkeleton() {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
      </CardHeader>
      <CardContent className="space-y-2">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
        ))}
      </CardContent>
    </Card>
  );
}
