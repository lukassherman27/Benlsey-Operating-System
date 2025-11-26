# 📧 CLAUDE 6 - Email Intelligence UI System

**Created:** November 25, 2025
**Priority:** 🟡 HIGH - Foundation for Phase 2 RAG
**Timeline:** 4-6 hours

---

## Your Mission

Build the **Email Intelligence UI** - a system where Bill can:
1. Review AI-linked emails to projects
2. Correct wrong links (trains the AI!)
3. See complete email history per project
4. Validate unlinked emails and attachments

**Read:** `EMAIL_INTELLIGENCE_SYSTEM_EXPLAINED.md` for full context

---

## Context: The Problem You're Solving

Bill has **3,356 emails** imported into the system. An AI (`ai_email_linker.py`) automatically links emails to projects based on subject/body analysis. But the AI isn't perfect:

- Some links are wrong (email about "Bali branding" linked to "Bali resort")
- Some emails aren't linked at all (no project code in subject)
- Some have low confidence (AI guessed 60%)

**Bill needs to:**
- Review these AI links
- Correct mistakes → This trains the AI (RLHF!)
- Build complete project context for future queries

**Your job:** Build the UI for this workflow.

---

## Database Schema (Already Exists)

### Key Tables

**1. emails**
```sql
email_id, message_id, thread_id, date, sender_email, sender_name
subject, body_full, snippet, category, has_attachments, processed
ai_confidence, ai_extracted_data
```

**2. email_project_links** (THE CRITICAL ONE)
```sql
email_id       → Which email
project_id     → Which project
project_code   → '25-BK-018'
confidence     → 0.0 - 1.0 (AI confidence)
link_method    → 'ai' | 'manual' | 'alias' | 'subject_match'
evidence       → "Found '25-BK-018' in subject line"
created_at
```

**3. email_content** (AI Insights)
```sql
email_id
category         → contract/invoice/design/rfi/schedule/meeting/general
key_points       → JSON: ["fee discussion", "deadline set"]
sentiment        → positive/neutral/concerned/urgent
client_sentiment → positive/neutral/negative/frustrated
urgency_level    → low/medium/high/critical
action_required  → 0 or 1
ai_summary       → "Client approved design direction"
```

**4. email_attachments**
```sql
attachment_id, email_id, filename, filepath, filesize
document_type    → bensley_contract | invoice | proposal | design_document
is_signed, is_executed
ai_summary
```

**5. email_threads**
```sql
thread_id, subject_normalized, proposal_id
emails           → JSON: [email_id, email_id, ...]
status           → open | resolved | waiting
```

**6. training_data** (For RLHF)
```sql
feature_type, feature_id, helpful
issue_type, feedback_text, expected_value, current_value, context_json
```

---

## What You're Building

### 3 Main Features

1. **Email Links Tab** - Review all AI-linked emails
2. **Validation Queue** - Priority list (unlinked, low confidence)
3. **Project Email Timeline** - Complete email history for one project

---

## Part 1: Backend API Endpoints

Create these in `backend/api/main.py` or a new `backend/services/email_intelligence_service.py`

### Endpoint 1: Get Validation Queue

