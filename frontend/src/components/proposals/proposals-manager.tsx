"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, Filter, Download, Plus, Eye } from "lucide-react";
import { useRouter } from "next/navigation";

interface Proposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  status?: string;
  health_score?: number;
  days_since_contact?: number;
  is_active_project: boolean;
  created_at?: string;
  updated_at?: string;
}

export default function ProposalsManager() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState<"all" | "active" | "proposals">("all");
  const router = useRouter();

  const { data: proposals, isLoading } = useQuery<Proposal[]>({
    queryKey: ["proposals"],
    queryFn: async () => {
      const res = await fetch("http://localhost:8000/api/proposals");
      if (!res.ok) throw new Error("Failed to fetch proposals");
      return res.json();
    },
  });

  const { data: stats } = useQuery({
    queryKey: ["proposal-stats"],
    queryFn: async () => {
      const res = await fetch("http://localhost:8000/api/proposals/stats");
      if (!res.ok) throw new Error("Failed to fetch stats");
      return res.json();
    },
  });

  const filteredProposals = proposals?.filter((p) => {
    const matchesSearch =
      p.project_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.project_code.toLowerCase().includes(searchTerm.toLowerCase());

    if (filter === "active") return matchesSearch && p.is_active_project;
    if (filter === "proposals") return matchesSearch && !p.is_active_project;
    return matchesSearch;
  });

  const getHealthColor = (score?: number) => {
    if (!score) return "bg-gray-500";
    if (score >= 70) return "bg-green-500";
    if (score >= 50) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getHealthLabel = (score?: number) => {
    if (!score) return "Unknown";
    if (score >= 70) return "Healthy";
    if (score >= 50) return "At Risk";
    return "Critical";
  };

  const formatDaysAgo = (days?: number) => {
    if (days === undefined || days === null) return "Never";
    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    return `${days} days ago`;
  };

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

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Proposals</CardDescription>
            <CardTitle className="text-2xl">
              {isLoading ? <Skeleton className="h-8 w-16" /> : stats?.total_proposals || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active Projects</CardDescription>
            <CardTitle className="text-2xl">
              {isLoading ? <Skeleton className="h-8 w-16" /> : stats?.active_projects || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Needs Attention</CardDescription>
            <CardTitle className="text-2xl text-red-500">
              {isLoading ? <Skeleton className="h-8 w-16" /> : stats?.needs_attention || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Avg Health Score</CardDescription>
            <CardTitle className="text-2xl">
              {isLoading ? <Skeleton className="h-8 w-16" /> : (stats?.avg_health_score?.toFixed(0) || "N/A")}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Search and Filter */}
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
          <Tabs value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
            <TabsList>
              <TabsTrigger value="all">All ({proposals?.length || 0})</TabsTrigger>
              <TabsTrigger value="active">
                Active Projects ({proposals?.filter(p => p.is_active_project).length || 0})
              </TabsTrigger>
              <TabsTrigger value="proposals">
                Proposals Only ({proposals?.filter(p => !p.is_active_project).length || 0})
              </TabsTrigger>
            </TabsList>

            <TabsContent value={filter} className="mt-4">
              {isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
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
                      {filteredProposals?.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                            No proposals found
                          </TableCell>
                        </TableRow>
                      ) : (
                        filteredProposals?.map((proposal) => (
                          <TableRow
                            key={proposal.proposal_id}
                            className="cursor-pointer hover:bg-muted/50"
                            onClick={() => router.push(`/proposals/${proposal.project_code}`)}
                          >
                            <TableCell className="font-mono font-semibold">
                              {proposal.project_code}
                            </TableCell>
                            <TableCell className="font-medium">{proposal.project_name}</TableCell>
                            <TableCell>
                              <Badge variant={proposal.is_active_project ? "default" : "secondary"}>
                                {proposal.is_active_project ? "Project" : "Proposal"}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline">
                                {proposal.status || "Unknown"}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${getHealthColor(proposal.health_score)}`} />
                                <span className="text-sm">
                                  {proposal.health_score ? `${proposal.health_score}` : "N/A"}
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
                                  router.push(`/proposals/${proposal.project_code}`);
                                }}
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))
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
