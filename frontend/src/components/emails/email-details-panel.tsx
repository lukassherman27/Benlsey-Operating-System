"use client"

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Check, Clock, FileText, Mail, AlertCircle, User } from 'lucide-react'

interface EmailDetailsPanelProps {
  emailId: number | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function EmailDetailsPanel({ emailId, open, onOpenChange }: EmailDetailsPanelProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['email-details', emailId],
    queryFn: () => emailId ? api.getEmailDetails(emailId) : null,
    enabled: !!emailId && open
  })

  const email = data?.email

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleString()
    } catch {
      return dateStr
    }
  }

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return 'N/A'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const parseKeyPoints = (keyPoints: string | null): string[] => {
    if (!keyPoints) return []
    try {
      return JSON.parse(keyPoints)
    } catch {
      return []
    }
  }

  const getSentimentColor = (sentiment: string | null) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'bg-green-100 text-green-800'
      case 'negative': return 'bg-red-100 text-red-800'
      case 'concerned': return 'bg-orange-100 text-orange-800'
      case 'urgent': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getUrgencyColor = (urgency: string | null) => {
    switch (urgency?.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getConfidenceColor = (confidence: number | null | undefined) => {
    if (!confidence) return 'text-gray-500'
    if (confidence >= 0.85) return 'text-green-600'
    if (confidence >= 0.70) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto w-full sm:max-w-[600px]">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-muted-foreground">Loading email details...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-red-500">Failed to load email details</div>
          </div>
        ) : email ? (
          <>
            <SheetHeader>
              <SheetTitle className="pr-8 text-left">
                {email.subject || '(No subject)'}
              </SheetTitle>
              <SheetDescription className="text-left">
                <div className="flex items-center gap-2 mt-1">
                  <User className="h-3 w-3" />
                  <span>{email.sender_email}</span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="h-3 w-3" />
                  <span>{formatDate(email.date)}</span>
                </div>
              </SheetDescription>
            </SheetHeader>

            <div className="mt-6 space-y-6">
              {/* Current Link */}
              {email.project_code && (
                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    Current Link
                  </h3>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="font-medium">
                      {email.project_code} - {email.project_name}
                    </div>
                    <div className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
                      <span>Confidence:</span>
                      <span className={`font-bold ${getConfidenceColor(email.confidence)}`}>
                        {email.confidence ? `${Math.round(email.confidence * 100)}%` : 'N/A'}
                      </span>
                      <span className="text-xs">({email.link_method || 'unknown'})</span>
                    </div>
                    {email.evidence && (
                      <div className="text-xs text-muted-foreground mt-1 bg-gray-100 p-2 rounded">
                        Evidence: {email.evidence}
                      </div>
                    )}
                  </div>
                </div>
              )}

              <Separator />

              {/* AI Insights */}
              {email.ai_insights && (
                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    AI Insights
                  </h3>
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      {email.ai_insights.category && (
                        <Badge variant="secondary">
                          {email.ai_insights.category}
                          {email.ai_insights.subcategory && ` / ${email.ai_insights.subcategory}`}
                        </Badge>
                      )}

                      {email.ai_insights.sentiment && (
                        <Badge className={getSentimentColor(email.ai_insights.sentiment)}>
                          {email.ai_insights.sentiment}
                        </Badge>
                      )}

                      {email.ai_insights.urgency_level && (
                        <Badge className={getUrgencyColor(email.ai_insights.urgency_level)}>
                          {email.ai_insights.urgency_level}
                        </Badge>
                      )}

                      {email.ai_insights.action_required === 1 && (
                        <Badge className="bg-purple-100 text-purple-800">
                          Action Required
                        </Badge>
                      )}
                    </div>

                    {email.ai_insights.ai_summary && (
                      <div>
                        <div className="text-sm text-muted-foreground mb-1">Summary:</div>
                        <p className="text-sm bg-blue-50 p-2 rounded">{email.ai_insights.ai_summary}</p>
                      </div>
                    )}

                    {email.ai_insights.key_points && parseKeyPoints(email.ai_insights.key_points).length > 0 && (
                      <div>
                        <div className="text-sm text-muted-foreground mb-1">Key Points:</div>
                        <ul className="list-disc list-inside text-sm space-y-1">
                          {parseKeyPoints(email.ai_insights.key_points).map((point, i) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <Separator />

              {/* Attachments */}
              {email.attachments && email.attachments.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Attachments ({email.attachments.length})
                  </h3>
                  <div className="space-y-2">
                    {email.attachments.map((att) => (
                      <div
                        key={att.attachment_id}
                        className="flex items-start gap-2 p-2 bg-gray-50 rounded"
                      >
                        <FileText className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{att.filename}</div>
                          <div className="text-xs text-muted-foreground">
                            {formatFileSize(att.filesize)}
                            {att.document_type && ` \u2022 ${att.document_type}`}
                          </div>
                          {(att.is_signed || att.is_executed) && (
                            <div className="flex gap-1 mt-1">
                              {att.is_signed && (
                                <Badge variant="default" className="text-xs bg-green-600">
                                  <Check className="h-3 w-3 mr-1" />
                                  Signed
                                </Badge>
                              )}
                              {att.is_executed && (
                                <Badge variant="default" className="text-xs bg-blue-600">
                                  <Check className="h-3 w-3 mr-1" />
                                  Executed
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <Separator />

              {/* Thread Info */}
              {email.thread && (
                <div>
                  <h3 className="font-semibold mb-2">Email Thread</h3>
                  <div className="text-sm space-y-1 p-3 bg-gray-50 rounded-lg">
                    <div>Messages: <span className="font-medium">{email.thread.message_count}</span></div>
                    {email.thread.status && (
                      <div>Status: <Badge variant="outline">{email.thread.status}</Badge></div>
                    )}
                    {email.thread.first_email_date && (
                      <div className="text-xs text-muted-foreground">
                        First: {formatDate(email.thread.first_email_date)}
                      </div>
                    )}
                    {email.thread.last_email_date && (
                      <div className="text-xs text-muted-foreground">
                        Last: {formatDate(email.thread.last_email_date)}
                      </div>
                    )}
                  </div>
                </div>
              )}

              <Separator />

              {/* Full Email Body */}
              <div>
                <h3 className="font-semibold mb-2">Email Body</h3>
                <div className="p-3 bg-gray-50 rounded-lg text-sm whitespace-pre-wrap max-h-[400px] overflow-y-auto">
                  {email.body_full || email.body_preview || email.snippet || 'No content available'}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  )
}
