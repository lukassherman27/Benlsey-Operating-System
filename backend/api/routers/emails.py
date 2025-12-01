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
    search: Optional[str] = None
):
    """Get paginated list of emails with optional filtering"""
    try:
        result = email_service.get_emails(
            page=page,
            per_page=per_page,
            category=category,
            project_code=project_code,
            search=search
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
        response = list_response(emails, len(emails))
        response["emails"] = emails  # Backward compat
        response["count"] = len(emails)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/categories")
async def get_email_categories():
    """Get all email categories with counts. Returns standardized list response."""
    try:
        categories = email_service.get_categories()
        response = list_response(categories, len(categories))
        response["categories"] = categories  # Backward compat
        return response
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
async def update_email_category(email_id: int, request: EmailCategoryRequest):
    """Update email category"""
    try:
        result = email_service.update_category(
            email_id,
            category=request.category,
            subcategory=request.subcategory,
            project_code=request.project_code
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))
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
        result = email_service.get_emails_by_project(
            project_code=project_code,
            page=1,
            per_page=limit
        )
        return {
            "success": True,
            "project_code": project_code,
            "data": result.get('emails', []),
            "count": result.get('total', 0)
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
        result = email_service.get_emails_by_project(
            project_code=project_code,
            page=1,
            per_page=100
        )

        emails = result.get('emails', [])
        total_emails = result.get('total', 0)

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