```python
@app.get("/api/emails/validation-queue")
async def get_email_validation_queue(
    priority: Optional[str] = Query(None, description="high|medium|low|all"),
    status: Optional[str] = Query(None, description="unlinked|low_confidence|all"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get emails needing validation

    Priority levels:
    - high: Unlinked emails with attachments (contracts!)
    - medium: Low confidence links (<70%)
    - low: Medium confidence links (70-85%)

    Returns emails with:
    - Current link (if exists)
    - AI insights
    - Attachments
    - Suggested actions
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build query based on filters
    where_clauses = []
    params = []

    if status == "unlinked":
        # Emails with no project link
        sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.has_attachments,
                e.category,
                COUNT(ea.attachment_id) as attachment_count
            FROM emails e
            LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
            LEFT JOIN email_attachments ea ON e.email_id = ea.email_id
            WHERE epl.email_id IS NULL
            GROUP BY e.email_id
            ORDER BY e.has_attachments DESC, e.date DESC
            LIMIT ?
        """
        params = [limit]

    elif status == "low_confidence":
        # Emails with AI links below 70% confidence
        sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                epl.project_code,
                p.name as project_name,
                epl.confidence,
                epl.link_method,
                epl.evidence,
                COUNT(ea.attachment_id) as attachment_count
            FROM emails e
            INNER JOIN email_project_links epl ON e.email_id = epl.email_id
            LEFT JOIN projects p ON epl.project_code = p.code
            LEFT JOIN email_attachments ea ON e.email_id = ea.email_id
            WHERE epl.confidence < 0.70
            GROUP BY e.email_id
            ORDER BY epl.confidence ASC, e.date DESC
            LIMIT ?
        """
        params = [limit]

    else:  # all
        sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                epl.project_code,
                p.name as project_name,
                epl.confidence,
                epl.link_method,
                COUNT(ea.attachment_id) as attachment_count
            FROM emails e
            LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
            LEFT JOIN projects p ON epl.project_code = p.code
            LEFT JOIN email_attachments ea ON e.email_id = ea.email_id
            GROUP BY e.email_id
            ORDER BY e.date DESC
            LIMIT ?
        """
        params = [limit]

    cursor.execute(sql, params)
    emails = [dict(row) for row in cursor.fetchall()]

    # Get counts for summary
    cursor.execute("""
        SELECT COUNT(*) as unlinked
        FROM emails e
        LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
        WHERE epl.email_id IS NULL
    """)
    unlinked_count = cursor.fetchone()['unlinked']

    cursor.execute("""
        SELECT COUNT(*) as low_conf
        FROM email_project_links
        WHERE confidence < 0.70
    """)
    low_conf_count = cursor.fetchone()['low_conf']

    conn.close()

    return {
        "success": True,
        "counts": {
            "unlinked": unlinked_count,
            "low_confidence": low_conf_count,
            "total": len(emails)
        },
        "emails": emails
    }
```

### Endpoint 2: Get Email Details

```python
@app.get("/api/emails/{email_id}")
async def get_email_details(email_id: int):
    """
    Get complete email details including:
    - Basic email data
    - Current project link (if exists)
    - AI insights from email_content
    - Attachments
    - Thread information
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get email basics
    cursor.execute("""
        SELECT
            e.*,
            epl.project_code,
            p.name as project_name,
            epl.confidence,
            epl.link_method,
            epl.evidence
        FROM emails e
        LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
        LEFT JOIN projects p ON epl.project_code = p.code
        WHERE e.email_id = ?
    """, (email_id,))

    email = dict(cursor.fetchone())

    # Get AI insights
    cursor.execute("""
        SELECT category, key_points, sentiment, client_sentiment,
               urgency_level, action_required, ai_summary
        FROM email_content
        WHERE email_id = ?
    """, (email_id,))

    content_row = cursor.fetchone()
    email['ai_insights'] = dict(content_row) if content_row else None

    # Get attachments
    cursor.execute("""
        SELECT attachment_id, filename, filesize, document_type,
               is_signed, is_executed, ai_summary
        FROM email_attachments
        WHERE email_id = ?
    """, (email_id,))

    email['attachments'] = [dict(row) for row in cursor.fetchall()]

    # Get thread info
    cursor.execute("""
        SELECT thread_id, subject_normalized, message_count, status
        FROM email_threads
        WHERE emails LIKE '%' || ? || '%'
    """, (email_id,))

    thread_row = cursor.fetchone()
    email['thread'] = dict(thread_row) if thread_row else None

    conn.close()

    return {"success": True, "email": email}
```

### Endpoint 3: Update Email Link

