"use client"

import { useParams } from 'next/navigation'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, ProjectTimelineEmail } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Mail, Paperclip, TrendingUp, Calendar, FileText, Check, ArrowLeft, AlertCircle } from 'lucide-react'
import Link from 'next/link'
import { EmailDetailsPanel } from '@/components/emails/email-details-panel'

export default function ProjectEmailsPage() {
  const params = useParams()
  const projectCode = decodeURIComponent(params.projectCode as string)
  const [selectedEmailId, setSelectedEmailId] = useState<number | null>(null)
  const [detailsPanelOpen, setDetailsPanelOpen] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['project-email-timeline', projectCode],
    queryFn: () => api.getProjectEmailTimeline(projectCode, {
      include_attachments: true,
      include_threads: true
    })
  })

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  const formatMonthYear = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown'
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long'
      })
    } catch {
      return 'Unknown'
    }
  }

  const parseKeyPoints = (keyPoints: string | null): string[] => {
    if (!keyPoints) return []
    try {
      return JSON.parse(keyPoints)
    } catch {
      return []
    }
  }

  const handleViewDetails = (emailId: number) => {
    setSelectedEmailId(emailId)
    setDetailsPanelOpen(true)
  }

  // Group emails by month
  const emailsByMonth: Record<string, ProjectTimelineEmail[]> = {}
  const emails = data?.emails || []

  emails.forEach((email) => {
    const month = formatMonthYear(email.date)
    if (!emailsByMonth[month]) {
      emailsByMonth[month] = []
    }
    emailsByMonth[month].push(email)
  })

  const project = data?.project
  const stats = data?.stats

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">Loading email history...</div>
      </div>
    )
  }

  if (error || !data?.success) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12 text-red-600">
          Failed to load email history. Make sure the project code is correct.
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <Link href={`/projects/${encodeURIComponent(projectCode)}`}>
          <Button variant="ghost" size="sm" className="mb-2">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Project
          </Button>
        </Link>

        <h1 className="text-3xl font-bold mb-2">
          {project?.code} - {project?.name}
        </h1>
        <p className="text-muted-foreground">Complete Email & Attachment History</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Mail className="h-4 w-4" />
              Total Emails
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_emails || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Paperclip className="h-4 w-4" />
              Attachments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_attachments || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Contracts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.contract_count || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Design Docs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.design_doc_count || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Timeline */}
      {emails.length === 0 ? (
        <Card className="p-12 text-center text-muted-foreground">
          No emails linked to this project yet.
        </Card>
      ) : (
        <div className="space-y-8">
          {Object.entries(emailsByMonth).map(([month, monthEmails]) => (
            <div key={month}>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                <span>{month}</span>
                <Badge variant="outline">{monthEmails.length} emails</Badge>
              </h2>

              <div className="space-y-3 ml-4 border-l-2 border-gray-200 pl-4">
                {monthEmails.map((email) => (
                  <div key={email.email_id} className="relative">
                    <div className="absolute -left-[25px] top-2 w-4 h-4 rounded-full bg-primary" />

                    <Card
                      className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => handleViewDetails(email.email_id)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            <h3 className="font-medium">{email.subject || '(No subject)'}</h3>
                            {email.thread_position && email.total_in_thread && email.total_in_thread > 1 && (
                              <Badge variant="outline" className="text-xs">
                                Thread: {email.thread_position}/{email.total_in_thread}
                              </Badge>
                            )}
                            {email.action_required === 1 && (
                              <Badge className="bg-purple-100 text-purple-800 text-xs">
                                <AlertCircle className="h-3 w-3 mr-1" />
                                Action Required
                              </Badge>
                            )}
                          </div>

                          <div className="text-sm text-muted-foreground">
                            From: {email.sender_email} | {formatDate(email.date)}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 flex-shrink-0">
                          {email.category && (
                            <Badge variant="secondary">{email.category}</Badge>
                          )}
                          {email.urgency_level && email.urgency_level !== 'low' && (
                            <Badge className={`text-xs ${
                              email.urgency_level === 'critical' ? 'bg-red-100 text-red-800' :
                              email.urgency_level === 'high' ? 'bg-orange-100 text-orange-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {email.urgency_level}
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* AI Summary */}
                      {email.ai_summary && (
                        <div className="mt-2 p-2 bg-blue-50 rounded text-sm flex items-start gap-2">
                          <TrendingUp className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                          <span>{email.ai_summary}</span>
                        </div>
                      )}

                      {/* Key Points */}
                      {email.key_points && parseKeyPoints(email.key_points).length > 0 && (
                        <div className="mt-2 text-sm">
                          <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                            {parseKeyPoints(email.key_points).slice(0, 3).map((point, i) => (
                              <li key={i}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Attachments */}
                      {email.attachments && email.attachments.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {email.attachments.map((att) => (
                            <Badge key={att.attachment_id} variant="outline" className="text-xs">
                              <Paperclip className="h-3 w-3 mr-1" />
                              {att.filename}
                              {att.is_signed && (
                                <Check className="h-3 w-3 ml-1 text-green-600" />
                              )}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </Card>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Email Details Panel */}
      <EmailDetailsPanel
        emailId={selectedEmailId}
        open={detailsPanelOpen}
        onOpenChange={setDetailsPanelOpen}
      />
    </div>
  )
}
