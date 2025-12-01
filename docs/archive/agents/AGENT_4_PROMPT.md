# AGENT 4: Frontend Email Components

**Your Mission:** Build 4 reusable React components for email functionality

**What You're Building:**
1. Email Detail Modal - Full email view with AI insights
2. Email Thread Viewer - Gmail-style conversation view
3. Email List Component - Reusable list with search/filters
4. Email Activity Widget - Recent email summary for dashboard

**CRITICAL RULES:**
- ✅ Create all components in `frontend/src/components/emails/`
- ✅ Use existing shadcn/ui components
- ✅ Use TanStack Query for data fetching
- ✅ Follow existing component patterns
- ❌ DO NOT install new packages
- ❌ DO NOT modify existing components outside `/emails` folder

**Dependencies:** Wait for Agent 3 (needs API endpoints)

---

## Component 1: Email Detail Modal

Create `frontend/src/components/emails/email-detail-modal.tsx`:

```tsx
"use client"

import { useQuery } from "@tanstack/react-query"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Mail, Calendar, User, Link2 } from "lucide-react"
import { api } from "@/lib/api"

interface EmailDetailModalProps {
  emailId: number | null
  isOpen: boolean
  onClose: () => void
}

export function EmailDetailModal({ emailId, isOpen, onClose }: EmailDetailModalProps) {
  const { data: email, isLoading } = useQuery({
    queryKey: ['email-detail', emailId],
    queryFn: () => api.getEmailDetail(emailId!),
    enabled: !!emailId && isOpen
  })

  if (!emailId) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5" />
            {email?.subject || "Email Detail"}
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground">Loading email...</div>
        ) : email ? (
          <div className="space-y-6">
            {/* Email Metadata */}
            <div className="space-y-2 border-b pb-4">
              <div className="flex items-center gap-2 text-sm">
                <User className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium">From:</span>
                <span>{email.sender_email}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium">Date:</span>
                <span>{new Date(email.date).toLocaleString()}</span>
              </div>
            </div>

            {/* AI Insights Panel */}
            {email.ai_summary && (
              <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4 space-y-3">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5" />
                  <div className="flex-1 space-y-2">
                    <div>
                      <span className="font-semibold text-blue-900 dark:text-blue-100">AI Summary</span>
                      <p className="text-sm text-blue-800 dark:text-blue-200 mt-1">{email.ai_summary}</p>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {email.sentiment && (
                        <Badge variant={
                          email.sentiment === 'positive' ? 'success' :
                          email.sentiment === 'negative' ? 'destructive' : 'secondary'
                        }>
                          {email.sentiment}
                        </Badge>
                      )}
                      {email.category && (
                        <Badge variant="outline">{email.category}</Badge>
                      )}
                      {email.urgency_level && (
                        <Badge variant={email.urgency_level === 'urgent' ? 'destructive' : 'secondary'}>
                          {email.urgency_level} urgency
                        </Badge>
                      )}
                      {email.action_required && (
                        <Badge variant="warning">Action Required</Badge>
                      )}
                    </div>

                    {email.key_points && email.key_points.length > 0 && (
                      <div>
                        <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">Key Points:</p>
                        <ul className="text-sm text-blue-800 dark:text-blue-200 list-disc list-inside space-y-1">
                          {email.key_points.map((point, i) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Linked Proposals */}
            {email.linked_proposals && email.linked_proposals.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Link2 className="w-4 h-4" />
                  Linked Proposals
                </div>
                <div className="space-y-2">
                  {email.linked_proposals.map((proposal) => (
                    <div
                      key={proposal.proposal_id}
                      className="flex items-center justify-between p-3 bg-muted rounded-lg"
                    >
                      <div>
                        <div className="font-medium">{proposal.project_code} - {proposal.project_name}</div>
                        <div className="text-sm text-muted-foreground">{proposal.client_name}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge>{proposal.current_status}</Badge>
                        <span className="text-xs text-muted-foreground">
                          {(proposal.confidence_score * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Email Body */}
            <div className="space-y-2">
              <div className="text-sm font-semibold">Email Content</div>
              <div className="bg-muted p-4 rounded-lg whitespace-pre-wrap text-sm">
                {email.clean_body || email.body_full}
              </div>
            </div>

            {/* Thread Info */}
            {email.thread && (
              <div className="text-sm text-muted-foreground">
                Part of thread with {email.thread.email_count} messages
              </div>
            )}
          </div>
        ) : (
          <div className="p-8 text-center text-muted-foreground">Email not found</div>
        )}
      </DialogContent>
    </Dialog>
  )
}
```

