"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Clock, DollarSign, FileWarning, CheckCircle2, ClipboardList } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface ProjectException {
  project_code: string;
  project_name: string;
  issues: {
    type: "overdue_invoice" | "overdue_deliverable" | "stale" | "unpaid" | "overdue_action";
    label: string;
    severity: "high" | "medium" | "low";
    value?: number;
    days?: number;
  }[];
}

interface ExceptionsResponse {
  success: boolean;
  exceptions: ProjectException[];
  healthy_count: number;
  total_count: number;
}

export function PortfolioExceptionsWidget() {
  const { data, isLoading, error } = useQuery<ExceptionsResponse>({
    queryKey: ["portfolio-exceptions"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/portfolio-exceptions`);
      if (!res.ok) throw new Error("Failed to fetch");
      return res.json();
    },
    refetchInterval: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Portfolio Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-slate-100 rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Portfolio Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Error loading portfolio data</p>
        </CardContent>
      </Card>
    );
  }

  const exceptions = data?.exceptions || [];
  const healthyCount = data?.healthy_count || 0;
  const totalCount = data?.total_count || 0;

  const getIssueIcon = (type: string) => {
    switch (type) {
      case "overdue_invoice":
      case "unpaid":
        return <DollarSign className="h-3.5 w-3.5" />;
      case "overdue_deliverable":
        return <FileWarning className="h-3.5 w-3.5" />;
      case "stale":
        return <Clock className="h-3.5 w-3.5" />;
      case "overdue_action":
        return <ClipboardList className="h-3.5 w-3.5" />;
      default:
        return <AlertTriangle className="h-3.5 w-3.5" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high":
        return "bg-red-50 text-red-700 border-red-200";
      case "medium":
        return "bg-amber-50 text-amber-700 border-amber-200";
      default:
        return "bg-slate-50 text-slate-600 border-slate-200";
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Portfolio Health
          </CardTitle>
          <div className="flex items-center gap-2">
            {exceptions.length > 0 ? (
              <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                {exceptions.length} need attention
              </Badge>
            ) : (
              <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                All healthy
              </Badge>
            )}
            <Badge variant="outline">
              {healthyCount}/{totalCount} on track
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {exceptions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-emerald-500" />
            <p className="font-medium">All projects on track</p>
            <p className="text-sm">No exceptions to report</p>
          </div>
        ) : (
          <div className="space-y-3">
            {exceptions.slice(0, 8).map((project) => (
              <Link
                key={project.project_code}
                href={`/projects/${encodeURIComponent(project.project_code)}`}
                className="block"
              >
                <div className="p-3 rounded-lg border hover:bg-slate-50 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">
                        {project.project_name || project.project_code}
                      </p>
                      <p className="text-xs text-muted-foreground font-mono">
                        {project.project_code}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-1 justify-end">
                      {project.issues.slice(0, 3).map((issue, idx) => (
                        <Badge
                          key={idx}
                          variant="outline"
                          className={cn("text-xs flex items-center gap-1", getSeverityColor(issue.severity))}
                        >
                          {getIssueIcon(issue.type)}
                          {issue.label}
                        </Badge>
                      ))}
                      {project.issues.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{project.issues.length - 3}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
            {exceptions.length > 8 && (
              <p className="text-xs text-center text-muted-foreground pt-2">
                + {exceptions.length - 8} more projects need attention
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