```python
class EmailLinkUpdate(BaseModel):
    project_code: str
    reason: str
    updated_by: str = "bill"

@app.patch("/api/emails/{email_id}/link")
async def update_email_link(email_id: int, update: EmailLinkUpdate):
    """
    Update email's project link

    This does 3 things:
    1. Updates email_project_links
    2. Logs to training_data (RLHF!)
    3. Returns success
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current link (if exists)
    cursor.execute("""
        SELECT project_code, confidence
        FROM email_project_links
        WHERE email_id = ?
    """, (email_id,))

    current = cursor.fetchone()
    old_project_code = dict(current)['project_code'] if current else None

    # Get project_id from project_code
    cursor.execute("""
        SELECT project_id FROM projects WHERE code = ?
    """, (update.project_code,))

    project = cursor.fetchone()
    if not project:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Project {update.project_code} not found")

    project_id = dict(project)['project_id']

    # Delete old link
    if current:
        cursor.execute("""
            DELETE FROM email_project_links
            WHERE email_id = ?
        """, (email_id,))

    # Insert new link
    cursor.execute("""
        INSERT INTO email_project_links
        (email_id, project_id, project_code, confidence, link_method, evidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (email_id, project_id, update.project_code, 1.0, 'manual', update.reason))

    # Log to training_data for RLHF
    training_service = TrainingDataService()
    training_service.log_feedback(
        feature_type='email_project_linking',
        feature_id=str(email_id),
        helpful=False,  # AI was wrong
        issue_type='incorrect_project',
        feedback_text=update.reason,
        expected_value=update.project_code,
        current_value=old_project_code or 'unlinked',
        context={
            'email_id': email_id,
            'old_project': old_project_code,
            'new_project': update.project_code,
            'updated_by': update.updated_by
        }
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Email linked to {update.project_code}",
        "training_logged": True
    }
```

### Endpoint 4: Confirm AI Link

```python
@app.post("/api/emails/{email_id}/confirm-link")
async def confirm_email_link(email_id: int, confirmed_by: str = "bill"):
    """
    Confirm AI link is correct

    This:
    1. Sets confidence to 1.0
    2. Logs positive feedback to training_data
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current link
    cursor.execute("""
        SELECT project_code, confidence, link_method
        FROM email_project_links
        WHERE email_id = ?
    """, (email_id,))

    link = cursor.fetchone()
    if not link:
        conn.close()
        raise HTTPException(status_code=404, detail="No link found for this email")

    link_dict = dict(link)

    # Update confidence to 1.0
    cursor.execute("""
        UPDATE email_project_links
        SET confidence = 1.0
        WHERE email_id = ?
    """, (email_id,))

    # Log positive feedback
    training_service = TrainingDataService()
    training_service.log_feedback(
        feature_type='email_project_linking',
        feature_id=str(email_id),
        helpful=True,  # AI was correct!
        current_value=link_dict['project_code'],
        context={
            'email_id': email_id,
            'project_code': link_dict['project_code'],
            'original_confidence': link_dict['confidence'],
            'confirmed_by': confirmed_by
        }
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Link confirmed",
        "training_logged": True
    }
```

### Endpoint 5: Get Project Email Timeline