---

## Component 2: Email Thread Viewer

Create `frontend/src/components/emails/email-thread-viewer.tsx`:

```tsx
"use client"

import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, Calendar, User } from "lucide-react"
import { api } from "@/lib/api"

interface EmailThreadViewerProps {
  threadId: number
}

export function EmailThreadViewer({ threadId }: EmailThreadViewerProps) {
  const { data: thread, isLoading } = useQuery({
    queryKey: ['email-thread', threadId],
    queryFn: () => api.getEmailThread(threadId)
  })

  if (isLoading) {
    return <div className="text-muted-foreground">Loading thread...</div>
  }

  if (!thread) {
    return <div className="text-muted-foreground">Thread not found</div>
  }

  return (
    <div className="space-y-4">
      {/* Thread Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            {thread.thread_subject}
          </CardTitle>
          <div className="text-sm text-muted-foreground">
            {thread.email_count} messages •
            {new Date(thread.first_email_date).toLocaleDateString()} -
            {new Date(thread.last_email_date).toLocaleDateString()}
          </div>
        </CardHeader>
      </Card>

      {/* Thread Emails */}
      <div className="space-y-3">
        {thread.emails?.map((email, index) => (
          <Card key={email.email_id} className="relative">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-muted-foreground" />
                    <span className="font-medium">{email.sender_email}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="w-3 h-3" />
                    {new Date(email.date).toLocaleString()}
                  </div>
                </div>
                <div className="flex gap-2">
                  {email.category && <Badge variant="outline">{email.category}</Badge>}
                  {email.sentiment && (
                    <Badge variant={
                      email.sentiment === 'positive' ? 'success' : 'secondary'
                    }>
                      {email.sentiment}
                    </Badge>
                  )}
                </div>
              </div>

              {email.ai_summary && (
                <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-950 rounded-md">
                  <p className="text-sm text-blue-900 dark:text-blue-100">{email.ai_summary}</p>
                </div>
              )}

              <div className="text-sm whitespace-pre-wrap text-muted-foreground">
                {email.body_full?.substring(0, 300)}
                {email.body_full && email.body_full.length > 300 && "..."}
              </div>

              {/* Thread position indicator */}
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-l" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
```

---

## Component 3: Email List Component

Create `frontend/src/components/emails/email-list.tsx`:

```tsx
"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Search, Mail, Calendar } from "lucide-react"
import { api } from "@/lib/api"
import { EmailDetailModal } from "./email-detail-modal"

interface EmailListProps {
  proposalId?: number
  limit?: number
}

export function EmailList({ proposalId, limit = 50 }: EmailListProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedEmailId, setSelectedEmailId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['emails', searchQuery, proposalId],
    queryFn: () => api.searchEmails({ q: searchQuery, proposal_id: proposalId, limit })
  })

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search emails..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Results Count */}
      {data && (
        <div className="text-sm text-muted-foreground">
          {data.total} email{data.total !== 1 ? 's' : ''} found
        </div>
      )}

      {/* Email List */}
      {isLoading ? (
        <div className="text-center text-muted-foreground py-8">Loading emails...</div>
      ) : data && data.results.length > 0 ? (
        <div className="space-y-2">
          {data.results.map((email) => (
            <Card
              key={email.email_id}
              className="cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => setSelectedEmailId(email.email_id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Mail className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <h4 className="font-medium truncate">{email.subject}</h4>
                    </div>
                    <div className="text-sm text-muted-foreground mb-2">
                      From: {email.sender_email}
                    </div>
                    {email.ai_summary && (
                      <p className="text-sm text-muted-foreground line-clamp-2">{email.ai_summary}</p>
                    )}
                  </div>

                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Calendar className="w-3 h-3" />
                      {new Date(email.date).toLocaleDateString()}
                    </div>
                    <div className="flex flex-wrap gap-1 justify-end">
                      {email.category && <Badge variant="outline" className="text-xs">{email.category}</Badge>}
                      {email.urgency_level === 'urgent' && <Badge variant="destructive" className="text-xs">Urgent</Badge>}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center text-muted-foreground py-8">
          {searchQuery ? 'No emails found matching your search' : 'No emails found'}
        </div>
      )}

      {/* Email Detail Modal */}
      <EmailDetailModal
        emailId={selectedEmailId}
        isOpen={!!selectedEmailId}
        onClose={() => setSelectedEmailId(null)}
      />
    </div>
  )
}
```

