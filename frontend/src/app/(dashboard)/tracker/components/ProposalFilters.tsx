"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, X, Bookmark, BookmarkPlus, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { ds, ALL_PROPOSAL_STATUSES } from "@/lib/design-system";
import { type ProposalStatus } from "@/lib/constants";
import { DisciplineFilter } from "@/lib/types";

interface DisciplineData {
  disciplines?: {
    all?: { count: number };
    landscape?: { count: number };
    interior?: { count: number };
    architect?: { count: number };
    combined?: { count: number };
  };
}

interface SavedFilterView {
  id: string;
  name: string;
  filters: {
    search: string;
    statusFilter: string;
    disciplineFilter: string;
    ownerFilter: string;
    activeMetric: string | null;
  };
  createdAt: string;
}

interface ProposalFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: ProposalStatus | "all";
  onStatusFilterChange: (value: ProposalStatus | "all") => void;
  ownerFilter: string;
  onOwnerFilterChange: (value: string) => void;
  disciplineFilter: DisciplineFilter;
  onDisciplineFilterChange: (value: DisciplineFilter) => void;
  disciplineData: DisciplineData | undefined;
  activeMetric: string | null;
  savedViews: SavedFilterView[];
  onApplyView: (view: SavedFilterView) => void;
  onDeleteView: (viewId: string) => void;
  onSaveViewClick: () => void;
  onClearFilters: () => void;
}

export function ProposalFilters({
  search,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  ownerFilter,
  onOwnerFilterChange,
  disciplineFilter,
  onDisciplineFilterChange,
  disciplineData,
  activeMetric,
  savedViews,
  onApplyView,
  onDeleteView,
  onSaveViewClick,
  onClearFilters,
}: ProposalFiltersProps) {
  const hasActiveFilters = search || statusFilter !== "all" || ownerFilter !== "all" || disciplineFilter !== "all" || activeMetric;

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
      <CardContent className="py-3 px-4">
        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative w-full sm:w-auto sm:flex-1 sm:max-w-xs">
            <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search..."
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-8 h-8 text-sm"
            />
          </div>

          {/* Status Filter */}
          <Select
            value={statusFilter}
            onValueChange={(v) => onStatusFilterChange(v as ProposalStatus | "all")}
          >
            <SelectTrigger className="w-[130px] h-8 text-sm">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              {ALL_PROPOSAL_STATUSES.map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Owner Filter */}
          <Select value={ownerFilter} onValueChange={onOwnerFilterChange}>
            <SelectTrigger className="w-[100px] h-8 text-sm">
              <SelectValue placeholder="Owner" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="bill">Bill</SelectItem>
              <SelectItem value="brian">Brian</SelectItem>
              <SelectItem value="lukas">Lukas</SelectItem>
              <SelectItem value="mink">Mink</SelectItem>
            </SelectContent>
          </Select>

          {/* Discipline Filter */}
          <Select
            value={disciplineFilter}
            onValueChange={(v) => onDisciplineFilterChange(v as DisciplineFilter)}
          >
            <SelectTrigger className="w-[120px] h-8 text-sm">
              <SelectValue placeholder="Discipline" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All ({disciplineData?.disciplines?.all?.count || 0})</SelectItem>
              <SelectItem value="landscape">LA ({disciplineData?.disciplines?.landscape?.count || 0})</SelectItem>
              <SelectItem value="interior">ID ({disciplineData?.disciplines?.interior?.count || 0})</SelectItem>
              <SelectItem value="architect">Arch ({disciplineData?.disciplines?.architect?.count || 0})</SelectItem>
              <SelectItem value="combined">Combined ({disciplineData?.disciplines?.combined?.count || 0})</SelectItem>
            </SelectContent>
          </Select>

          {/* Saved Views */}
          {savedViews.length > 0 && (
            <Select
              value=""
              onValueChange={(id) => {
                const view = savedViews.find((x) => x.id === id);
                if (view) onApplyView(view);
              }}
            >
              <SelectTrigger className="w-[120px] h-8 text-sm">
                <Bookmark className="h-3 w-3 mr-1" />
                <SelectValue placeholder="Views" />
              </SelectTrigger>
              <SelectContent>
                {savedViews.map((view) => (
                  <div
                    key={view.id}
                    className="flex items-center justify-between px-2 py-1 hover:bg-slate-100 rounded cursor-pointer group"
                  >
                    <span className="text-sm" onClick={() => onApplyView(view)}>
                      {view.name}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-5 w-5 p-0 opacity-0 group-hover:opacity-100 text-red-500"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteView(view.id);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </SelectContent>
            </Select>
          )}

          {/* Save View */}
          <Button
            variant="outline"
            size="sm"
            onClick={onSaveViewClick}
            className="h-8 text-xs gap-1"
          >
            <BookmarkPlus className="h-3 w-3" />
            Save
          </Button>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearFilters}
              className="h-8 text-xs text-slate-500 hover:text-slate-700"
            >
              <X className="h-3 w-3 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