```python
@app.get("/api/projects/{project_code}/emails")
async def get_project_email_timeline(
    project_code: str,
    include_attachments: bool = True,
    include_threads: bool = True
):
    """
    Get complete email history for a project

    Returns:
    - All emails linked to this project
    - Sorted chronologically
    - With AI summaries, key points
    - Attachments
    - Thread grouping
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all emails for this project
    cursor.execute("""
        SELECT
            e.email_id,
            e.subject,
            e.sender_email,
            e.sender_name,
            e.date,
            e.snippet,
            e.thread_id,
            ec.category,
            ec.ai_summary,
            ec.key_points,
            ec.sentiment,
            ec.action_required,
            epl.confidence,
            epl.link_method
        FROM emails e
        INNER JOIN email_project_links epl ON e.email_id = epl.email_id
        LEFT JOIN email_content ec ON e.email_id = ec.email_id
        WHERE epl.project_code = ?
        ORDER BY e.date DESC
    """, (project_code,))

    emails = [dict(row) for row in cursor.fetchall()]

    # Get attachments if requested
    if include_attachments:
        for email in emails:
            cursor.execute("""
                SELECT attachment_id, filename, filesize, document_type,
                       is_signed, is_executed
                FROM email_attachments
                WHERE email_id = ?
            """, (email['email_id'],))
            email['attachments'] = [dict(row) for row in cursor.fetchall()]

    # Get thread info if requested
    if include_threads:
        # Group emails by thread
        threads = {}
        for email in emails:
            thread_id = email.get('thread_id')
            if thread_id:
                if thread_id not in threads:
                    threads[thread_id] = []
                threads[thread_id].append(email['email_id'])

        for email in emails:
            thread_id = email.get('thread_id')
            if thread_id and thread_id in threads:
                email['thread_position'] = threads[thread_id].index(email['email_id']) + 1
                email['total_in_thread'] = len(threads[thread_id])

    # Get project info
    cursor.execute("""
        SELECT code, name, project_value, status
        FROM projects
        WHERE code = ?
    """, (project_code,))

    project = dict(cursor.fetchone())

    # Get stats
    cursor.execute("""
        SELECT
            COUNT(DISTINCT e.email_id) as total_emails,
            COUNT(DISTINCT ea.attachment_id) as total_attachments,
            SUM(CASE WHEN ea.document_type = 'bensley_contract' THEN 1 ELSE 0 END) as contract_count,
            SUM(CASE WHEN ea.document_type = 'design_document' THEN 1 ELSE 0 END) as design_doc_count
        FROM emails e
        INNER JOIN email_project_links epl ON e.email_id = epl.email_id
        LEFT JOIN email_attachments ea ON e.email_id = ea.email_id
        WHERE epl.project_code = ?
    """, (project_code,))

    stats = dict(cursor.fetchone())

    conn.close()

    return {
        "success": True,
        "project": project,
        "emails": emails,
        "stats": stats
    }
```

### Endpoint 6: Unlink Email

```python
@app.delete("/api/emails/{email_id}/link")
async def unlink_email(email_id: int, reason: str, updated_by: str = "bill"):
    """
    Remove project link from email

    Logs to training_data that AI was wrong
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current link
    cursor.execute("""
        SELECT project_code
        FROM email_project_links
        WHERE email_id = ?
    """, (email_id,))

    link = cursor.fetchone()
    if not link:
        conn.close()
        raise HTTPException(status_code=404, detail="No link to remove")

    old_project = dict(link)['project_code']

    # Delete link
    cursor.execute("""
        DELETE FROM email_project_links
        WHERE email_id = ?
    """, (email_id,))

    # Log to training_data
    training_service = TrainingDataService()
    training_service.log_feedback(
        feature_type='email_project_linking',
        feature_id=str(email_id),
        helpful=False,
        issue_type='wrong_project',
        feedback_text=reason,
        current_value=old_project,
        expected_value='unlinked',
        context={
            'email_id': email_id,
            'removed_project': old_project,
            'updated_by': updated_by
        }
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Email unlinked",
        "training_logged": True
    }
```

---

## Part 2: Frontend Components

Create in `frontend/src/app/(dashboard)/emails/` directory

### Page 1: Email Links Tab

**File:** `frontend/src/app/(dashboard)/emails/page.tsx`

