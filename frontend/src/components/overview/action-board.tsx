"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, cn } from "@/lib/utils";
import { ProposalTrackerItem } from "@/lib/types";
import { AlertTriangle, User, Clock, CheckCircle } from "lucide-react";

interface ActionBoardProps {
  proposals: ProposalTrackerItem[];
  isLoading: boolean;
}

interface ActionCardProps {
  proposal: ProposalTrackerItem;
  onClick: () => void;
}

function ActionCard({ proposal, onClick }: ActionCardProps) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const isOverdue = proposal.action_due && new Date(proposal.action_due) < today;

  return (
    <div
      className={cn(
        "p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md",
        isOverdue ? "bg-red-50 border-red-200" : "bg-white border-slate-200"
      )}
      onClick={onClick}
    >
      <p className="font-medium text-sm text-slate-900 truncate" title={proposal.project_name}>
        {proposal.project_name}
      </p>
      <p className="text-xs text-slate-500 mt-1">{formatCurrency(proposal.project_value)}</p>
      {proposal.action_needed && (
        <p className="text-xs text-slate-600 mt-2 line-clamp-2">
          {proposal.action_needed}
        </p>
      )}
      {proposal.action_due && (
        <p className={cn(
          "text-xs mt-2 font-medium",
          isOverdue ? "text-red-600" : "text-slate-400"
        )}>
          {isOverdue ? "Overdue: " : "Due: "}
          {new Date(proposal.action_due).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </p>
      )}
    </div>
  );
}

export function ActionBoard({ proposals, isLoading }: ActionBoardProps) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-96" />
        ))}
      </div>
    );
  }

  const activeProposals = proposals.filter(p =>
    !["Contract Signed", "Lost", "Declined", "Dormant"].includes(p.current_status)
  );

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Categorize proposals
  const overdueItems = activeProposals.filter(p =>
    p.action_due && new Date(p.action_due) < today
  );

  const billItems = activeProposals.filter(p =>
    p.action_owner === 'bill' &&
    !(p.action_due && new Date(p.action_due) < today)
  );

  const brianItems = activeProposals.filter(p =>
    p.action_owner === 'brian' &&
    !(p.action_due && new Date(p.action_due) < today)
  );

  const waitingItems = activeProposals.filter(p =>
    p.ball_in_court === 'them' &&
    !(p.action_due && new Date(p.action_due) < today)
  );

  const handleClick = (projectCode: string) => {
    router.push(`/proposals/${encodeURIComponent(projectCode)}`);
  };

  const columns = [
    {
      title: "Overdue",
      icon: AlertTriangle,
      iconColor: "text-red-500",
      borderColor: "border-t-red-500",
      items: overdueItems,
    },
    {
      title: "Bill's Queue",
      icon: User,
      iconColor: "text-blue-500",
      borderColor: "border-t-blue-500",
      items: billItems,
    },
    {
      title: "Brian's Queue",
      icon: User,
      iconColor: "text-purple-500",
      borderColor: "border-t-purple-500",
      items: brianItems,
    },
    {
      title: "Waiting on Client",
      icon: Clock,
      iconColor: "text-amber-500",
      borderColor: "border-t-amber-500",
      items: waitingItems,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {columns.map(({ title, icon: Icon, iconColor, borderColor, items }) => (
        <Card key={title} className={cn("border-t-4", borderColor)}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 flex items-center gap-2">
              <Icon className={cn("h-4 w-4", iconColor)} />
              {title} ({items.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
            {items.length === 0 ? (
              <div className="py-8 text-center">
                <CheckCircle className="h-8 w-8 text-slate-200 mx-auto mb-2" />
                <p className="text-sm text-slate-400">All clear!</p>
              </div>
            ) : (
              items.map((proposal) => (
                <ActionCard
                  key={proposal.id}
                  proposal={proposal}
                  onClick={() => handleClick(proposal.project_code)}
                />
              ))
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
