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
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, Plus, Eye } from "lucide-react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { ProposalSummary } from "@/lib/types";

type FilterOption = "all" | "active" | "proposals";

export default function ProposalsManager() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState<FilterOption>("all");
  const router = useRouter();

  const proposalsQuery = useQuery({
    queryKey: ["proposals", "all"],
    queryFn: () => api.getProposals({ per_page: 500 }),
    staleTime: 1000 * 60 * 5,
  });

  const statsQuery = useQuery({
    queryKey: ["proposal-stats"],
    queryFn: api.getProposalStats,
    staleTime: 1000 * 60 * 5,
  });

  const proposals = useMemo<ProposalSummary[]>(() => {
    return proposalsQuery.data?.data ?? [];
  }, [proposalsQuery.data]);

  const filteredProposals = useMemo(() => {
    const search = searchTerm.trim().toLowerCase();
    return proposals.filter((proposal) => {
      const matchesSearch =
        !search ||
        proposal.project_name.toLowerCase().includes(search) ||
        proposal.project_code.toLowerCase().includes(search);

      if (!matchesSearch) {
        return false;
      }

      if (filter === "active") {
        return proposal.is_active_project === 1;
      }

      if (filter === "proposals") {
        return proposal.is_active_project === 0;
      }

      return true;
    });
  }, [proposals, searchTerm, filter]);

  const totalCount = proposals.length;
  const activeCount = proposals.filter((p) => p.is_active_project === 1).length;
  const proposalCount = totalCount - activeCount;

  const needsAttention =
    statsQuery.data?.needs_attention ??
    statsQuery.data?.need_followup ??
    0;
  const avgHealth = statsQuery.data?.avg_health_score;

  const getHealthColor = (score?: number | null) => {
    if (score === undefined || score === null) return "bg-gray-500";
    if (score >= 70) return "bg-green-500";
    if (score >= 50) return "bg-yellow-500";
    return "bg-red-500";
  };

  const formatDaysAgo = (days?: number | null) => {
    if (days === undefined || days === null) return "Never";
    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    return `${days} days ago`;
  };

  const proposalsErrorMessage =
    proposalsQuery.error instanceof Error
      ? proposalsQuery.error.message
      : "Unable to load proposals.";

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Proposals & Projects</h1>
          <p className="text-muted-foreground mt-1">
            Manage and track all proposals and active projects
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Proposal
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Records</CardDescription>
            <CardTitle className="text-2xl">
              {statsQuery.isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                statsQuery.data?.total_proposals ?? 0
              )}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active Projects</CardDescription>
            <CardTitle className="text-2xl">
              {statsQuery.isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                statsQuery.data?.active_projects ?? 0
              )}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Needs Attention</CardDescription>
            <CardTitle className="text-2xl text-red-500">
              {statsQuery.isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                needsAttention
              )}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Avg Health Score</CardDescription>
            <CardTitle className="text-2xl">
              {statsQuery.isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : avgHealth !== undefined && avgHealth !== null ? (
                Number(avgHealth).toFixed(0)
              ) : (
                "N/A"
              )}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All Proposals</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative w-64">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search proposals..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs value={filter} onValueChange={(v) => setFilter(v as FilterOption)}>
            <TabsList>
              <TabsTrigger value="all">All ({totalCount})</TabsTrigger>
              <TabsTrigger value="active">
                Active Projects ({activeCount})
              </TabsTrigger>
              <TabsTrigger value="proposals">
                Proposals Only ({proposalCount})
              </TabsTrigger>
            </TabsList>

            <TabsContent value={filter} className="mt-4">
              {proposalsQuery.isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : proposalsQuery.isError ? (
                <div className="rounded-md border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
                  {proposalsErrorMessage}
                </div>
              ) : (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Project Code</TableHead>
                        <TableHead>Project Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Health</TableHead>
                        <TableHead>Last Contact</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredProposals.length === 0 ? (
                        <TableRow>
                          <TableCell
                            colSpan={7}
                            className="py-8 text-center text-muted-foreground"
                          >
                            No proposals found
                          </TableCell>
                        </TableRow>
                      ) : (
                        filteredProposals.map((proposal) => {
                          const isActive = proposal.is_active_project === 1;
                          return (
                            <TableRow
                              key={proposal.proposal_id}
                              className="cursor-pointer hover:bg-muted/50"
                              onClick={() =>
                                router.push(`/proposals/${proposal.project_code}`)
                              }
                            >
                              <TableCell className="font-mono font-semibold">
                                {proposal.project_code}
                              </TableCell>
                              <TableCell className="font-medium">
                                {proposal.project_name}
                              </TableCell>
                              <TableCell>
                                <Badge variant={isActive ? "default" : "secondary"}>
                                  {isActive ? "Project" : "Proposal"}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline">
                                  {proposal.status || "Unknown"}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <div
                                    className={`h-2 w-2 rounded-full ${getHealthColor(
                                      proposal.health_score
                                    )}`}
                                  />
                                  <span className="text-sm">
                                    {proposal.health_score ?? "N/A"}
                                  </span>
                                </div>
                              </TableCell>
                              <TableCell className="text-sm text-muted-foreground">
                                {formatDaysAgo(proposal.days_since_contact)}
                              </TableCell>
                              <TableCell className="text-right">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    router.push(
                                      `/proposals/${proposal.project_code}`
                                    );
                                  }}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          );
                        })
                      )}
                    </TableBody>
                  </Table>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