```typescript
"use client"

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Check, Edit, X, Link as LinkIcon, Mail } from 'lucide-react'
import { EmailLinkDialog } from '@/components/emails/email-link-dialog'
import { EmailDetailsPanel } from '@/components/emails/email-details-panel'
import { toast } from 'sonner'

export default function EmailLinksPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null)
  const [linkDialogOpen, setLinkDialogOpen] = useState(false)
  const [emailToLink, setEmailToLink] = useState<number | null>(null)

  const queryClient = useQueryClient()

  // Fetch validation queue
  const { data, isLoading } = useQuery({
    queryKey: ['email-validation-queue', statusFilter],
    queryFn: () => api.get(`/api/emails/validation-queue?status=${statusFilter}&limit=100`)
  })

  // Confirm link mutation
  const confirmLink = useMutation({
    mutationFn: (emailId: number) => api.post(`/api/emails/${emailId}/confirm-link`),
    onSuccess: () => {
      toast.success('Link confirmed! AI learns from your feedback.')
      queryClient.invalidateQueries({ queryKey: ['email-validation-queue'] })
    }
  })

  // Unlink mutation
  const unlinkEmail = useMutation({
    mutationFn: ({ emailId, reason }: { emailId: number, reason: string }) =>
      api.delete(`/api/emails/${emailId}/link`, { reason }),
    onSuccess: () => {
      toast.success('Email unlinked. AI learns from your correction.')
      queryClient.invalidateQueries({ queryKey: ['email-validation-queue'] })
    }
  })

  const emails = data?.emails || []
  const counts = data?.counts || {}

  // Filter by search
  const filteredEmails = emails.filter((email: any) =>
    email.subject?.toLowerCase().includes(search.toLowerCase()) ||
    email.sender_email?.toLowerCase().includes(search.toLowerCase())
  )

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.85) return { color: 'green', label: '🟢', text: 'High' }
    if (confidence >= 0.70) return { color: 'yellow', label: '🟡', text: 'Med' }
    return { color: 'red', label: '🔴', text: 'Low' }
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Email Links</h1>
        <p className="text-muted-foreground">
          Review AI-linked emails and correct mistakes to train the system
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
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
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Unlinked</div>
          <div className="text-2xl font-bold">{counts.unlinked}</div>
        </div>
        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Low Confidence</div>
          <div className="text-2xl font-bold">{counts.low_confidence}</div>
        </div>
        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Total</div>
          <div className="text-2xl font-bold">{counts.total}</div>
        </div>
      </div>

      {/* Email List */}
      {isLoading ? (
        <div>Loading emails...</div>
      ) : (
        <div className="space-y-2">
          {filteredEmails.map((email: any) => (
            <div
              key={email.email_id}
              className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <h3
                      className="font-medium truncate cursor-pointer hover:text-primary"
                      onClick={() => setSelectedEmail(email.email_id)}
                    >
                      {email.subject || 'No subject'}
                    </h3>
                    {email.has_attachments && (
                      <Badge variant="outline" className="text-xs">
                        📎 {email.attachment_count}
                      </Badge>
                    )}
                  </div>

                  <div className="text-sm text-muted-foreground">
                    From: {email.sender_email} • {new Date(email.date).toLocaleDateString()}
                  </div>

                  {email.project_code && (
                    <div className="mt-2 flex items-center gap-2">
                      <Badge variant="secondary">
                        {email.project_code} - {email.project_name}
                      </Badge>
                      {email.confidence && (
                        <Badge variant="outline">
                          {getConfidenceBadge(email.confidence).label} {Math.round(email.confidence * 100)}%
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        ({email.link_method})
                      </span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-1 ml-4">
                  {email.project_code ? (
                    <>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => confirmLink.mutate(email.email_id)}
                        title="Confirm correct"
                      >
                        <Check className="h-4 w-4 text-green-600" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setEmailToLink(email.email_id)
                          setLinkDialogOpen(true)
                        }}
                        title="Change link"
                      >
                        <Edit className="h-4 w-4 text-blue-600" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          const reason = prompt('Why is this link wrong?')
                          if (reason) {
                            unlinkEmail.mutate({ emailId: email.email_id, reason })
                          }
                        }}
                        title="Unlink"
                      >
                        <X className="h-4 w-4 text-red-600" />
                      </Button>
                    </>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEmailToLink(email.email_id)
                        setLinkDialogOpen(true)
                      }}
                    >
                      <LinkIcon className="h-4 w-4 mr-1" />
                      Link
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Email Link Dialog */}
      <EmailLinkDialog
        open={linkDialogOpen}
        onOpenChange={setLinkDialogOpen}
        emailId={emailToLink}
      />

      {/* Email Details Panel */}
      {selectedEmail && (
        <EmailDetailsPanel
          emailId={selectedEmail}
          onClose={() => setSelectedEmail(null)}
        />
      )}
    </div>
  )
}
```

