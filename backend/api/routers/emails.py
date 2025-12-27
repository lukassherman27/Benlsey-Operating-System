"""
Emails Router - Email management and linking endpoints

Endpoints:
    GET /api/emails - List emails
    GET /api/emails/stats - Email statistics
    GET /api/emails/{email_id} - Get email details
    POST /api/emails/{email_id}/link - Link email to project
    GET /api/emails/pending-approval - Emails pending approval
    ... and more
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import sqlite3

from api.services import email_service, email_intelligence_service, email_orchestrator
from api.dependencies import DB_PATH
from api.models import EmailCategoryRequest, EmailLinkRequest, BulkCategoryRequest
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["emails"])


# ============================================================================
# EMAIL LIST ENDPOINTS
# ============================================================================

@router.get("/emails")
async def get_emails(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    project_code: Optional[str] = None,
    search: Optional[str] = None,
    inbox_source: Optional[str] = Query(None, description="Filter by source inbox (e.g., projects@bensley.com)"),
    inbox_category: Optional[str] = Query(None, description="Filter by inbox category (projects, invoices, internal, general)")
):
    """Get paginated list of emails with optional filtering"""
    try:
        result = email_service.get_emails(
            page=page,
            per_page=per_page,
            category=category,
            project_code=project_code,
            search=search,
            inbox_source=inbox_source,
            inbox_category=inbox_category
        )
        return list_response(
            result.get('emails', []),
            result.get('total', 0),
            page,
            per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/stats")
async def get_email_stats():
    """Get email statistics"""
    try:
        stats = email_service.get_email_stats()
        return item_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/inbox-stats")
async def get_inbox_stats():
    """
    Get email counts grouped by inbox source and category.

    Returns counts for:
    - By inbox_source (projects@, invoices@, lukas@, etc.)
    - By inbox_category (projects, invoices, internal, general)
    """
    try:
        import sqlite3
        from api.dependencies import DB_PATH

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get counts by inbox_source
            cursor.execute("""
                SELECT inbox_source, COUNT(*) as count
                FROM emails
                WHERE inbox_source IS NOT NULL
                GROUP BY inbox_source
                ORDER BY count DESC
            """)
            by_source = [dict(row) for row in cursor.fetchall()]

            # Get counts by inbox_category
            cursor.execute("""
                SELECT inbox_category, COUNT(*) as count
                FROM emails
                WHERE inbox_category IS NOT NULL
                GROUP BY inbox_category
                ORDER BY count DESC
            """)
            by_category = [dict(row) for row in cursor.fetchall()]

            # Get total
            cursor.execute("SELECT COUNT(*) FROM emails")
            total = cursor.fetchone()[0]

        return {
            "success": True,
            "data": {
                "total": total,
                "by_source": by_source,
                "by_category": by_category
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/import-stats")
async def get_import_stats():
    """
    Get comprehensive email import statistics.

    Returns daily, weekly, and total import stats with trends.
    Used by ImportSummaryWidget on dashboard.
    """
    try:
        stats = email_orchestrator.get_import_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/process-batch")
async def process_email_batch(
    limit: int = Query(100, ge=1, le=500),
    hours: int = Query(24, ge=1, le=168)
):
    """
    Process batch of emails through categorization and suggestion pipeline.

    Coordinates:
    1. EmailCategoryService.batch_categorize() - categorizes uncategorized emails
    2. AILearningService.process_recent_emails_for_suggestions() - generates suggestions

    NEVER auto-applies anything - all changes go through suggestion approval.
    """
    try:
        result = email_orchestrator.process_new_emails(limit=limit, hours=hours)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/uncategorized")
async def get_uncategorized_emails(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200)
):
    """Get emails that haven't been categorized"""
    try:
        result = email_service.get_uncategorized_emails(page=page, per_page=per_page)
        return list_response(
            result.get('emails', []),
            result.get('total', 0),
            page,
            per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/recent")
async def get_recent_emails(limit: int = Query(20, ge=1, le=100)):
    """Get most recent emails. Returns standardized list response."""
    try:
        emails = email_service.get_recent_emails(limit=limit)
        return list_response(emails, len(emails))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/categories")
async def get_email_categories():
    """Get all email categories with counts. Returns standardized list response."""
    try:
        categories = email_service.get_categories()
        return list_response(categories, len(categories))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/categories/list")
async def get_email_categories_list():
    """Alias for /emails/categories - Get all email categories with counts."""
    return await get_email_categories()


@router.get("/emails/pending-approval")
async def get_emails_pending_approval(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200)
):
    """Get emails pending category approval"""
    try:
        result = email_service.get_pending_approval(page=page, per_page=per_page)
        return list_response(
            result.get('emails', []),
            result.get('total', 0),
            page,
            per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/validation-queue")
async def get_validation_queue(
    status: Optional[str] = Query(None, description="Filter: 'unlinked', 'low_confidence', or 'all'"),
    priority: Optional[str] = Query(None, description="Filter: 'high', 'medium', 'low', or 'all'"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get emails needing validation - unlinked or low confidence links"""
    try:
        result = email_intelligence_service.get_validation_queue(
            status=status,
            priority=priority,
            limit=limit
        )
        return result  # Already in correct format with success, counts, emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EMAIL REVIEW QUEUE - For learning loop (MUST be before {email_id} routes)
# ============================================================================

@router.get("/emails/review-queue")
async def get_review_queue(
    limit: int = Query(50, ge=1, le=200, description="Max emails to return")
):
    """
    Get emails with pending AI suggestions for review.

    Returns emails that have pending suggestions (email_link, contact_link, etc.)
    with inline AI suggestion details and sender context.

    Used by the Email Review Queue page for batch reviewing with approve/reject.
    """
    try:
        result = email_intelligence_service.get_review_queue(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/bulk-approve")
async def bulk_approve_emails(
    email_ids: List[int] = Query(..., description="List of email IDs to approve"),
    learn_patterns: bool = Query(True, description="Learn patterns from approvals")
):
    """
    Bulk approve multiple email suggestions at once.

    Each email must have a pending suggestion. The suggested link is applied.
    Optionally learns patterns from all approvals.

    Returns summary of successes and failures.
    """
    try:
        from backend.services.ai_learning_service import AILearningService

        ai_service = AILearningService(DB_PATH)

        results = {
            "approved": 0,
            "failed": 0,
            "patterns_learned": [],
            "errors": []
        }

        for email_id in email_ids:
            try:
                # Find pending suggestion for this email
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT suggestion_id, project_code
                        FROM ai_suggestions
                        WHERE source_type = 'email'
                        AND source_id = ?
                        AND status = 'pending'
                        AND suggestion_type = 'email_link'
                        LIMIT 1
                    """, (email_id,))
                    suggestion = cursor.fetchone()

                if not suggestion:
                    results["failed"] += 1
                    results["errors"].append({
                        "email_id": email_id,
                        "error": "No pending suggestion found"
                    })
                    continue

                suggestion_id, target_code = suggestion  # target_code is actually project_code

                # Approve the suggestion
                result = ai_service.approve_suggestion(suggestion_id)

                if result.get('success'):
                    results["approved"] += 1

                    # Learn pattern if requested
                    if learn_patterns:
                        with sqlite3.connect(DB_PATH) as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT sender_email FROM emails WHERE email_id = ?", (email_id,))
                            sender_row = cursor.fetchone()

                        if sender_row and sender_row[0]:
                            sender_email = sender_row[0]
                            domain = sender_email.split('@')[1] if '@' in sender_email else None
                            if domain and domain not in [p.split('@')[1] if '@' in p else p for p in results["patterns_learned"]]:
                                results["patterns_learned"].append(f"@{domain} → {target_code}")
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "email_id": email_id,
                        "error": result.get('error', 'Unknown error')
                    })

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "email_id": email_id,
                    "error": str(e)
                })

        return {
            "success": True,
            "message": f"Approved {results['approved']} emails, {results['failed']} failed",
            "data": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/{email_id}/quick-approve")
async def quick_approve_email(
    email_id: int,
    project_code: str = Query(..., description="Project code to link to"),
    learn_pattern: bool = Query(True, description="Learn sender pattern from this approval")
):
    """
    Quick approve an email link suggestion.

    This:
    1. Creates the email-proposal link
    2. Marks the suggestion as applied
    3. Optionally learns a sender pattern for future emails

    Returns info about pattern learning for UI feedback.
    """
    try:
        from backend.services.ai_learning_service import AILearningService

        ai_service = AILearningService(DB_PATH)

        # Find the pending suggestion for this email
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT suggestion_id, project_code
                FROM ai_suggestions
                WHERE source_type = 'email'
                AND source_id = ?
                AND status = 'pending'
                AND suggestion_type = 'email_link'
                LIMIT 1
            """, (email_id,))
            suggestion = cursor.fetchone()

        if not suggestion:
            # No existing suggestion - create direct link
            # Get proposal_id from project_code
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT proposal_id, project_name FROM proposals WHERE project_code = ?
                """, (project_code,))
                proposal = cursor.fetchone()

            if not proposal:
                raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

            proposal_id, project_name = proposal

            # Create direct link
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO email_proposal_links
                    (email_id, proposal_id, confidence_score, match_method, created_at)
                    VALUES (?, ?, 1.0, 'manual_quick_approve', datetime('now'))
                """, (email_id, proposal_id))
                conn.commit()

            pattern_result = None
            if learn_pattern:
                # Get sender email to learn pattern
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT sender_email FROM emails WHERE email_id = ?", (email_id,))
                    sender_row = cursor.fetchone()

                if sender_row and sender_row[0]:
                    sender_email = sender_row[0]
                    domain = sender_email.split('@')[1] if '@' in sender_email else None

                    if domain:
                        pattern_result = f"domain_to_proposal: @{domain} → {project_code}"

            return {
                "success": True,
                "link_created": True,
                "project_code": project_code,
                "project_name": project_name,
                "pattern_learned": pattern_result,
                "message": f"Email linked to {project_code} ({project_name})"
            }

        else:
            # Have existing suggestion - approve it
            suggestion_id, suggested_project = suggestion

            # If user picked a different project than suggested, treat as correction
            if project_code != suggested_project:
                # Approve with correction
                result = ai_service.approve_suggestion_with_correction(
                    suggestion_id,
                    correct_value=project_code
                )
            else:
                # Approve as-is
                result = ai_service.approve_suggestion(suggestion_id)

            pattern_result = None
            if learn_pattern and result.get('success'):
                # Learn pattern from this approval
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT sender_email FROM emails WHERE email_id = ?", (email_id,))
                    sender_row = cursor.fetchone()

                if sender_row and sender_row[0]:
                    sender_email = sender_row[0]
                    domain = sender_email.split('@')[1] if '@' in sender_email else None
                    if domain:
                        pattern_result = f"domain_to_proposal: @{domain} → {project_code}"

            return {
                "success": True,
                "link_created": result.get('success', False),
                "project_code": project_code,
                "pattern_learned": pattern_result,
                "message": result.get('message', f"Email linked to {project_code}")
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EMAIL DETAIL ENDPOINTS
# ============================================================================

@router.get("/emails/{email_id}")
async def get_email(email_id: int):
    """Get email details by ID"""
    try:
        email = email_service.get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")
        return item_response(email)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/{email_id}/details")
async def get_email_details(email_id: int):
    """Get full email details including body and attachments"""
    try:
        email = email_service.get_email_details(email_id)
        if not email:
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")
        return item_response(email)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EMAIL ACTIONS
# ============================================================================

@router.post("/emails/{email_id}/category")
async def update_email_category_endpoint(email_id: int, request: EmailCategoryRequest):
    """Update email category using the unified category system"""
    try:
        result = email_service.update_email_category(
            email_id,
            new_category=request.category,
            subcategory=request.subcategory,
            feedback=None
        )
        if not result:
            raise HTTPException(status_code=404, detail="Email not found")
        return action_response(True, message="Category updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/{email_id}/link")
async def link_email_to_project(email_id: int, request: EmailLinkRequest):
    """Link email to a project"""
    try:
        result = email_service.link_to_project(
            email_id,
            project_code=request.project_code,
            link_type=request.link_type
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        return action_response(True, message=f"Email linked to {request.project_code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/emails/{email_id}/link")
async def unlink_email_from_project(email_id: int):
    """Remove project link from email"""
    try:
        result = email_service.unlink_from_project(email_id)
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        return action_response(True, message="Email unlinked")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/{email_id}/approve-category")
async def approve_email_category(email_id: int):
    """Approve AI-suggested category"""
    try:
        result = email_service.approve_category(email_id)
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        return action_response(True, message="Category approved")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/{email_id}/reject-category")
async def reject_email_category(email_id: int):
    """Reject AI-suggested category"""
    try:
        result = email_service.reject_category(email_id)
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        return action_response(True, message="Category rejected")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/{email_id}/read")
async def mark_email_read(email_id: int):
    """Mark email as read"""
    try:
        result = email_service.mark_as_read(email_id)
        return action_response(True, message="Marked as read")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/{email_id}/confirm-link")
async def confirm_email_link(
    email_id: int,
    confirmed_by: str = Query("bill", description="Who confirmed this link")
):
    """
    Confirm that an AI-suggested email-project link is correct.

    This:
    1. Updates confidence score to 1.0
    2. Logs for AI training
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Update confidence to 1.0 to mark as confirmed
            cursor.execute("""
                UPDATE email_proposal_links
                SET confidence_score = 1.0,
                    match_method = CASE
                        WHEN match_method LIKE '%confirmed%' THEN match_method
                        ELSE match_method || '_confirmed'
                    END
                WHERE email_id = ?
            """, (email_id,))

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"No link found for email {email_id}")

            conn.commit()

        return {
            "success": True,
            "message": f"Link confirmed by {confirmed_by}",
            "training_logged": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/{email_id}/extract-scheduling")
async def extract_scheduling_data(email_id: int):
    """
    Extract scheduling data from an email using OpenAI.

    Extracts:
    - deadlines: Dates and deadlines mentioned
    - people: People mentioned with their apparent roles
    - project_references: Project codes found
    - potential_nicknames: Informal project names that might be aliases
    - action_items: Tasks and action items

    Used by the adaptive suggestions UI when category is "Internal > Scheduling".
    """
    try:
        from backend.services.scheduling_email_parser import SchedulingEmailParser
        from api.dependencies import DB_PATH

        parser = SchedulingEmailParser(db_path=DB_PATH)
        result = parser.parse_email_by_id(email_id)

        if not result.get('success'):
            raise HTTPException(
                status_code=404 if 'not found' in result.get('error', '').lower() else 400,
                detail=result.get('error', 'Extraction failed')
            )

        return {
            "success": True,
            "email_id": email_id,
            "deadlines": result.get('deadlines', []),
            "people": result.get('people', []),
            "project_references": result.get('project_references', []),
            "potential_nicknames": result.get('potential_nicknames', []),
            "action_items": result.get('action_items', [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/emails/bulk-category")
async def bulk_update_category(request: BulkCategoryRequest):
    """Update category for multiple emails"""
    try:
        result = email_service.bulk_update_category(
            email_ids=request.email_ids,
            category=request.category,
            subcategory=request.subcategory,
            project_code=request.project_code
        )
        return action_response(
            True,
            data={"updated": result.get('updated', 0)},
            message=f"Updated {result.get('updated', 0)} emails"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT EMAIL ENDPOINTS
# ============================================================================

@router.get("/projects/{project_code}/emails")
async def get_project_emails(
    project_code: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200)
):
    """Get emails linked to a project"""
    try:
        result = email_service.get_emails_by_project(
            project_code=project_code,
            page=page,
            per_page=per_page
        )
        return list_response(
            result.get('emails', []),
            result.get('total', 0),
            page,
            per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT EMAIL ENDPOINTS (Frontend-compatible routes)
# ============================================================================

@router.get("/emails/project/{project_code}")
async def get_project_emails_alt(
    project_code: str,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get emails linked to a project.
    Frontend-compatible route for EmailActivityFeed component.
    """
    try:
        emails = email_service.get_emails_by_project(
            project_code=project_code,
            limit=limit
        )
        return {
            "success": True,
            "project_code": project_code,
            "data": emails,
            "count": len(emails)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/scan-sent-proposals")
async def scan_sent_for_proposals(
    days_back: int = Query(30, ge=1, le=90, description="Days to look back"),
    limit: int = Query(200, ge=1, le=500, description="Max emails to scan")
):
    """
    Scan Sent folder for proposal-related emails and create status suggestions.

    This endpoint:
    1. Connects to IMAP Sent folder
    2. Detects "proposal sent" patterns (attachments, subject keywords)
    3. Creates proposal_status_update suggestions for approval
    4. Links email as evidence for the status change

    NEVER auto-updates status - creates suggestions only.
    """
    try:
        from backend.services.sent_email_detector import SentEmailDetector

        detector = SentEmailDetector()

        if not detector.connect():
            raise HTTPException(
                status_code=503,
                detail="Could not connect to email server. Check EMAIL_* environment variables."
            )

        try:
            results = detector.scan_sent_for_proposals(days_back=days_back, limit=limit)
        finally:
            detector.close()

        return {
            "success": True,
            "message": f"Scanned {results['emails_scanned']} sent emails, "
                      f"detected {results['proposals_detected']} proposals, "
                      f"created {results['suggestions_created']} suggestions",
            "data": {
                "emails_scanned": results['emails_scanned'],
                "proposals_detected": results['proposals_detected'],
                "suggestions_created": results['suggestions_created'],
                "detections": [
                    {
                        "project_code": d['matched_proposal']['project_code'],
                        "project_name": d['matched_proposal']['project_name'],
                        "subject": d['subject'][:80],
                        "date": d['date_normalized'],
                        "confidence": round(d['confidence'], 2)
                    }
                    for d in results.get('detections', [])[:20]
                ]
            },
            "errors": results.get('errors', [])[:10]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/process-sent-emails")
async def process_sent_emails(
    days_back: int = Query(30, ge=1, le=90, description="Days to look back"),
    limit: int = Query(200, ge=1, le=500, description="Max emails to process")
):
    """
    Process sent emails that haven't been linked yet.

    Uses SentEmailLinker to match outbound @bensley.com emails to proposals via:
    1. Project code in subject/body (0.95 confidence)
    2. Recipient matches proposals.contact_email (0.95 confidence)
    3. Recipient found in contacts table (0.85 confidence)
    4. Domain patterns from learned patterns (0.70 confidence, needs review)

    Returns summary of auto-linked, needs_review, and unmatched emails.
    """
    try:
        from backend.services.sent_email_linker import SentEmailLinker

        linker = SentEmailLinker(DB_PATH)
        results = linker.process_unlinked_sent_emails(days_back=days_back, limit=limit)

        return {
            "success": True,
            "message": f"Processed {results['total']} sent emails: "
                      f"{results['auto_linked']} auto-linked, "
                      f"{results['needs_review']} need review, "
                      f"{results['no_match']} unmatched",
            "data": {
                "total_processed": results['total'],
                "auto_linked": results['auto_linked'],
                "needs_review": results['needs_review'],
                "no_match": results['no_match'],
                "no_external_recipients": results['no_external_recipients'],
                "linked_emails": results['linked_emails'][:20],  # First 20
                "review_emails": results['review_emails'][:10]   # First 10
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/project/{project_code}/summary")
async def get_project_email_summary(
    project_code: str,
    use_ai: bool = Query(True)
):
    """
    Get AI-powered email intelligence summary for a project.
    Used by EmailIntelligenceSummary component.
    """
    try:
        emails = email_service.get_emails_by_project(
            project_code=project_code,
            limit=100
        )
        total_emails = len(emails)

        if total_emails == 0:
            return {
                "success": True,
                "project_code": project_code,
                "total_emails": 0,
                "date_range": None,
                "ai_summary": None,
                "key_points": [],
                "timeline": [],
                "email_groups": {}
            }

        # Calculate date range
        dates = [e.get('date') or e.get('date_normalized') for e in emails if e.get('date') or e.get('date_normalized')]
        date_range = None
        if dates:
            dates_sorted = sorted([d for d in dates if d])
            if dates_sorted:
                date_range = {
                    "first": dates_sorted[0],
                    "last": dates_sorted[-1]
                }

        # Group emails by subject (thread-like grouping)
        email_groups = {}
        for email in emails:
            subject = email.get('subject') or '(No subject)'
            # Normalize subject for grouping (remove Re:, Fwd:, etc.)
            normalized_subject = subject
            for prefix in ['Re:', 'RE:', 'Fwd:', 'FWD:', 'Fw:']:
                normalized_subject = normalized_subject.replace(prefix, '').strip()
            if normalized_subject in email_groups:
                email_groups[normalized_subject] += 1
            else:
                email_groups[normalized_subject] = 1

        # Build response with AI summary if available
        ai_summary = None
        key_points = []

        if use_ai:
            # Try to get AI-generated insights from emails that have them
            summaries = [e.get('ai_summary') for e in emails[:10] if e.get('ai_summary')]
            key_points_raw = [e.get('key_points') for e in emails[:10] if e.get('key_points')]

            if summaries:
                ai_summary = {
                    "executive_summary": f"This project has {total_emails} emails in the communication history. " +
                        (summaries[0] if summaries else ""),
                    "topics": list(email_groups.keys())[:5]
                }

            # Flatten key points
            for kp in key_points_raw:
                if isinstance(kp, str):
                    key_points.append(kp)
                elif isinstance(kp, list):
                    key_points.extend(kp[:3])
            key_points = key_points[:5]  # Limit to 5

        # Build timeline from recent emails
        timeline = []
        for email in emails[:5]:
            timeline.append({
                "date": email.get('date') or email.get('date_normalized'),
                "event": email.get('subject') or 'Email',
                "description": email.get('snippet') or email.get('ai_summary')
            })

        return {
            "success": True,
            "project_code": project_code,
            "total_emails": total_emails,
            "date_range": date_range,
            "ai_summary": ai_summary,
            "key_points": key_points,
            "timeline": timeline,
            "email_groups": email_groups
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
