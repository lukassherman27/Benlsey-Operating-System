"use client"

import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Calendar, Clock, Video, Phone, Users } from "lucide-react"
import { cn } from "@/lib/utils"

interface Meeting {
  email_id: number
  subject: string
  meeting_type: string
  sender: string
  email_date: string
  snippet: string | null
  ai_summary: string | null
  project_code: string | null
  project_title: string | null
}

interface MeetingsResponse {
  success: boolean
  meetings: Meeting[]
  count: number
  type_breakdown: Record<string, number>
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export function MeetingsWidget() {
  const { data, isLoading, error } = useQuery<MeetingsResponse>({
    queryKey: ["dashboard-meetings"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/meetings?limit=5`)
      if (!res.ok) throw new Error("Failed to fetch meetings")
      return res.json()
    },
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  })

  const getMeetingIcon = (type: string) => {
    switch (type) {
      case 'Zoom Call':
      case 'Teams Meeting':
        return Video
      case 'Call':
        return Phone
      default:
        return Users
    }
  }

  const getMeetingColor = (type: string) => {
    switch (type) {
      case 'Zoom Call':
        return 'bg-blue-100 text-blue-800'
      case 'Teams Meeting':
        return 'bg-purple-100 text-purple-800'
      case 'Call':
        return 'bg-green-100 text-green-800'
      case 'Kick-off Meeting':
        return 'bg-orange-100 text-orange-800'
      case 'Review Meeting':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown date'
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Meetings & Calls
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading meetings...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Meetings & Calls
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Error loading meetings</p>
        </CardContent>
      </Card>
    )
  }

  const meetings = data?.meetings || []

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Meetings & Calls
          </CardTitle>
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3" />
            {meetings.length} recent
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {meetings.length === 0 ? (
          <div className="text-center py-8">
            <div className="rounded-lg bg-slate-100 p-4 inline-flex mb-3">
              <Calendar className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground">
              No meeting-related emails found
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {meetings.map((meeting) => {
              const Icon = getMeetingIcon(meeting.meeting_type)
              return (
                <div
                  key={meeting.email_id}
                  className="p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className={cn(
                      "p-2 rounded-lg",
                      getMeetingColor(meeting.meeting_type)
                    )}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="font-medium text-sm truncate">
                          {meeting.subject}
                        </h4>
                        <Badge variant="outline" className="text-xs flex-shrink-0">
                          {meeting.meeting_type}
                        </Badge>
                      </div>

                      {meeting.project_title && (
                        <p className="text-xs text-blue-600 mt-0.5">
                          {meeting.project_code} - {meeting.project_title}
                        </p>
                      )}

                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <span>{meeting.sender}</span>
                        <span className="text-slate-300">|</span>
                        <span>{formatDate(meeting.email_date)}</span>
                      </div>

                      {meeting.ai_summary && (
                        <p className="text-xs text-gray-600 mt-2 line-clamp-2 bg-blue-50 p-2 rounded">
                          {meeting.ai_summary}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Type breakdown */}
        {data?.type_breakdown && Object.keys(data.type_breakdown).length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-muted-foreground mb-2">By Type</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(data.type_breakdown).map(([type, count]) => (
                <Badge
                  key={type}
                  variant="outline"
                  className={cn("text-xs", getMeetingColor(type))}
                >
                  {type}: {count}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