### Component: Email Link Dialog

**File:** `frontend/src/components/emails/email-link-dialog.tsx`

```typescript
"use client"

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from 'sonner'

interface EmailLinkDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  emailId: number | null
}

export function EmailLinkDialog({ open, onOpenChange, emailId }: EmailLinkDialogProps) {
  const [selectedProject, setSelectedProject] = useState('')
  const [reason, setReason] = useState('')

  const queryClient = useQueryClient()

  // Get all projects
  const { data: projects } = useQuery({
    queryKey: ['projects-list'],
    queryFn: () => api.get('/api/projects?status=active&limit=500'),
    enabled: open
  })

  // Update link mutation
  const updateLink = useMutation({
    mutationFn: ({ emailId, projectCode, reason }: any) =>
      api.patch(`/api/emails/${emailId}/link`, {
        project_code: projectCode,
        reason,
        updated_by: 'bill'
      }),
    onSuccess: () => {
      toast.success('Email linked! AI learns from this correction.')
      queryClient.invalidateQueries({ queryKey: ['email-validation-queue'] })
      onOpenChange(false)
      setSelectedProject('')
      setReason('')
    }
  })

  const handleSubmit = () => {
    if (!selectedProject || !reason) {
      toast.error('Please select a project and provide a reason')
      return
    }

    updateLink.mutate({
      emailId,
      projectCode: selectedProject,
      reason
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Link Email to Project</DialogTitle>
          <DialogDescription>
            Select the correct project for this email. Your correction trains the AI!
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label htmlFor="project">Project</Label>
            <Select value={selectedProject} onValueChange={setSelectedProject}>
              <SelectTrigger id="project">
                <SelectValue placeholder="Select project..." />
              </SelectTrigger>
              <SelectContent>
                {projects?.map((project: any) => (
                  <SelectItem key={project.code} value={project.code}>
                    {project.code} - {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="reason">
              Why this project? <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="reason"
              placeholder="E.g., Email discusses branding work, not resort design"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
            />
            <p className="text-xs text-muted-foreground mt-1">
              This explanation helps train the AI
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedProject || !reason || updateLink.isPending}
          >
            {updateLink.isPending ? 'Linking...' : 'Link Email'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

### Component: Email Details Panel

**File:** `frontend/src/components/emails/email-details-panel.tsx`

```typescript
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
import { Check, Clock, FileText } from 'lucide-react'

interface EmailDetailsPanelProps {
  emailId: number
  onClose: () => void
}

