'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  ChevronRight,
  RefreshCw,
  MessageSquare,
  Target,
  ArrowRight,
  AlertCircle,
  Phone,
  Mail,
  Calendar,
  Users,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import Link from 'next/link'
import { api } from '@/lib/api'
import { MyDayProposal } from '@/lib/types'
import { useCurrentUser, getFirstName } from '@/hooks/useCurrentUser'

export default function ProposalsMyDayPage() {
  const queryClient = useQueryClient()
  const { email, name } = useCurrentUser()
  const firstName = getFirstName(name)

  // Fetch My Day data (includes proposals)
  const { data, isLoading, error } = useQuery({
    queryKey: ['my-day', email],
    queryFn: () => api.getMyDay(email || 'user', firstName),
    refetchInterval: 60000, // Refresh every minute
    enabled: !!email,
  })

  // Urgency colors for badges
  const urgencyColors: Record<string, string> = {
    overdue: 'bg-red-100 text-red-700 border-red-200',
    today: 'bg-amber-100 text-amber-700 border-amber-200',
    upcoming: 'bg-blue-100 text-blue-700 border-blue-200',
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  // Error state
  if (error || !data) {
    return (
      <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50")}>
        <CardContent className="py-12 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
          <p className={cn(ds.typography.heading3, "text-red-700 mb-2")}>
            Failed to load proposals
          </p>
          <p className={cn(ds.typography.body, "text-red-600 mb-4")}>
            Please try again or check the API connection.
          </p>
          <Button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['my-day'] })}
            variant="outline"
            className="border-red-200 text-red-700 hover:bg-red-100"
          >
            Try Again
          </Button>
        </CardContent>
      </Card>
    )
  }

  const { proposals } = data

  // Categorize proposals by urgency
  const overdueProposals = proposals.needing_followup.filter(
    (p: MyDayProposal) => p.urgency === 'overdue'
  )
  const todayProposals = proposals.needing_followup.filter(
    (p: MyDayProposal) => p.urgency === 'today'
  )
  const upcomingProposals = proposals.needing_followup.filter(
    (p: MyDayProposal) => p.urgency === 'upcoming'
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            My Proposals Today
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary)}>
            Proposals where the ball is in your court
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['my-day'] })}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className={cn(ds.borderRadius.card, overdueProposals.length > 0 ? "border-red-200 bg-red-50/30" : "border-slate-200")}>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-3">
              <div className={cn("p-2 rounded-lg", overdueProposals.length > 0 ? "bg-red-100" : "bg-slate-100")}>
                <AlertTriangle className={cn("h-5 w-5", overdueProposals.length > 0 ? "text-red-700" : "text-slate-500")} />
              </div>
              <div>
                <p className={cn(ds.typography.caption, overdueProposals.length > 0 ? "text-red-600" : ds.textColors.tertiary)}>
                  Overdue
                </p>
                <p className={cn(ds.typography.heading2, overdueProposals.length > 0 ? "text-red-700" : ds.textColors.primary)}>
                  {overdueProposals.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-amber-200 bg-amber-50/30")}>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-100">
                <Clock className="h-5 w-5 text-amber-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-amber-600")}>Due Today</p>
                <p className={cn(ds.typography.heading2, "text-amber-700")}>
                  {todayProposals.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-teal-200 bg-teal-50/30")}>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-teal-100">
                <Target className="h-5 w-5 text-teal-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-teal-600")}>Total Our Ball</p>
                <p className={cn(ds.typography.heading2, "text-teal-700")}>
                  {proposals.total_our_ball}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Overdue Proposals */}
      {overdueProposals.length > 0 && (
        <Card className={cn(ds.borderRadius.card, "border-red-200")}>
          <CardHeader className="pb-2">
            <CardTitle className={cn(ds.typography.heading3, "text-red-700 flex items-center gap-2")}>
              <AlertTriangle className="h-5 w-5" />
              Overdue - Action Required ({overdueProposals.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {overdueProposals.map((proposal: MyDayProposal) => (
                <ProposalCard key={proposal.proposal_id} proposal={proposal} urgencyColors={urgencyColors} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Today's Follow-ups */}
      {todayProposals.length > 0 && (
        <Card className={cn(ds.borderRadius.card, "border-amber-200")}>
          <CardHeader className="pb-2">
            <CardTitle className={cn(ds.typography.heading3, "text-amber-700 flex items-center gap-2")}>
              <Clock className="h-5 w-5" />
              Due Today ({todayProposals.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {todayProposals.map((proposal: MyDayProposal) => (
                <ProposalCard key={proposal.proposal_id} proposal={proposal} urgencyColors={urgencyColors} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upcoming */}
      {upcomingProposals.length > 0 && (
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardHeader className="pb-2">
            <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary, "flex items-center gap-2")}>
              <Calendar className="h-5 w-5 text-blue-600" />
              Upcoming ({upcomingProposals.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingProposals.map((proposal: MyDayProposal) => (
                <ProposalCard key={proposal.proposal_id} proposal={proposal} urgencyColors={urgencyColors} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {proposals.needing_followup.length === 0 && (
        <Card className={cn(ds.borderRadius.card, "border-emerald-200 bg-emerald-50/30")}>
          <CardContent className="py-12 text-center">
            <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500 mb-4" />
            <p className={cn(ds.typography.heading3, "text-emerald-700 mb-2")}>
              All caught up!
            </p>
            <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
              No proposals need your attention right now.
            </p>
          </CardContent>
        </Card>
      )}

      {/* View All Link */}
      <div className="flex justify-center">
        <Link href="/tracker">
          <Button variant="outline" size="lg">
            View All Proposals
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>
      </div>
    </div>
  )
}

// Proposal Card Component
function ProposalCard({
  proposal,
  urgencyColors,
}: {
  proposal: MyDayProposal
  urgencyColors: Record<string, string>
}) {
  return (
    <Link href={`/proposals/${encodeURIComponent(proposal.project_code)}`}>
      <div className="flex items-start gap-4 p-4 rounded-lg border border-slate-200 hover:border-teal-300 hover:bg-slate-50 transition-colors cursor-pointer">
        {/* Main Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
              {proposal.project_name || proposal.project_code}
            </p>
            {proposal.urgency && (
              <Badge variant="outline" className={cn("shrink-0 text-xs", urgencyColors[proposal.urgency])}>
                {proposal.urgency === 'overdue' ? 'Overdue' :
                 proposal.urgency === 'today' ? 'Today' : 'Upcoming'}
              </Badge>
            )}
          </div>
          <p className={cn(ds.typography.caption, ds.textColors.tertiary, "flex items-center gap-2")}>
            <Users className="h-3 w-3" />
            {proposal.client_name || 'Unknown Client'}
          </p>
          {proposal.waiting_for && (
            <p className={cn(ds.typography.caption, "text-amber-600 mt-1")}>
              Waiting for: {proposal.waiting_for}
            </p>
          )}
        </div>

        {/* Stats */}
        <div className="text-right shrink-0">
          {proposal.days_since_contact !== null && proposal.days_since_contact !== undefined && (
            <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
              {Math.round(proposal.days_since_contact)}d since contact
            </p>
          )}
          {proposal.probability !== null && proposal.probability !== undefined && (
            <Badge variant="secondary" className="mt-1">
              {proposal.probability}% probability
            </Badge>
          )}
        </div>

        <ChevronRight className="h-5 w-5 text-slate-400 shrink-0 self-center" />
      </div>
    </Link>
  )
}
