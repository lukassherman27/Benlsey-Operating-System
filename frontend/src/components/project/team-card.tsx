"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { Users, Mail, Star, Layers } from "lucide-react";
import { format, parseISO, isValid } from "date-fns";
import { cn } from "@/lib/utils";

interface TeamCardProps {
  projectCode: string;
}

interface TeamMember {
  contact_id: number;
  name: string | null;
  email: string | null;
  role: string | null;
  email_count: number;
  is_primary: number;
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return "Never";
  try {
    const date = parseISO(dateStr);
    if (!isValid(date)) return "Never";
    return format(date, "MMM d, yyyy");
  } catch {
    return "Never";
  }
};

// Icon for discipline
const DISCIPLINE_ICONS: Record<string, { color: string; label: string }> = {
  Architecture: { color: "bg-blue-100 text-blue-700 border-blue-200", label: "Architecture" },
  Interior: { color: "bg-purple-100 text-purple-700 border-purple-200", label: "Interior" },
  Landscape: { color: "bg-green-100 text-green-700 border-green-200", label: "Landscape" },
  Engineering: { color: "bg-orange-100 text-orange-700 border-orange-200", label: "Engineering" },
  Planning: { color: "bg-teal-100 text-teal-700 border-teal-200", label: "Planning" },
};

export function TeamCard({ projectCode }: TeamCardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["project-team", projectCode],
    queryFn: () => api.getProjectTeam(projectCode),
    retry: 1,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Project Team
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Project Team
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-amber-700">
            Unable to load team members. This feature may not be available yet.
          </p>
        </CardContent>
      </Card>
    );
  }

  const byDiscipline = data?.by_discipline || {};
  const totalMembers = data?.count || 0;

  if (totalMembers === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Project Team
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Users className="h-12 w-12 mx-auto text-slate-200 mb-3" />
            <p className="text-muted-foreground text-sm">
              No team members found for this project
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Project Team
          <Badge variant="secondary" className="ml-2">
            {totalMembers}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {Object.entries(byDiscipline).map(([discipline, members]) => {
            const disciplineStyle = DISCIPLINE_ICONS[discipline] || {
              color: "bg-slate-100 text-slate-700 border-slate-200",
              label: discipline,
            };

            // Sort by primary first, then by email count
            const sortedMembers = [...(members as TeamMember[])].sort((a, b) => {
              if (a.is_primary !== b.is_primary) return b.is_primary - a.is_primary;
              return b.email_count - a.email_count;
            });

            return (
              <div key={discipline} className="space-y-2">
                {/* Discipline Header */}
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-slate-500" />
                  <Badge variant="outline" className={cn("text-xs", disciplineStyle.color)}>
                    {disciplineStyle.label}
                  </Badge>
                  <span className="text-xs text-slate-500">({sortedMembers.length})</span>
                </div>

                {/* Team Members in this discipline */}
                <div className="pl-6 space-y-2">
                  {sortedMembers.map((member) => {
                    const displayName = member.name || member.email || "Unknown";

                    return (
                      <div
                        key={member.contact_id}
                        className="border rounded-lg p-3 bg-white hover:bg-slate-50 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className="font-medium text-sm truncate">{displayName}</p>
                              {member.is_primary === 1 && (
                                <Badge variant="default" className="text-xs flex items-center gap-1">
                                  <Star className="h-3 w-3" />
                                  Primary
                                </Badge>
                              )}
                            </div>
                            {member.role && (
                              <p className="text-xs text-slate-500 mt-1">{member.role}</p>
                            )}
                            {member.email && (
                              <div className="flex items-center gap-1 mt-1 text-xs text-slate-500">
                                <Mail className="h-3 w-3" />
                                <span className="truncate">{member.email}</span>
                              </div>
                            )}
                          </div>
                          {member.email_count > 0 && (
                            <Badge variant="outline" className="text-xs flex-shrink-0">
                              {member.email_count} email{member.email_count !== 1 ? 's' : ''}
                            </Badge>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