export function EmailDetailsPanel({ emailId, onClose }: EmailDetailsPanelProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['email-details', emailId],
    queryFn: () => api.get(`/api/emails/${emailId}`)
  })

  const email = data?.email

  if (isLoading) {
    return (
      <Sheet open={true} onOpenChange={onClose}>
        <SheetContent className="overflow-y-auto">
          <div>Loading email details...</div>
        </SheetContent>
      </Sheet>
    )
  }

  return (
    <Sheet open={true} onOpenChange={onClose}>
      <SheetContent className="overflow-y-auto w-[600px]">
        <SheetHeader>
          <SheetTitle>{email.subject || 'No subject'}</SheetTitle>
          <SheetDescription>
            From: {email.sender_email} • {new Date(email.date).toLocaleString()}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Current Link */}
          {email.project_code && (
            <div>
              <h3 className="font-semibold mb-2">Current Link</h3>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="font-medium">
                  {email.project_code} - {email.project_name}
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  Confidence: {Math.round(email.confidence * 100)}% ({email.link_method})
                </div>
                {email.evidence && (
                  <div className="text-xs text-muted-foreground mt-1">
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
              <h3 className="font-semibold mb-2">AI Insights</h3>
              <div className="space-y-2">
                {email.ai_insights.category && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Category:</span>
                    <Badge variant="secondary">{email.ai_insights.category}</Badge>
                  </div>
                )}

                {email.ai_insights.sentiment && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Sentiment:</span>
                    <Badge variant="outline">{email.ai_insights.sentiment}</Badge>
                  </div>
                )}

                {email.ai_insights.ai_summary && (
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">Summary:</div>
                    <p className="text-sm">{email.ai_insights.ai_summary}</p>
                  </div>
                )}

                {email.ai_insights.key_points && (
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">Key Points:</div>
                    <ul className="list-disc list-inside text-sm space-y-1">
                      {JSON.parse(email.ai_insights.key_points).map((point: string, i: number) => (
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
              <h3 className="font-semibold mb-2">Attachments ({email.attachments.length})</h3>
              <div className="space-y-2">
                {email.attachments.map((att: any) => (
                  <div key={att.attachment_id} className="flex items-start gap-2 p-2 bg-gray-50 rounded">
                    <FileText className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{att.filename}</div>
                      <div className="text-xs text-muted-foreground">
                        {(att.filesize / 1024).toFixed(1)} KB
                        {att.document_type && ` • ${att.document_type}`}
                      </div>
                      {att.is_signed && (
                        <Badge variant="default" className="text-xs mt-1">
                          <Check className="h-3 w-3 mr-1" />
                          Signed
                        </Badge>
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
              <div className="text-sm space-y-1">
                <div>Messages: {email.thread.message_count}</div>
                <div>Status: <Badge variant="outline">{email.thread.status}</Badge></div>
              </div>
            </div>
          )}

          <Separator />

          {/* Full Email Body */}
          <div>
            <h3 className="font-semibold mb-2">Email Body</h3>
            <div className="p-3 bg-gray-50 rounded-lg text-sm whitespace-pre-wrap max-h-[400px] overflow-y-auto">
              {email.body_full || email.snippet || 'No content available'}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
```

### Page 2: Project Email Timeline

**File:** `frontend/src/app/(dashboard)/projects/[projectCode]/emails/page.tsx`

```typescript
"use client"

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Mail, Paperclip, TrendingUp } from 'lucide-react'
import { format, parseISO } from 'date-fns'

export default function ProjectEmailsPage() {
  const params = useParams()
  const projectCode = params.projectCode as string

  const { data, isLoading } = useQuery({
    queryKey: ['project-emails', projectCode],
    queryFn: () => api.get(`/api/projects/${projectCode}/emails?include_attachments=true`)
  })

  if (isLoading) {
    return <div className="container mx-auto p-6">Loading email history...</div>
  }

  const project = data?.project
  const emails = data?.emails || []
  const stats = data?.stats || {}

  // Group emails by month
  const emailsByMonth: Record<string, any[]> = {}
  emails.forEach((email: any) => {
    const month = format(parseISO(email.date), 'MMMM yyyy')
    if (!emailsByMonth[month]) {
      emailsByMonth[month] = []
    }
    emailsByMonth[month].push(email)
  })

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">
          {project.code} - {project.name}
        </h1>
        <p className="text-muted-foreground">Complete Email & Attachment History</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Emails
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_emails}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Attachments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_attachments}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Contracts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.contract_count}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Design Docs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.design_doc_count}</div>
          </CardContent>
        </Card>
      </div>

      {/* Timeline */}
      <div className="space-y-8">
        {Object.entries(emailsByMonth).map(([month, monthEmails]) => (
          <div key={month}>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <span>📅 {month}</span>
              <Badge variant="outline">{monthEmails.length} emails</Badge>
            </h2>

            <div className="space-y-3 ml-4 border-l-2 border-gray-200 pl-4">
              {monthEmails.map((email: any) => (
                <div key={email.email_id} className="relative">
                  <div className="absolute -left-[25px] top-2 w-4 h-4 rounded-full bg-primary" />

                  <div className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <h3 className="font-medium">{email.subject}</h3>
                          {email.thread_position && (
                            <Badge variant="outline" className="text-xs">
                              Thread: {email.thread_position}/{email.total_in_thread}
                            </Badge>
                          )}
                        </div>

                        <div className="text-sm text-muted-foreground">
                          From: {email.sender_email} • {format(parseISO(email.date), 'MMM d, h:mm a')}
                        </div>
                      </div>

                      {email.category && (
                        <Badge variant="secondary">{email.category}</Badge>
                      )}
                    </div>

                    {/* AI Summary */}
                    {email.ai_summary && (
                      <div className="mt-2 p-2 bg-blue-50 rounded text-sm flex items-start gap-2">
                        <TrendingUp className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                        <span>{email.ai_summary}</span>
                      </div>
                    )}

                    {/* Attachments */}
                    {email.attachments && email.attachments.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {email.attachments.map((att: any) => (
                          <Badge key={att.attachment_id} variant="outline" className="text-xs">
                            <Paperclip className="h-3 w-3 mr-1" />
                            {att.filename}
                            {att.is_signed && ' ✓ SIGNED'}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Key Points */}
                    {email.key_points && (
                      <div className="mt-2 text-sm">
                        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                          {JSON.parse(email.key_points).slice(0, 3).map((point: string, i: number) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

---

## Testing Instructions

### Test Backend Endpoints

```bash
# 1. Get validation queue
curl http://localhost:8000/api/emails/validation-queue?status=all | jq

# 2. Get email details
curl http://localhost:8000/api/emails/123 | jq

# 3. Update email link
curl -X PATCH http://localhost:8000/api/emails/123/link \
  -H "Content-Type: application/json" \
  -d '{
    "project_code": "25-BK-018",
    "reason": "Email discusses Mumbai pool design",
    "updated_by": "bill"
  }'

# 4. Confirm link
curl -X POST http://localhost:8000/api/emails/123/confirm-link | jq

# 5. Get project timeline
curl http://localhost:8000/api/projects/25-BK-018/emails | jq
```

### Test Frontend

```bash
# 1. Start backend
cd backend
uvicorn api.main:app --reload --port 8000

# 2. Frontend should already be running
# Open: http://localhost:3002/emails

# 3. Test flows:
# - View validation queue
# - Click on an email → See details panel
# - Confirm a link → Check training_data logged
# - Change a link → Check updated + training_data logged
# - Unlink an email → Check removed + training_data logged

# 4. Go to project page
# Open: http://localhost:3002/projects/25-BK-018/emails
# - Verify timeline shows all emails
# - Verify attachments displayed
# - Verify AI summaries shown
```

---

## Report Back With

✅ Screenshots:
1. Email Links page with validation queue
2. Email details panel expanded
3. Email link dialog
4. Project email timeline

✅ Backend verification:
```bash
# Show training_data logged
sqlite3 database/bensley_master.db "
SELECT feature_type, helpful, issue_type, feedback_text,
       expected_value, current_value
FROM training_data
WHERE feature_type = 'email_project_linking'
ORDER BY created_at DESC
LIMIT 5
"
```

✅ Confirm:
- Link corrections update email_project_links
- All corrections logged to training_data (RLHF!)
- Email details panel shows AI insights
- Project timeline shows complete history
- Attachments displayed with document types

---

## Timeline

- **Backend endpoints:** 2 hours
- **Email Links page:** 1.5 hours
- **Email Details panel:** 1 hour
- **Project Timeline page:** 1.5 hours
- **Testing:** 30 minutes

**Total:** 6.5 hours

---

## Priority

🟡 **HIGH** - This is the foundation for Phase 2 RAG system

**Why important:**
- Builds complete project context
- Trains AI with your corrections (RLHF!)
- Enables intelligent queries in Phase 2
- Gives Bill visibility into email linking

---

**Ready to build? Let me know when you start and report back with progress!**
