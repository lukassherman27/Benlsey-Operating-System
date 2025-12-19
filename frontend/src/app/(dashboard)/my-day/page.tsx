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
  Calendar,
  CheckSquare,
  Bell,
  Video,
  MessageSquare,
  Lightbulb,
  Users,
  Target,
  ArrowRight,
  ExternalLink,
  AlertCircle,
  Sun,
  Sunrise,
  Moon,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import Link from 'next/link'
import { api } from '@/lib/api'
import {
  MyDayResponse,
  MyDayTask,
  MyDayMeeting,
  MyDayProposal,
  MyDaySuggestion,
} from '@/lib/types'

export default function MyDayPage() {
  const queryClient = useQueryClient()

  // Fetch My Day data
  const { data, isLoading, error } = useQuery({
    queryKey: ['my-day'],
    queryFn: () => api.getMyDay('bill', 'Bill'),
    refetchInterval: 60000, // Refresh every minute
  })

  // Mark task complete mutation
  const completeTask = useMutation({
    mutationFn: (taskId: number) => api.completeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-day'] })
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  // Snooze task mutation
  const snoozeTask = useMutation({
    mutationFn: ({ taskId, newDueDate }: { taskId: number; newDueDate: string }) =>
      api.snoozeTask(taskId, newDueDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-day'] })
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  const handleSnooze = (task: MyDayTask) => {
    const currentDue = task.due_date ? new Date(task.due_date) : new Date()
    currentDue.setDate(currentDue.getDate() + 1) // Snooze to tomorrow
    const newDueDate = currentDue.toISOString().split('T')[0]
    snoozeTask.mutate({ taskId: task.task_id, newDueDate })
  }

  // Priority colors
  const priorityColors: Record<string, string> = {
    low: 'bg-slate-100 text-slate-700',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-amber-100 text-amber-700',
    critical: 'bg-red-100 text-red-700',
  }

  // Get greeting icon based on time of day
  const getGreetingIcon = (greeting: string) => {
    if (greeting.includes('morning')) return <Sunrise className="h-6 w-6 text-amber-500" />
    if (greeting.includes('afternoon')) return <Sun className="h-6 w-6 text-amber-500" />
    return <Moon className="h-6 w-6 text-indigo-500" />
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-48 w-full" /></CardContent></Card>
          ))}
        </div>
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
            Failed to load your day
          </p>
          <p className={cn(ds.typography.body, "text-red-600 mb-4")}>
            The My Day API may not be available yet.
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

  const { greeting, tasks, meetings, proposals, suggestions_queue, week_ahead, commitments } = data

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Greeting Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {getGreetingIcon(greeting.text)}
          <div>
            <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
              {greeting.text}, {greeting.name}
            </h1>
            <p className={cn(ds.typography.body, ds.textColors.secondary)}>
              {greeting.day_of_week}, {greeting.formatted_date}
            </p>
          </div>
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

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className={cn(ds.borderRadius.card, tasks.overdue_count > 0 ? "border-red-200 bg-red-50/30" : "border-slate-200")}>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-3">
              <div className={cn("p-2 rounded-lg", tasks.overdue_count > 0 ? "bg-red-100" : "bg-slate-100")}>
                <AlertTriangle className={cn("h-5 w-5", tasks.overdue_count > 0 ? "text-red-700" : "text-slate-500")} />
              </div>
              <div>
                <p className={cn(ds.typography.caption, tasks.overdue_count > 0 ? "text-red-600" : ds.textColors.tertiary)}>Overdue</p>
                <p className={cn(ds.typography.heading2, tasks.overdue_count > 0 ? "text-red-700" : ds.textColors.primary)}>
                  {tasks.overdue_count}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/30")}>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Clock className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-blue-600")}>Today</p>
                <p className={cn(ds.typography.heading2, "text-blue-700")}>
                  {tasks.today_count}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-purple-200 bg-purple-50/30")}>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100">
                <Calendar className="h-5 w-5 text-purple-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-purple-600")}>Meetings</p>
                <p className={cn(ds.typography.heading2, "text-purple-700")}>
                  {meetings.count}
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
                <p className={cn(ds.typography.caption, "text-teal-600")}>Follow-ups</p>
                <p className={cn(ds.typography.heading2, "text-teal-700")}>
                  {proposals.count}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Tasks */}
        <div className="space-y-6">
          {/* Overdue Tasks */}
          {tasks.overdue.length > 0 && (
            <Card className={cn(ds.borderRadius.card, "border-red-200")}>
              <CardHeader className="pb-2">
                <CardTitle className={cn(ds.typography.heading3, "text-red-700 flex items-center gap-2")}>
                  <AlertTriangle className="h-5 w-5" />
                  Overdue ({tasks.overdue.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {tasks.overdue.slice(0, 5).map((task) => (
                    <TaskItem
                      key={task.task_id}
                      task={task}
                      onComplete={() => completeTask.mutate(task.task_id)}
                      onSnooze={() => handleSnooze(task)}
                      priorityColors={priorityColors}
                      isOverdue
                    />
                  ))}
                </div>
                {tasks.overdue.length > 5 && (
                  <Link href="/tasks?filter=overdue" className="block mt-3">
                    <Button variant="ghost" size="sm" className="w-full text-red-600">
                      View all {tasks.overdue.length} overdue
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </Link>
                )}
              </CardContent>
            </Card>
          )}

          {/* Today's Tasks */}
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader className="pb-2">
              <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary, "flex items-center gap-2")}>
                <CheckSquare className="h-5 w-5 text-blue-600" />
                Today&apos;s Tasks ({tasks.today.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {tasks.today.length === 0 ? (
                <div className="text-center py-6">
                  <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-400 mb-2" />
                  <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                    No tasks due today!
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {tasks.today.map((task) => (
                    <TaskItem
                      key={task.task_id}
                      task={task}
                      onComplete={() => completeTask.mutate(task.task_id)}
                      onSnooze={() => handleSnooze(task)}
                      priorityColors={priorityColors}
                    />
                  ))}
                </div>
              )}
              <Link href="/tasks" className="block mt-3">
                <Button variant="ghost" size="sm" className="w-full">
                  View all tasks ({tasks.total_active})
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Middle Column - Meetings & Proposals */}
        <div className="space-y-6">
          {/* Today's Meetings */}
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader className="pb-2">
              <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary, "flex items-center gap-2")}>
                <Calendar className="h-5 w-5 text-purple-600" />
                Today&apos;s Meetings ({meetings.count})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {meetings.today.length === 0 ? (
                <div className="text-center py-6">
                  <Calendar className="mx-auto h-8 w-8 text-slate-300 mb-2" />
                  <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                    No meetings today
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {meetings.today.map((meeting) => (
                    <MeetingItem key={meeting.meeting_id} meeting={meeting} />
                  ))}
                </div>
              )}
              <Link href="/meetings" className="block mt-3">
                <Button variant="ghost" size="sm" className="w-full">
                  View calendar
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Proposals Needing Follow-up */}
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader className="pb-2">
              <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary, "flex items-center gap-2")}>
                <MessageSquare className="h-5 w-5 text-teal-600" />
                Ball in Our Court ({proposals.total_our_ball})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {proposals.needing_followup.length === 0 ? (
                <div className="text-center py-6">
                  <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-400 mb-2" />
                  <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                    All caught up!
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {proposals.needing_followup.slice(0, 5).map((proposal) => (
                    <ProposalItem key={proposal.proposal_id} proposal={proposal} />
                  ))}
                </div>
              )}
              <Link href="/tracker" className="block mt-3">
                <Button variant="ghost" size="sm" className="w-full">
                  View all proposals
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - AI Suggestions & Week Ahead */}
        <div className="space-y-6">
          {/* AI Suggestions Queue */}
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader className="pb-2">
              <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary, "flex items-center gap-2")}>
                <Lightbulb className="h-5 w-5 text-amber-500" />
                AI Suggestions ({suggestions_queue.total_pending})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {suggestions_queue.top_suggestions.length === 0 ? (
                <div className="text-center py-6">
                  <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-400 mb-2" />
                  <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                    All suggestions reviewed!
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {suggestions_queue.top_suggestions.map((suggestion) => (
                    <SuggestionItem key={suggestion.suggestion_id} suggestion={suggestion} />
                  ))}
                </div>
              )}
              <Link href="/admin/suggestions" className="block mt-3">
                <Button variant="ghost" size="sm" className="w-full">
                  Review all suggestions
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Week Ahead Preview */}
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader className="pb-2">
              <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary, "flex items-center gap-2")}>
                <Clock className="h-5 w-5 text-slate-600" />
                Week Ahead
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Upcoming Deadlines */}
                {week_ahead.upcoming_deadlines.length > 0 && (
                  <div>
                    <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mb-2")}>
                      Upcoming Deadlines
                    </p>
                    <div className="space-y-1">
                      {week_ahead.upcoming_deadlines.slice(0, 3).map((task) => (
                        <div key={task.task_id} className="flex items-center justify-between text-sm">
                          <span className="truncate flex-1">{task.title}</span>
                          <span className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                            {task.due_date}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Meetings This Week */}
                <div className="flex items-center justify-between">
                  <span className={cn(ds.typography.body, ds.textColors.secondary)}>
                    Meetings this week
                  </span>
                  <Badge variant="secondary">{week_ahead.meetings_this_week}</Badge>
                </div>

                {/* Decision Dates */}
                {week_ahead.decision_dates.length > 0 && (
                  <div>
                    <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mb-2")}>
                      Proposal Decisions
                    </p>
                    <div className="space-y-1">
                      {week_ahead.decision_dates.map((proposal) => (
                        <div key={proposal.project_code} className="flex items-center justify-between text-sm">
                          <span className="truncate flex-1">{proposal.project_name}</span>
                          <span className={cn(ds.typography.caption, "text-amber-600")}>
                            {proposal.decision_date}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Deliverables Due */}
                {week_ahead.deliverables_due.length > 0 && (
                  <div>
                    <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mb-2")}>
                      Deliverables Due
                    </p>
                    <div className="space-y-1">
                      {week_ahead.deliverables_due.slice(0, 3).map((d) => (
                        <div key={d.deliverable_id} className="flex items-center justify-between text-sm">
                          <span className="truncate flex-1">{d.name}</span>
                          <span className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                            {d.due_date}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Commitments (if any overdue) */}
          {(commitments.our_overdue_count > 0 || commitments.their_overdue_count > 0) && (
            <Card className={cn(ds.borderRadius.card, "border-amber-200 bg-amber-50/30")}>
              <CardHeader className="pb-2">
                <CardTitle className={cn(ds.typography.heading3, "text-amber-700 flex items-center gap-2")}>
                  <Users className="h-5 w-5" />
                  Overdue Commitments
                </CardTitle>
              </CardHeader>
              <CardContent>
                {commitments.our_overdue_count > 0 && (
                  <div className="mb-3">
                    <p className={cn(ds.typography.caption, "text-amber-700 mb-1")}>
                      Our commitments ({commitments.our_overdue_count})
                    </p>
                    <div className="space-y-1">
                      {commitments.our_overdue.slice(0, 2).map((c) => (
                        <p key={c.commitment_id} className="text-sm text-amber-800 truncate">
                          {c.description}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
                {commitments.their_overdue_count > 0 && (
                  <div>
                    <p className={cn(ds.typography.caption, "text-amber-700 mb-1")}>
                      Their commitments ({commitments.their_overdue_count})
                    </p>
                    <div className="space-y-1">
                      {commitments.their_overdue.slice(0, 2).map((c) => (
                        <p key={c.commitment_id} className="text-sm text-amber-800 truncate">
                          {c.description}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

// Task Item Component
function TaskItem({
  task,
  onComplete,
  onSnooze,
  priorityColors,
  isOverdue = false,
}: {
  task: MyDayTask
  onComplete: () => void
  onSnooze: () => void
  priorityColors: Record<string, string>
  isOverdue?: boolean
}) {
  return (
    <div className={cn(
      "flex items-center gap-3 p-3 rounded-lg border transition-colors",
      isOverdue ? "border-red-200 bg-red-50/50" : "border-slate-100 hover:bg-slate-50"
    )}>
      <Button
        variant="ghost"
        size="sm"
        onClick={(e) => { e.stopPropagation(); onComplete(); }}
        className="h-8 w-8 p-0 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 shrink-0"
        title="Mark complete"
      >
        <CheckSquare className="h-4 w-4" />
      </Button>
      <div className="flex-1 min-w-0">
        <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
          {task.title}
        </p>
        {task.project_code && (
          <Link
            href={`/proposals/${encodeURIComponent(task.project_code)}`}
            className={cn(ds.typography.caption, "text-teal-600 hover:underline")}
          >
            {task.project_code}
          </Link>
        )}
      </div>
      <Badge
        variant="outline"
        className={cn("shrink-0 text-xs", priorityColors[task.priority] || 'bg-slate-100')}
      >
        {task.priority}
      </Badge>
      <Button
        variant="ghost"
        size="sm"
        onClick={(e) => { e.stopPropagation(); onSnooze(); }}
        className="h-8 w-8 p-0 text-amber-600 hover:text-amber-700 hover:bg-amber-50 shrink-0"
        title="Snooze to tomorrow"
      >
        <Bell className="h-4 w-4" />
      </Button>
    </div>
  )
}

// Meeting Item Component
function MeetingItem({ meeting }: { meeting: MyDayMeeting }) {
  const isVirtual = meeting.location?.toLowerCase().includes('zoom') ||
                   meeting.location?.toLowerCase().includes('teams') ||
                   meeting.location?.toLowerCase().includes('meet')

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
      <div className={cn("p-2 rounded-lg shrink-0", isVirtual ? "bg-purple-100" : "bg-slate-100")}>
        {isVirtual ? (
          <Video className="h-4 w-4 text-purple-600" />
        ) : (
          <Calendar className="h-4 w-4 text-slate-600" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
          {meeting.meeting_title || meeting.meeting_type || 'Meeting'}
        </p>
        <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
          {meeting.start_time || 'TBD'}
          {meeting.location && ` - ${meeting.location}`}
        </p>
      </div>
      {isVirtual && (
        <Button size="sm" variant="outline" className="shrink-0 text-purple-600 border-purple-200">
          <Video className="h-4 w-4 mr-1" />
          Join
        </Button>
      )}
    </div>
  )
}

// Proposal Item Component
function ProposalItem({ proposal }: { proposal: MyDayProposal }) {
  const urgencyColors = {
    overdue: 'text-red-600 bg-red-50 border-red-200',
    today: 'text-amber-600 bg-amber-50 border-amber-200',
    upcoming: 'text-slate-600 bg-slate-50 border-slate-200',
  }

  return (
    <Link href={`/proposals/${encodeURIComponent(proposal.project_code)}`}>
      <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-100 hover:bg-slate-50 hover:border-teal-200 transition-colors cursor-pointer">
        <div className="flex-1 min-w-0">
          <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
            {proposal.project_name || proposal.project_code}
          </p>
          <p className={cn(ds.typography.caption, ds.textColors.tertiary, "truncate")}>
            {proposal.client_name}
            {proposal.days_since_contact !== null && ` - ${proposal.days_since_contact}d ago`}
          </p>
        </div>
        {proposal.urgency && (
          <Badge variant="outline" className={cn("shrink-0 text-xs", urgencyColors[proposal.urgency])}>
            {proposal.urgency === 'overdue' ? 'Overdue' :
             proposal.urgency === 'today' ? 'Due Today' : 'Upcoming'}
          </Badge>
        )}
        <ChevronRight className="h-4 w-4 text-slate-400 shrink-0" />
      </div>
    </Link>
  )
}

// Suggestion Item Component
function SuggestionItem({ suggestion }: { suggestion: MyDaySuggestion }) {
  const typeColors: Record<string, string> = {
    email_link: 'bg-blue-100 text-blue-700',
    follow_up_needed: 'bg-amber-100 text-amber-700',
    new_contact: 'bg-emerald-100 text-emerald-700',
    status_update: 'bg-purple-100 text-purple-700',
  }

  return (
    <Link href={`/admin/suggestions`}>
      <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-100 hover:bg-slate-50 hover:border-amber-200 transition-colors cursor-pointer">
        <Lightbulb className="h-4 w-4 text-amber-500 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className={cn(ds.typography.body, ds.textColors.primary, "truncate")}>
            {suggestion.title}
          </p>
          {suggestion.project_code && (
            <p className={cn(ds.typography.caption, "text-teal-600")}>
              {suggestion.project_code}
            </p>
          )}
        </div>
        <Badge variant="outline" className={cn("shrink-0 text-xs", typeColors[suggestion.suggestion_type] || 'bg-slate-100')}>
          {suggestion.suggestion_type.replace('_', ' ')}
        </Badge>
      </div>
    </Link>
  )
}
