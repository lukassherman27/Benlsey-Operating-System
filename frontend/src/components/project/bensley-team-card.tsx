"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { Users, Briefcase } from "lucide-react";

interface BensleyTeamCardProps {
  projectCode: string;
}

interface TeamMember {
  member_id: number;
  full_name: string;
  phase: string | null;
  task_description: string | null;
  work_days: number;
}

export function BensleyTeamCard({ projectCode }: BensleyTeamCardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["project-schedule-team", projectCode],
    queryFn: async () => {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectCode)}/schedule-team`);
      if (!res.ok) throw new Error("Failed to fetch team");
      return res.json();
    },
    retry: 1,
    staleTime: 1000 * 60 * 5,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Bensley Team
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const team = data?.team || [];

  if (team.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Bensley Team
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-sm text-slate-500">
            No team members scheduled for this project yet
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Bensley Team
          </CardTitle>
          <Badge variant="secondary">{team.length} people</Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2">
          {team.map((member: TeamMember) => (
            <div
              key={member.member_id}
              className="flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-medium text-sm">
                  {member.full_name.charAt(0)}
                </div>
                <div>
                  <p className="font-medium text-sm text-slate-900">{member.full_name}</p>
                  {member.task_description && (
                    <p className="text-xs text-slate-500 truncate max-w-[200px]">
                      {member.task_description}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {member.phase && (
                  <Badge variant="outline" className="text-xs">
                    {member.phase}
                  </Badge>
                )}
                {member.work_days > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {member.work_days}d
                  </Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
