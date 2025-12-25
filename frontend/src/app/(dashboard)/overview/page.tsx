"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ExecutiveMetrics } from "@/components/overview/executive-metrics";
import { ActionBoard } from "@/components/overview/action-board";
import { WeeklySummary } from "@/components/overview/weekly-summary";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { BarChart3, Kanban, Calendar } from "lucide-react";

export default function OverviewPage() {
  const [activeTab, setActiveTab] = useState("executive");

  // Fetch stats for executive dashboard
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ["proposalTrackerStats"],
    queryFn: () => api.getProposalTrackerStats(),
  });

  // Fetch all proposals for action board
  const { data: proposalsData, isLoading: proposalsLoading } = useQuery({
    queryKey: ["proposalTrackerList", "all", "all", "", 1],
    queryFn: () => api.getProposalTrackerList({ per_page: 200 }),
  });

  // Fetch weekly changes
  const { data: weeklyData, isLoading: weeklyLoading } = useQuery({
    queryKey: ["proposalWeeklyChanges"],
    queryFn: () => api.getProposalWeeklyChanges(),
  });

  return (
    <div className={cn(ds.gap.loose, "space-y-6 w-full max-w-full")}>
      {/* Header */}
      <div>
        <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
          Proposals Overview
        </h1>
        <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
          Executive dashboard, action board, and weekly report
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="executive" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Executive
          </TabsTrigger>
          <TabsTrigger value="actions" className="flex items-center gap-2">
            <Kanban className="h-4 w-4" />
            Action Board
          </TabsTrigger>
          <TabsTrigger value="weekly" className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Weekly
          </TabsTrigger>
        </TabsList>

        <TabsContent value="executive" className="mt-6">
          <ExecutiveMetrics
            stats={statsData?.stats}
            proposals={proposalsData?.proposals || []}
            isLoading={statsLoading || proposalsLoading}
          />
        </TabsContent>

        <TabsContent value="actions" className="mt-6">
          <ActionBoard
            proposals={proposalsData?.proposals || []}
            isLoading={proposalsLoading}
          />
        </TabsContent>

        <TabsContent value="weekly" className="mt-6">
          <WeeklySummary
            weeklyData={weeklyData}
            isLoading={weeklyLoading}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