---

## Component 4: Email Activity Widget

Create `frontend/src/components/emails/email-activity-widget.tsx`:

```tsx
"use client"

import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Mail, TrendingUp } from "lucide-react"
import { api } from "@/lib/api"

export function EmailActivityWidget() {
  const { data: recentEmails } = useQuery({
    queryKey: ['recent-emails'],
    queryFn: () => api.searchEmails({ limit: 5 })
  })

  const { data: actionRequiredEmails } = useQuery({
    queryKey: ['action-required-emails'],
    queryFn: () => api.searchEmails({ urgency: 'urgent', limit: 10 })
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mail className="w-5 h-5" />
          Recent Email Activity
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-2xl font-bold">{recentEmails?.total || 0}</div>
            <div className="text-xs text-muted-foreground">Total Emails</div>
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-bold text-orange-600">{actionRequiredEmails?.total || 0}</div>
            <div className="text-xs text-muted-foreground">Urgent</div>
          </div>
        </div>

        {/* Recent Emails */}
        <div className="space-y-2">
          <div className="text-sm font-semibold">Latest Messages</div>
          {recentEmails?.results.slice(0, 3).map((email) => (
            <div key={email.email_id} className="flex items-start gap-2 text-sm">
              <div className="w-2 h-2 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="truncate font-medium">{email.subject}</div>
                <div className="text-xs text-muted-foreground truncate">{email.sender_email}</div>
              </div>
              {email.category && <Badge variant="outline" className="text-xs">{email.category}</Badge>}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## Add API Methods to lib/api.ts

Add these methods to `frontend/src/lib/api.ts`:

```typescript
// Email endpoints
getEmailDetail: async (emailId: number) => {
  const response = await fetch(`${API_BASE_URL}/api/emails/${emailId}/detail`)
  if (!response.ok) throw new Error('Failed to fetch email')
  return response.json()
},

getEmailThread: async (threadId: number) => {
  const response = await fetch(`${API_BASE_URL}/api/emails/thread/${threadId}`)
  if (!response.ok) throw new Error('Failed to fetch thread')
  return response.json()
},

searchEmails: async (params: {
  q?: string
  category?: string
  sentiment?: string
  urgency?: string
  proposal_id?: number
  limit?: number
  offset?: number
}) => {
  const queryParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) queryParams.append(key, String(value))
  })

  const response = await fetch(`${API_BASE_URL}/api/emails/search?${queryParams}`)
  if (!response.ok) throw new Error('Failed to search emails')
  return response.json()
},
```

---

## SUCCESS CRITERIA

- ✅ All 4 components created in `frontend/src/components/emails/`
- ✅ Components render without errors
- ✅ EmailDetailModal shows AI insights and linked proposals
- ✅ EmailList supports search
- ✅ EmailActivityWidget shows recent emails
- ✅ API methods added to `lib/api.ts`

**Report back:** "Agent 4 complete. 4 email components created and tested."
