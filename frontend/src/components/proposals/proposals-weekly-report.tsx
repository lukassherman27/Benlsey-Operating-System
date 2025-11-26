"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TrendingUp, AlertCircle, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";
import { format } from "date-fns";

export default function ProposalsWeeklyReport() {
  const [days, setDays] = useState(7);

  const weeklyChangesQuery = useQuery({
    queryKey: ["proposal-weekly-changes", days],
    queryFn: () => api.getProposalWeeklyChanges(days),
    staleTime: 1000 * 60 * 10,
  });

  const weeklyData = useMemo(() => {
    return weeklyChangesQuery.data ?? null;
  }, [weeklyChangesQuery.data]);

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { variant: "default" | "destructive" | "outline" | "secondary"; label: string }> = {
      sent: { variant: "outline", label: "Sent" },
      waiting: { variant: "secondary", label: "Waiting" },
      won: { variant: "default", label: "Won" },
      lost: { variant: "destructive", label: "Lost" },
      active_project: { variant: "default", label: "Active" },
      signed: { variant: "default", label: "Signed" },
    };
    const mapped = statusMap[status.toLowerCase()] || {
      variant: "outline" as const,
      label: status,
    };
    return <Badge variant={mapped.variant}>{mapped.label}</Badge>;
  };

  if (weeklyChangesQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (weeklyChangesQuery.isError) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <p className="text-red-700">
            Error loading weekly proposal changes. Please try again later.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!weeklyData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-gray-600">No proposal data available.</p>
        </CardContent>
      </Card>
    );
  }

  const periodStart = new Date(
    new Date().getTime() - days * 24 * 60 * 60 * 1000
  );
  const periodEnd = new Date();

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Weekly Proposal Report</h2>
          <p className="text-sm text-gray-600">
            {format(periodStart, "MMM d")} - {format(periodEnd, "MMM d, yyyy")}
          </p>
        </div>
        <Select value={String(days)} onValueChange={(v) => setDays(Number(v))}>
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="14">Last 14 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              New Proposals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {weeklyData.summary.new_proposals}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Status Changes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {weeklyData.summary.status_changes}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Won Proposals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {weeklyData.summary.won_proposals}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Stalled
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {weeklyData.summary.stalled_proposals}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* New Proposals Section */}
      {weeklyData.new_proposals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              New Proposals ({weeklyData.new_proposals.length})
            </CardTitle>
            <CardDescription>
              {weeklyData.new_proposals.length} new proposal
              {weeklyData.new_proposals.length !== 1 ? "s" : ""} entered the
              pipeline
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Client</TableHead>
                    <TableHead>Project</TableHead>
                    <TableHead>Fee</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Days Since Contact</TableHead>
                    <TableHead>Next Action</TableHead>
                    <TableHead>Health</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {weeklyData.new_proposals.map((proposal) => (
                    <TableRow key={proposal.proposal_id}>
                      <TableCell className="font-medium">
                        {proposal.client_company}
                      </TableCell>
                      <TableCell>{proposal.project_name}</TableCell>
                      <TableCell>
                        ${(proposal.fee || 0).toLocaleString()}
                      </TableCell>
                      <TableCell>{getStatusBadge(proposal.status || "")}</TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>-</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status Changes Section */}
      {weeklyData.status_changes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              Status Changes ({weeklyData.status_changes.length})
            </CardTitle>
            <CardDescription>
              Proposals that moved through the pipeline
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Client</TableHead>
                    <TableHead>Project</TableHead>
                    <TableHead>From Status</TableHead>
                    <TableHead>To Status</TableHead>
                    <TableHead>Fee</TableHead>
                    <TableHead>Last Contact</TableHead>
                    <TableHead>Next Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {weeklyData.status_changes.map((change) => (
                    <TableRow key={`${change.project_code}-${change.changed_date}`}>
                      <TableCell className="font-medium">
                        {change.client_company}
                      </TableCell>
                      <TableCell>{change.project_name}</TableCell>
                      <TableCell>{getStatusBadge(change.previous_status)}</TableCell>
                      <TableCell>{getStatusBadge(change.new_status)}</TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>-</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stalled Proposals Section */}
      {weeklyData.stalled_proposals.length > 0 && (
        <Card className="border-yellow-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-700">
              <AlertCircle className="h-5 w-5" />
              Stalled Proposals ({weeklyData.stalled_proposals.length})
            </CardTitle>
            <CardDescription>
              Proposals with 21+ days no contact - require attention
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Client</TableHead>
                    <TableHead>Project</TableHead>
                    <TableHead>Fee</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Days No Contact</TableHead>
                    <TableHead>Last Contact Date</TableHead>
                    <TableHead>Next Action</TableHead>
                    <TableHead>Health</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {weeklyData.stalled_proposals.map((proposal) => (
                    <TableRow key={proposal.proposal_id} className="bg-yellow-50">
                      <TableCell className="font-medium">
                        {proposal.client_company}
                      </TableCell>
                      <TableCell>{proposal.project_name}</TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>-</TableCell>
                      <TableCell className="font-medium text-yellow-700">
                        {proposal.days_since_contact} days
                      </TableCell>
                      <TableCell>
                        {proposal.last_contact_date
                          ? format(new Date(proposal.last_contact_date), "MMM d")
                          : "-"}
                      </TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>-</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Won Proposals Section */}
      {weeklyData.won_proposals.length > 0 && (
        <Card className="border-green-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-700">
              <CheckCircle className="h-5 w-5" />
              Won Proposals ({weeklyData.won_proposals.length})
            </CardTitle>
            <CardDescription>
              Recently signed or activated proposals
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Client</TableHead>
                    <TableHead>Project</TableHead>
                    <TableHead>Contract Value</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Signed Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {weeklyData.won_proposals.map((proposal) => (
                    <TableRow key={proposal.proposal_id} className="bg-green-50">
                      <TableCell className="font-medium">
                        {proposal.client_company}
                      </TableCell>
                      <TableCell>{proposal.project_name}</TableCell>
                      <TableCell>
                        ${(proposal.fee || 0).toLocaleString()}
                      </TableCell>
                      <TableCell>Won</TableCell>
                      <TableCell>
                        {proposal.signed_date
                          ? format(
                              new Date(proposal.signed_date),
                              "MMM d"
                            )
                          : "-"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
