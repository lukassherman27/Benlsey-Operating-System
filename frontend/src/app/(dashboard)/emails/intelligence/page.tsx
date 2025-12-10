"use client"

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Check, Edit, X, Link as LinkIcon, Mail, Paperclip, AlertCircle } from 'lucide-react'
import { EmailLinkDialog } from '@/components/emails/email-link-dialog'
import { EmailDetailsPanel } from '@/components/emails/email-details-panel'

export default function EmailIntelligencePage() {
  const [statusFilter, setStatusFilter] = useState<'all' | 'unlinked' | 'low_confidence'>('all')
  const [search, setSearch] = useState('')
  const [selectedEmailId, setSelectedEmailId] = useState<number | null>(null)
  const [detailsPanelOpen, setDetailsPanelOpen] = useState(false)
  const [linkDialogOpen, setLinkDialogOpen] = useState(false)
  const [emailToLink, setEmailToLink] = useState<number | null>(null)

  const queryClient = useQueryClient()

  // Fetch validation queue
  const { data, isLoading, error } = useQuery({
    queryKey: ['email-validation-queue', statusFilter],
    queryFn: () => api.getEmailValidationQueue({ status: statusFilter, limit: 100 })
  })

  // Confirm link mutation
  const confirmLink = useMutation({
    mutationFn: (emailId: number) => api.confirmEmailLink(emailId, 'bill'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-validation-queue'] })
    }
  })

  // Unlink mutation
  const unlinkEmail = useMutation({
    mutationFn: ({ emailId, reason }: { emailId: number; reason: string }) =>
      api.unlinkEmailIntelligence(emailId, reason, 'bill'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-validation-queue'] })
    }
  })

  const emails = data?.emails || []
  const counts = data?.counts || { unlinked: 0, low_confidence: 0, total_linked: 0 }

  // Filter by search
  const filteredEmails = emails.filter((email) =>
    email.subject?.toLowerCase().includes(search.toLowerCase()) ||
    email.sender_email?.toLowerCase().includes(search.toLowerCase()) ||
    email.project_code?.toLowerCase().includes(search.toLowerCase())
  )

  const getConfidenceBadge = (confidence: number | null | undefined) => {
    if (!confidence) return { emoji: '', text: 'N/A', className: 'bg-gray-100 text-gray-800' }
    if (confidence >= 0.85) return { emoji: '', text: `${Math.round(confidence * 100)}%`, className: 'bg-green-100 text-green-800' }
    if (confidence >= 0.70) return { emoji: '', text: `${Math.round(confidence * 100)}%`, className: 'bg-yellow-100 text-yellow-800' }
    return { emoji: '', text: `${Math.round(confidence * 100)}%`, className: 'bg-red-100 text-red-800' }
  }

  const handleViewDetails = (emailId: number) => {
    setSelectedEmailId(emailId)
    setDetailsPanelOpen(true)
  }

  const handleLinkEmail = (emailId: number) => {
    setEmailToLink(emailId)
    setLinkDialogOpen(true)
  }

  const handleConfirmLink = (emailId: number) => {
    confirmLink.mutate(emailId)
  }

  const handleUnlink = (emailId: number) => {
    const reason = prompt('Why is this link wrong? (Required for AI training)')
    if (reason) {
      unlinkEmail.mutate({ emailId, reason })
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleDateString()
    } catch {
      return dateStr
    }
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Email Intelligence</h1>
        <p className="text-muted-foreground">
          Review AI-linked emails and correct mistakes to train the system
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Unlinked</div>
          <div className="text-2xl font-bold text-orange-600">{counts.unlinked}</div>
          <div className="text-xs text-muted-foreground">Need linking</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Low Confidence</div>
          <div className="text-2xl font-bold text-yellow-600">{counts.low_confidence}</div>
          <div className="text-xs text-muted-foreground">Need review</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Total Linked</div>
          <div className="text-2xl font-bold text-green-600">{counts.total_linked}</div>
          <div className="text-xs text-muted-foreground">Email-project links</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Shown</div>
          <div className="text-2xl font-bold">{filteredEmails.length}</div>
          <div className="text-xs text-muted-foreground">Current results</div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Emails</SelectItem>
            <SelectItem value="unlinked">Unlinked ({counts.unlinked})</SelectItem>
            <SelectItem value="low_confidence">Low Confidence ({counts.low_confidence})</SelectItem>
          </SelectContent>
        </Select>

        <Input
          placeholder="Search emails..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />

        <Button
          variant="outline"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['email-validation-queue'] })}
        >
          Refresh
        </Button>
      </div>

      {/* Email List */}
      {isLoading ? (
        <Card className="p-12 text-center">
          <div className="text-lg">Loading emails...</div>
        </Card>
      ) : error ? (
        <Card className="p-12 text-center">
          <div className="text-lg text-red-600">Failed to load emails</div>
        </Card>
      ) : filteredEmails.length === 0 ? (
        <Card className="p-12 text-center text-muted-foreground">
          No emails found matching your filters
        </Card>
      ) : (
        <div className="space-y-2">
          {filteredEmails.map((email) => (
            <Card
              key={email.email_id}
              className="p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <h3
                      className="font-medium truncate cursor-pointer hover:text-primary"
                      onClick={() => handleViewDetails(email.email_id)}
                    >
                      {email.subject || '(No subject)'}
                    </h3>
                    {email.has_attachments === 1 && (
                      <Badge variant="outline" className="text-xs flex-shrink-0">
                        <Paperclip className="h-3 w-3 mr-1" />
                        {email.attachment_count}
                      </Badge>
                    )}
                    {email.urgency_level && email.urgency_level !== 'low' && (
                      <Badge className={`text-xs ${
                        email.urgency_level === 'critical' ? 'bg-red-100 text-red-800' :
                        email.urgency_level === 'high' ? 'bg-orange-100 text-orange-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        <AlertCircle className="h-3 w-3 mr-1" />
                        {email.urgency_level}
                      </Badge>
                    )}
                  </div>

                  <div className="text-sm text-muted-foreground">
                    From: {email.sender_email} | {formatDate(email.date)}
                  </div>

                  {email.ai_summary && (
                    <div className="mt-1 text-sm text-gray-600 bg-blue-50 p-2 rounded">
                      {email.ai_summary}
                    </div>
                  )}

                  {email.project_code && (
                    <div className="mt-2 flex items-center gap-2 flex-wrap">
                      <Badge variant="secondary">
                        {email.project_code} - {email.project_name}
                      </Badge>
                      {email.confidence && (
                        <Badge className={getConfidenceBadge(email.confidence).className}>
                          {getConfidenceBadge(email.confidence).text}
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        ({email.link_method})
                      </span>
                    </div>
                  )}

                  {!email.project_code && (
                    <div className="mt-2">
                      <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
                        Not linked to any project
                      </Badge>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-1 flex-shrink-0">
                  {email.project_code ? (
                    <>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleConfirmLink(email.email_id)}
                        disabled={confirmLink.isPending}
                        title="Confirm correct"
                      >
                        <Check className="h-4 w-4 text-green-600" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleLinkEmail(email.email_id)}
                        title="Change link"
                      >
                        <Edit className="h-4 w-4 text-blue-600" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleUnlink(email.email_id)}
                        disabled={unlinkEmail.isPending}
                        title="Unlink"
                      >
                        <X className="h-4 w-4 text-red-600" />
                      </Button>
                    </>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleLinkEmail(email.email_id)}
                    >
                      <LinkIcon className="h-4 w-4 mr-1" />
                      Link
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Email Link Dialog */}
      <EmailLinkDialog
        open={linkDialogOpen}
        onOpenChange={setLinkDialogOpen}
        emailId={emailToLink}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['email-validation-queue'] })
        }}
      />

      {/* Email Details Panel */}
      <EmailDetailsPanel
        emailId={selectedEmailId}
        open={detailsPanelOpen}
        onOpenChange={setDetailsPanelOpen}
      />
    </div>
  )
}
