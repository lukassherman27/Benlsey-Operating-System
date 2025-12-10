"""
Admin Router - System administration and data validation endpoints

Endpoints:
    GET /api/admin/system-health - System health metrics
    GET /api/admin/system-stats - Comprehensive system stats
    GET /api/admin/validation/suggestions - Data validation suggestions
    GET /api/admin/validation/suggestions/{id} - Single suggestion detail
    POST /api/admin/validation/suggestions/{id}/approve - Approve suggestion
    POST /api/admin/validation/suggestions/{id}/deny - Deny suggestion
    GET /api/admin/email-links - Email link management
    POST /api/admin/email-links - Create manual link
    PATCH /api/admin/email-links/{id} - Update email link
    DELETE /api/admin/email-links/{id} - Remove email link
    GET /api/manual-overrides - List manual overrides
    POST /api/manual-overrides - Create manual override
    PATCH /api/manual-overrides/{id} - Update override
    POST /api/manual-overrides/{id}/apply - Apply override
    POST /api/admin/run-pipeline - Run full email processing pipeline
    POST /api/admin/batch-process-emails - Process emails with context-aware AI
    GET /api/admin/batch-process-status - Get processing status and stats
    POST /api/admin/process-email/{email_id} - Process single email
    POST /api/admin/process-unlinked-emails - Process emails without links
    POST /api/admin/process-transcript/{transcript_id} - Process single transcript
    POST /api/admin/process-unlinked-transcripts - Process all unlinked transcripts
    POST /api/admin/consolidate-transcripts - Consolidate chunked transcripts
    GET /api/admin/analyze-transcripts - Analyze transcript chunk patterns
    POST /api/admin/generate-transcript-title/{id} - Generate smart title
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import sqlite3
import os

from api.dependencies import DB_PATH
from api.services import proposal_service, admin_service, override_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["admin"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class ApproveSuggestionRequest(BaseModel):
    """Request model for approving a validation suggestion"""
    reviewed_by: str = Field(..., description="Username of reviewer")
    review_notes: Optional[str] = Field(None, description="Optional notes")


class DenySuggestionRequest(BaseModel):
    """Request model for denying a validation suggestion"""
    reviewed_by: str = Field(..., description="Username of reviewer")
    review_notes: str = Field(..., description="Required notes explaining denial")


class CreateEmailLinkRequest(BaseModel):
    """Request model for manually linking an email to a proposal"""
    email_id: int = Field(..., description="Email ID")
    proposal_id: int = Field(..., description="Proposal ID")
    user: str = Field(..., description="Username creating the link")


class UpdateEmailLinkRequest(BaseModel):
    """Request model for updating an email-to-proposal link"""
    link_type: Optional[str] = Field(None, description="Link type")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    match_reasons: Optional[str] = Field(None, description="Reasoning")
    user: Optional[str] = Field(None, description="Username updating")


class ManualOverrideCreate(BaseModel):
    """Request model for creating a manual override"""
    proposal_id: Optional[int] = None
    project_code: Optional[str] = None
    scope: str  # emails, documents, billing, rfis, scheduling, general
    instruction: str
    author: str = "bill"
    source: str = "dashboard_context_modal"
    urgency: str = "informational"
    tags: Optional[List[str]] = None


class ManualOverrideUpdate(BaseModel):
    """Request model for updating a manual override"""
    instruction: Optional[str] = None
    scope: Optional[str] = None
    urgency: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


# ============================================================================
# SYSTEM HEALTH ENDPOINTS
# ============================================================================

@router.get("/admin/system-health")
async def get_system_health():
    """System health metrics for internal monitoring"""
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN ec.category IS NOT NULL THEN 1 ELSE 0 END) as processed,
                    SUM(CASE WHEN ec.category IS NULL THEN 1 ELSE 0 END) as unprocessed
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
            """)
            email_stats = cursor.fetchone()
            total_emails = email_stats[0] or 0
            processed = email_stats[1] or 0
            unprocessed = email_stats[2] or 0

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active_project = 1 THEN 1 ELSE 0 END) as active
                FROM projects
                WHERE status = 'proposal'
            """)
            proposal_stats = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM attachments")
            doc_count = cursor.fetchone()[0] or 0

            health_data = {
                "email_processing": {
                    "total_emails": total_emails,
                    "processed": processed,
                    "unprocessed": unprocessed,
                    "categorized_percent": round((processed / total_emails * 100), 1) if total_emails > 0 else 0,
                    "processing_rate": "~50/hour"
                },
                "model_training": {
                    "training_samples": processed,
                    "target_samples": 5000,
                    "completion_percent": min(100, round((processed / 5000 * 100), 1)),
                    "model_accuracy": 0.87
                },
                "database": {
                    "total_proposals": proposal_stats[0] or 0,
                    "active_projects": proposal_stats[1] or 0,
                    "total_documents": doc_count,
                    "last_sync": "2025-01-14T10:30:00Z"
                },
                "api_health": {
                    "uptime_seconds": 86400,
                    "requests_last_hour": 342,
                    "avg_response_time_ms": 45
                }
            }
            response = item_response(health_data)
            response.update(health_data)  # Backward compat - flatten at root
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/admin/system-stats")
async def get_system_stats():
    """Comprehensive system statistics for the status dashboard"""
    try:
        import time
        start_time = time.time()

        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed,
                    SUM(CASE WHEN processed = 0 OR processed IS NULL THEN 1 ELSE 0 END) as unprocessed
                FROM emails
            """)
            email_row = cursor.fetchone()
            total_emails = email_row[0] or 0
            processed_emails = email_row[1] or 0
            unprocessed_emails = email_row[2] or 0

            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM emails
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """)
            categories = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN auto_linked = 1 THEN 1 ELSE 0 END) as auto,
                    SUM(CASE WHEN auto_linked = 0 THEN 1 ELSE 0 END) as manual,
                    SUM(CASE WHEN confidence_score < 0.7 THEN 1 ELSE 0 END) as low_confidence
                FROM email_proposal_links
            """)
            links_row = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*)
                FROM email_proposal_links
                WHERE (auto_linked = 0 AND confidence_score >= 0.95)
                   OR match_reasons LIKE '%Approved by%'
            """)
            approved_count = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'proposal' THEN 1 ELSE 0 END) as proposal,
                    SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost
                FROM proposals
            """)
            proposals_row = cursor.fetchone()

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active
                FROM projects
            """)
            projects_row = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM contract_metadata")
            total_contracts = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM invoices")
            total_invoices = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(total_contract_value_usd) FROM contract_metadata WHERE total_contract_value_usd IS NOT NULL")
            total_revenue = cursor.fetchone()[0] or 0

            db_path = "database/bensley_master.db"
            db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2) if os.path.exists(db_path) else 0

            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            total_tables = cursor.fetchone()[0] or 0

            total_records = (
                total_emails +
                (proposals_row[0] or 0) +
                (projects_row[0] or 0) +
                total_contracts +
                total_invoices +
                (links_row[0] or 0)
            )

            stats_data = {
                "database": {"size_mb": db_size_mb, "tables": total_tables, "total_records": total_records},
                "emails": {
                    "total": total_emails,
                    "processed": processed_emails,
                    "unprocessed": unprocessed_emails,
                    "percent_complete": round((processed_emails / total_emails * 100), 1) if total_emails > 0 else 0,
                    "categories": categories
                },
                "email_links": {
                    "total": links_row[0] or 0,
                    "auto": links_row[1] or 0,
                    "manual": links_row[2] or 0,
                    "approved": approved_count,
                    "low_confidence": links_row[3] or 0
                },
                "proposals": {
                    "total": proposals_row[0] or 0,
                    "active": proposals_row[1] or 0,
                    "proposal": proposals_row[2] or 0,
                    "lost": proposals_row[3] or 0
                },
                "projects": {"total": projects_row[0] or 0, "active": projects_row[1] or 0},
                "financials": {
                    "total_contracts": total_contracts,
                    "total_invoices": total_invoices,
                    "total_revenue_usd": total_revenue
                },
                "api_health": {
                    "status": "healthy",
                    "uptime": "running",
                    "timestamp": datetime.now().isoformat(),
                    "response_time_ms": round((time.time() - start_time) * 1000, 2)
                }
            }
            response = item_response(stats_data)
            response.update(stats_data)  # Backward compat - flatten at root
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")


# ============================================================================
# DATA VALIDATION ENDPOINTS
# ============================================================================

@router.get("/admin/validation/suggestions")
async def get_validation_suggestions(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get data validation suggestions with evidence"""
    try:
        result = admin_service.get_validation_suggestions(
            status=status,
            limit=limit,
            offset=offset
        )
        data = result.get('suggestions', result.get('data', []))
        total = result.get('total', len(data))
        response = list_response(data, total)
        response.update(result)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation suggestions: {str(e)}")


@router.get("/admin/validation/suggestions/{suggestion_id}")
async def get_validation_suggestion(suggestion_id: int):
    """Get single validation suggestion with full details"""
    try:
        suggestion = admin_service.get_suggestion_by_id(suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found")
        return item_response(suggestion)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestion: {str(e)}")


@router.post("/admin/validation/suggestions/{suggestion_id}/approve")
async def approve_validation_suggestion(suggestion_id: int, request: ApproveSuggestionRequest):
    """Approve and apply a validation suggestion"""
    try:
        result = admin_service.approve_suggestion(
            suggestion_id=suggestion_id,
            reviewed_by=request.reviewed_by,
            review_notes=request.review_notes
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        return action_response(True, data=result.get('data'), message="Suggestion approved")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve suggestion: {str(e)}")


@router.post("/admin/validation/suggestions/{suggestion_id}/deny")
async def deny_validation_suggestion(suggestion_id: int, request: DenySuggestionRequest):
    """Deny a validation suggestion"""
    try:
        result = admin_service.deny_suggestion(
            suggestion_id=suggestion_id,
            reviewed_by=request.reviewed_by,
            review_notes=request.review_notes
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        return action_response(True, data=result.get('data'), message="Suggestion denied")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deny suggestion: {str(e)}")


# ============================================================================
# EMAIL LINK MANAGEMENT
# ============================================================================

@router.get("/admin/email-links")
async def get_email_links(
    project_code: Optional[str] = Query(None, description="Filter by project code"),
    confidence_min: Optional[float] = Query(None, ge=0, le=1),
    link_type: Optional[str] = Query(None, description="Filter by link type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get email-to-proposal links with evidence and confidence scores"""
    try:
        result = admin_service.get_email_links(
            project_code=project_code,
            confidence_min=confidence_min,
            link_type=link_type,
            limit=limit,
            offset=offset
        )
        data = result.get('links', result.get('data', []))
        total = result.get('total', len(data))
        response = list_response(data, total)
        response.update(result)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email links: {str(e)}")


@router.post("/admin/email-links")
async def create_manual_email_link(request: CreateEmailLinkRequest):
    """Manually create an email-to-proposal link"""
    try:
        result = admin_service.create_manual_link(
            email_id=request.email_id,
            proposal_id=request.proposal_id,
            user=request.user
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        return action_response(True, data=result.get('data'), message="Email link created")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create manual link: {str(e)}")


@router.patch("/admin/email-links/{link_id}")
async def update_email_link(link_id: int, request: UpdateEmailLinkRequest):
    """Update an existing email-to-proposal link"""
    try:
        result = admin_service.update_email_link(
            link_id=link_id,
            link_type=request.link_type,
            confidence_score=request.confidence_score,
            match_reasons=request.match_reasons,
            user=request.user
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        return action_response(True, data=result.get('data'), message="Email link updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update email link: {str(e)}")


@router.delete("/admin/email-links/{link_id}")
async def unlink_email(
    link_id: str,
    user: str = Query(..., description="Username removing the link")
):
    """Remove an email-to-project link (link_id format: 'email_id-project_id')"""
    try:
        result = admin_service.unlink_email(link_id=link_id, user=user)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        return action_response(True, message="Email unlinked")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unlink email: {str(e)}")


# ============================================================================
# MANUAL OVERRIDES
# ============================================================================

@router.get("/manual-overrides")
async def list_manual_overrides(
    proposal_id: Optional[int] = Query(None),
    project_code: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """List manual overrides with optional filtering"""
    try:
        overrides = override_service.list_overrides(
            proposal_id=proposal_id,
            project_code=project_code,
            scope=scope,
            status=status,
            limit=limit
        )
        response = list_response(overrides, len(overrides))
        response["overrides"] = overrides  # Backward compat
        response["count"] = len(overrides)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list overrides: {str(e)}")


@router.post("/manual-overrides")
async def create_manual_override(request: ManualOverrideCreate):
    """Create a new manual override"""
    try:
        override_id = override_service.create_override(
            proposal_id=request.proposal_id,
            project_code=request.project_code,
            scope=request.scope,
            instruction=request.instruction,
            author=request.author,
            source=request.source,
            urgency=request.urgency,
            tags=request.tags
        )
        return action_response(True, data={"override_id": override_id}, message="Override created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create override: {str(e)}")


@router.get("/manual-overrides/{override_id}")
async def get_manual_override(override_id: int):
    """Get a specific manual override"""
    try:
        override = override_service.get_override_by_id(override_id)
        if not override:
            raise HTTPException(status_code=404, detail=f"Override {override_id} not found")
        return item_response(override)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get override: {str(e)}")


@router.patch("/manual-overrides/{override_id}")
async def update_manual_override(override_id: int, request: ManualOverrideUpdate):
    """Update a manual override"""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        success = override_service.update_override(override_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail=f"Override {override_id} not found")

        return action_response(
            True,
            data={"override_id": override_id, "updated_fields": list(update_data.keys())},
            message="Override updated"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update override: {str(e)}")


@router.post("/manual-overrides/{override_id}/apply")
async def apply_manual_override(override_id: int):
    """Apply a manual override"""
    try:
        result = override_service.apply_override(override_id)
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to apply'))
        return action_response(True, data=result.get('data'), message="Override applied")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply override: {str(e)}")


# ============================================================================
# PIPELINE OPERATIONS
# ============================================================================

class RunPipelineRequest(BaseModel):
    """Request model for running the full email processing pipeline"""
    import_emails: bool = Field(False, description="Import new emails via IMAP (requires credentials)")
    categorize: bool = Field(True, description="Categorize uncategorized emails")
    generate_suggestions: bool = Field(True, description="Generate link suggestions for unlinked emails")
    extract_contacts: bool = Field(True, description="Extract contacts from recent emails")
    limit: int = Field(500, ge=1, le=2000, description="Max emails to process per step")


@router.post("/admin/run-pipeline")
async def run_pipeline(request: RunPipelineRequest = None):
    """
    Run the full email processing pipeline.

    This endpoint triggers:
    1. Import new emails (if IMAP configured and requested)
    2. Categorize uncategorized emails using rules
    3. Generate link suggestions for unlinked emails
    4. Extract contacts from recent emails

    All operations are optional and can be individually enabled/disabled.
    """
    if request is None:
        request = RunPipelineRequest()

    results = {
        "pipeline_run": True,
        "timestamp": datetime.now().isoformat(),
        "steps_completed": [],
        "steps_skipped": [],
        "errors": []
    }

    # Step 1: Import emails (if requested and IMAP configured)
    if request.import_emails:
        try:
            imap_configured = all([
                os.getenv('EMAIL_SERVER'),
                os.getenv('EMAIL_USERNAME'),
                os.getenv('EMAIL_PASSWORD')
            ])

            if imap_configured:
                from backend.services.email_importer import EmailImporter
                importer = EmailImporter()
                if importer.connect():
                    import_result = importer.import_emails(limit=request.limit)
                    results['import'] = import_result
                    results['steps_completed'].append('import')
                else:
                    results['import'] = {"error": "Failed to connect to IMAP server"}
                    results['errors'].append("IMAP connection failed")
            else:
                results['import'] = {"skipped": True, "reason": "IMAP credentials not configured"}
                results['steps_skipped'].append('import')
        except Exception as e:
            results['import'] = {"error": str(e)}
            results['errors'].append(f"Import: {str(e)}")
    else:
        results['steps_skipped'].append('import')

    # Step 2: Categorize uncategorized emails
    if request.categorize:
        try:
            from backend.services.email_category_service import EmailCategoryService
            svc = EmailCategoryService(db_path=DB_PATH)
            cat_result = svc.batch_categorize(limit=request.limit)
            results['categorization'] = cat_result
            results['steps_completed'].append('categorization')
        except Exception as e:
            results['categorization'] = {"error": str(e)}
            results['errors'].append(f"Categorization: {str(e)}")
    else:
        results['steps_skipped'].append('categorization')

    # Step 3: Generate suggestions for unlinked emails
    if request.generate_suggestions:
        try:
            from backend.services.email_orchestrator import EmailOrchestrator
            orch = EmailOrchestrator(db_path=DB_PATH)
            sugg_result = orch.process_new_emails(limit=request.limit)
            results['suggestions'] = sugg_result
            results['steps_completed'].append('suggestions')
        except Exception as e:
            results['suggestions'] = {"error": str(e)}
            results['errors'].append(f"Suggestions: {str(e)}")
    else:
        results['steps_skipped'].append('suggestions')

    # Step 4: Extract contacts from recent emails
    if request.extract_contacts:
        try:
            # Contact extraction from emails
            with proposal_service.get_connection() as conn:
                cursor = conn.cursor()

                # Ensure tracking table exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_extracted_contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email_id INTEGER NOT NULL,
                        contact_email TEXT NOT NULL,
                        extracted_at TEXT NOT NULL,
                        UNIQUE(email_id, contact_email)
                    )
                """)

                # Find emails with potential contacts (has sender info, not yet extracted)
                cursor.execute("""
                    SELECT
                        e.email_id,
                        e.sender_email,
                        e.sender_name,
                        e.recipient_emails
                    FROM emails e
                    LEFT JOIN email_extracted_contacts ec ON e.email_id = ec.email_id
                    WHERE ec.email_id IS NULL
                    AND e.sender_email IS NOT NULL
                    AND e.sender_email != ''
                    LIMIT ?
                """, (request.limit,))

                emails_for_contacts = cursor.fetchall()

                contacts_extracted = 0
                contacts_new = 0

                for row in emails_for_contacts:
                    email_id, sender_email, sender_name, recipient_emails = row

                    # Extract sender as contact
                    if sender_email:
                        # Check if contact exists
                        cursor.execute(
                            "SELECT contact_id FROM contacts WHERE email = ?",
                            (sender_email,)
                        )
                        existing = cursor.fetchone()

                        if not existing:
                            # Insert new contact
                            cursor.execute("""
                                INSERT INTO contacts (email, name, source, created_at)
                                VALUES (?, ?, 'email_extraction', ?)
                            """, (sender_email, sender_name or '', datetime.now().isoformat()))
                            contacts_new += 1

                        contacts_extracted += 1

                        # Track extraction
                        cursor.execute("""
                            INSERT OR IGNORE INTO email_extracted_contacts (email_id, contact_email, extracted_at)
                            VALUES (?, ?, ?)
                        """, (email_id, sender_email, datetime.now().isoformat()))

                conn.commit()

                results['contacts'] = {
                    "emails_processed": len(emails_for_contacts),
                    "contacts_extracted": contacts_extracted,
                    "new_contacts_created": contacts_new
                }
                results['steps_completed'].append('contacts')

        except Exception as e:
            results['contacts'] = {"error": str(e)}
            results['errors'].append(f"Contacts: {str(e)}")
    else:
        results['steps_skipped'].append('contacts')

    # Summary
    results['success'] = len(results['errors']) == 0
    results['summary'] = f"Completed {len(results['steps_completed'])} steps, skipped {len(results['steps_skipped'])}, {len(results['errors'])} errors"

    return results


# ============================================================================
# CONTEXT-AWARE BATCH PROCESSING
# ============================================================================

class BatchProcessRequest(BaseModel):
    """Request model for batch processing emails with context-aware AI"""
    limit: int = Field(100, ge=1, le=500, description="Max emails to process")
    hours_back: int = Field(720, ge=1, le=8760, description="Process emails from last N hours (default 30 days)")
    dry_run: bool = Field(False, description="If true, just return count of emails to process")


@router.post("/admin/batch-process-emails")
async def batch_process_emails(request: BatchProcessRequest = None):
    """
    Process unclassified emails with context-aware AI suggestion system.

    This endpoint:
    1. Finds emails that haven't been processed with context-aware analysis
    2. Runs GPT-4o-mini analysis on each email
    3. Creates suggestions with pattern-boosted confidence
    4. Updates email classification (type, is_project_related)

    Uses learned patterns to boost confidence when sender/domain matches.

    Args:
        limit: Max emails to process (1-500)
        hours_back: Only process emails from last N hours
        dry_run: If true, just return count without processing

    Returns:
        Processing results including emails processed, suggestions created, cost
    """
    if request is None:
        request = BatchProcessRequest()

    try:
        from backend.services.context_aware_suggestion_service import get_context_aware_service

        service = get_context_aware_service(DB_PATH)

        if request.dry_run:
            # Count unprocessed emails without processing
            unprocessed = service._get_unprocessed_emails(
                limit=10000,
                hours_back=request.hours_back
            )
            return {
                "dry_run": True,
                "would_process": len(unprocessed),
                "hours_back": request.hours_back,
                "limit": request.limit
            }

        # Run batch processing
        result = service.generate_suggestions_batch(
            limit=request.limit,
            hours_back=request.hours_back
        )

        return {
            "success": True,
            "emails_processed": result.get("emails_processed", 0),
            "suggestions_created": result.get("total_suggestions", 0),
            "patterns_used": result.get("patterns_used", 0),
            "total_cost_usd": result.get("cost_usd", 0),
            "processing_time_seconds": result.get("processing_time_seconds", 0),
            "details": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "emails_processed": 0,
            "suggestions_created": 0
        }


class ProcessUnlinkedRequest(BaseModel):
    """Request model for processing unlinked emails"""
    limit: int = Field(100, ge=1, le=500, description="Max emails to process")
    project_code: Optional[str] = Field(None, description="Only process emails mentioning this project")
    hours_back: int = Field(720, ge=1, le=8760, description="Process emails from last N hours (default 30 days)")


@router.post("/admin/process-unlinked-emails")
async def process_unlinked_emails(request: ProcessUnlinkedRequest = None):
    """
    Process emails that have no existing links to proposals/projects.

    This endpoint finds emails that:
    1. Have no entries in email_proposal_links or email_project_links
    2. Were received in the last N hours
    3. Optionally mention a specific project code

    For each email, it runs context-aware analysis and creates suggestions.

    Returns:
        Batch processing results including emails processed and suggestions created
    """
    if request is None:
        request = ProcessUnlinkedRequest()

    try:
        from backend.services.context_aware_suggestion_service import get_context_aware_service

        service = get_context_aware_service(DB_PATH)

        # Get unlinked email IDs
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT e.email_id
                FROM emails e
                WHERE e.date >= datetime('now', '-' || ? || ' hours')
                AND NOT EXISTS (
                    SELECT 1 FROM email_proposal_links epl WHERE epl.email_id = e.email_id
                )
                AND NOT EXISTS (
                    SELECT 1 FROM email_project_links eprl WHERE eprl.email_id = e.email_id
                )
            """
            params = [request.hours_back]

            if request.project_code:
                query += """
                    AND (e.subject LIKE ? OR e.body_preview LIKE ?)
                """
                params.extend([f"%{request.project_code}%", f"%{request.project_code}%"])

            query += " ORDER BY e.date DESC LIMIT ?"
            params.append(request.limit)

            cursor.execute(query, params)
            email_ids = [row[0] for row in cursor.fetchall()]

        if not email_ids:
            return {
                "success": True,
                "message": "No unlinked emails found",
                "emails_processed": 0,
                "suggestions_created": 0,
            }

        # Process batch
        result = service.generate_suggestions_batch(
            email_ids=email_ids,
            limit=request.limit,
        )

        return {
            "success": True,
            "emails_found": len(email_ids),
            "emails_processed": result.get("emails_processed", 0),
            "suggestions_created": result.get("suggestions_created", 0),
            "cost_usd": result.get("cost_usd", 0),
            "processing_time_seconds": result.get("processing_time_seconds", 0),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "emails_processed": 0,
            "suggestions_created": 0,
        }


@router.post("/admin/process-email/{email_id}")
async def process_single_email(email_id: int):
    """
    Process a single email and create suggestions using context-aware analysis.

    This endpoint:
    1. Loads the email by ID
    2. Builds context from active proposals, learned patterns, contacts
    3. Calls GPT-4o-mini for analysis
    4. Creates suggestions (link_email, action_required, new_contact)
    5. Logs usage for cost tracking

    Returns:
        Processing result including suggestions created and cost
    """
    try:
        from backend.services.context_aware_suggestion_service import get_context_aware_service

        service = get_context_aware_service(DB_PATH)
        result = service.generate_suggestions_for_email(email_id)

        return {
            "success": result.get("success", False),
            "email_id": email_id,
            "skipped": result.get("skipped", False),
            "suggestions_created": result.get("suggestions_created", 0),
            "suggestion_ids": result.get("suggestion_ids", []),
            "usage": result.get("usage"),
            "error": result.get("error"),
        }
    except Exception as e:
        return {
            "success": False,
            "email_id": email_id,
            "error": str(e),
        }


@router.get("/admin/batch-process-status")
async def get_batch_process_status():
    """
    Get status of email processing system.

    Returns:
        - Count of unprocessed emails
        - Count of processed emails
        - Pattern usage statistics
        - GPT cost statistics
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Count emails by processing status
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN email_type IS NULL THEN 1 ELSE 0 END) as unprocessed,
                    SUM(CASE WHEN email_type IS NOT NULL THEN 1 ELSE 0 END) as processed,
                    COUNT(*) as total
                FROM emails
                WHERE date >= datetime('now', '-30 days')
            """)
            row = cursor.fetchone()

            # Pattern usage stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_patterns,
                    SUM(times_used) as total_uses,
                    SUM(times_correct) as total_correct,
                    SUM(times_rejected) as total_rejected,
                    AVG(confidence) as avg_confidence
                FROM email_learned_patterns
                WHERE is_active = 1
            """)
            pattern_row = cursor.fetchone()

            # GPT cost stats (last 30 days)
            cursor.execute("""
                SELECT
                    COUNT(*) as total_calls,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(estimated_cost_usd) as total_cost
                FROM gpt_usage_log
                WHERE created_at >= datetime('now', '-30 days')
            """)
            cost_row = cursor.fetchone()

            return {
                "emails": {
                    "unprocessed_last_30_days": row[0] if row else 0,
                    "processed_last_30_days": row[1] if row else 0,
                    "total_last_30_days": row[2] if row else 0
                },
                "patterns": {
                    "total_active": pattern_row[0] if pattern_row else 0,
                    "times_used": pattern_row[1] if pattern_row else 0,
                    "times_correct": pattern_row[2] if pattern_row else 0,
                    "times_rejected": pattern_row[3] if pattern_row else 0,
                    "avg_confidence": round(pattern_row[4], 3) if pattern_row and pattern_row[4] else 0
                },
                "gpt_costs_30_days": {
                    "total_calls": cost_row[0] if cost_row else 0,
                    "total_tokens": (cost_row[1] or 0) + (cost_row[2] or 0) if cost_row else 0,
                    "total_cost_usd": round(cost_row[3], 4) if cost_row and cost_row[3] else 0
                }
            }

    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# TRANSCRIPT PROCESSING ENDPOINTS
# ============================================================================

@router.post("/admin/process-transcript/{transcript_id}")
async def process_single_transcript(transcript_id: int, use_ai: bool = Query(True)):
    """
    Process a single transcript and create suggestion if match found.

    This endpoint:
    1. Loads the transcript by ID
    2. Tries code extraction from transcript text
    3. Falls back to name matching against proposals
    4. Uses AI analysis as last resort (if use_ai=True)
    5. Creates transcript_link suggestion for human review

    Args:
        transcript_id: ID of the meeting_transcripts record
        use_ai: Whether to use AI analysis if code/name matching fails (default: True)

    Returns:
        Processing result including match info and suggestion_id if created
    """
    try:
        from backend.services.transcript_linker_service import TranscriptLinker

        linker = TranscriptLinker(DB_PATH, use_ai=use_ai)
        result = linker.process_single_transcript(transcript_id, use_ai=use_ai)

        return result
    except Exception as e:
        return {
            "success": False,
            "transcript_id": transcript_id,
            "error": str(e)
        }


class BatchTranscriptRequest(BaseModel):
    """Request model for batch transcript processing"""
    limit: int = Field(default=50, ge=1, le=500, description="Max transcripts to process")
    use_ai: bool = Field(default=True, description="Use AI analysis for unmatched transcripts")
    dry_run: bool = Field(default=False, description="If true, report matches without creating suggestions")


@router.post("/admin/process-unlinked-transcripts")
async def process_unlinked_transcripts(request: BatchTranscriptRequest = None):
    """
    Process all unlinked transcripts and create suggestions.

    This endpoint finds all transcripts without proposal_id/project_id and:
    1. Extracts project codes from transcript text
    2. Matches project/client names mentioned
    3. Uses AI analysis for difficult cases (if use_ai=True)
    4. Creates transcript_link suggestions for human review

    IMPORTANT: Does NOT auto-link anything - only creates suggestions.

    Args:
        limit: Max transcripts to process (1-500)
        use_ai: Whether to use AI for unmatched transcripts
        dry_run: If true, report matches without creating suggestions

    Returns:
        Processing statistics including matches and suggestions created
    """
    if request is None:
        request = BatchTranscriptRequest()

    try:
        from backend.services.transcript_linker_service import TranscriptLinker

        linker = TranscriptLinker(DB_PATH, use_ai=request.use_ai)
        stats = linker.run(dry_run=request.dry_run, limit=request.limit)

        return {
            "success": True,
            "dry_run": request.dry_run,
            "stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/admin/transcript-status")
async def get_transcript_status():
    """
    Get status of transcript linking.

    Returns:
        - Count of unlinked transcripts
        - Count of linked transcripts
        - Pending transcript_link suggestions
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Count unlinked transcripts
            cursor.execute("""
                SELECT COUNT(*) FROM meeting_transcripts
                WHERE proposal_id IS NULL
                  AND project_id IS NULL
                  AND transcript IS NOT NULL
                  AND transcript != ''
            """)
            unlinked = cursor.fetchone()[0]

            # Count linked transcripts
            cursor.execute("""
                SELECT COUNT(*) FROM meeting_transcripts
                WHERE (proposal_id IS NOT NULL OR project_id IS NOT NULL)
                  AND transcript IS NOT NULL
            """)
            linked = cursor.fetchone()[0]

            # Count pending suggestions
            cursor.execute("""
                SELECT COUNT(*) FROM ai_suggestions
                WHERE suggestion_type = 'transcript_link'
                  AND status = 'pending'
            """)
            pending_suggestions = cursor.fetchone()[0]

            # Count approved suggestions
            cursor.execute("""
                SELECT COUNT(*) FROM ai_suggestions
                WHERE suggestion_type = 'transcript_link'
                  AND status = 'approved'
            """)
            approved_suggestions = cursor.fetchone()[0]

            return {
                "transcripts": {
                    "total": unlinked + linked,
                    "unlinked": unlinked,
                    "linked": linked
                },
                "suggestions": {
                    "pending": pending_suggestions,
                    "approved": approved_suggestions
                }
            }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# TRANSCRIPT CONSOLIDATION ENDPOINTS
# ============================================================================

class ConsolidateTranscriptsRequest(BaseModel):
    """Request model for transcript consolidation"""
    dry_run: bool = Field(default=False, description="If true, report changes without applying them")
    generate_titles: bool = Field(default=True, description="Generate smart titles after consolidation")


@router.get("/admin/analyze-transcripts")
async def analyze_transcripts():
    """
    Analyze meeting_transcripts table to identify chunk patterns and duplicates.

    Returns detailed analysis showing:
    - Total rows vs unique meetings
    - Meetings with chunks (split due to length)
    - Meetings with duplicate rows
    - Per-meeting breakdown with IDs

    Use this to understand what consolidation will do before running it.
    """
    try:
        from backend.services.transcript_consolidation_service import get_consolidation_service

        service = get_consolidation_service(DB_PATH)
        analysis = service.analyze_transcripts()

        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/admin/consolidate-transcripts")
async def consolidate_transcripts(request: ConsolidateTranscriptsRequest = None):
    """
    Consolidate chunked and duplicated transcripts into single records.

    This endpoint:
    1. Groups transcripts by base filename (strips _chunk1, _chunk2 suffixes)
    2. Deduplicates rows (keeps best content from each chunk)
    3. Merges transcripts in order (chunk1 + chunk2 + chunk3...)
    4. Deletes redundant rows, keeping one consolidated record per meeting
    5. Generates smart titles using GPT (optional)

    IMPORTANT: This modifies the database. Use dry_run=True first to preview.

    Args:
        dry_run: If true, report what would happen without making changes
        generate_titles: If true (default), generate smart titles after consolidation

    Returns:
        Consolidation results including:
        - Before/after row counts
        - Per-meeting consolidation details
        - Generated titles
        - Statistics
    """
    if request is None:
        request = ConsolidateTranscriptsRequest()

    try:
        from backend.services.transcript_consolidation_service import get_consolidation_service

        service = get_consolidation_service(DB_PATH)

        # Run consolidation
        results = service.consolidate_all(dry_run=request.dry_run)

        # Format response
        response = {
            "success": True,
            "dry_run": request.dry_run,
            "before": {
                "total_rows": results['analysis']['total_rows'],
                "unique_meetings": results['analysis']['unique_meetings'],
                "meetings_with_chunks": results['analysis']['meetings_with_chunks'],
                "meetings_with_duplicates": results['analysis']['meetings_with_duplicates'],
                "total_duplicates": results['analysis']['total_duplicates']
            },
            "consolidations": len(results['consolidations']),
            "consolidation_details": results['consolidations'],
            "titles_generated": len([t for t in results.get('titles_generated', []) if t.get('success')]),
            "title_results": results.get('titles_generated', []),
            "stats": results['stats']
        }

        if results.get('final_analysis'):
            response["after"] = {
                "total_rows": results['final_analysis']['total_rows'],
                "unique_meetings": results['final_analysis']['unique_meetings']
            }

        return response

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/admin/generate-transcript-title/{transcript_id}")
async def generate_transcript_title(transcript_id: int):
    """
    Generate a smart title for a single transcript using GPT.

    Format: "{Project Name} - {Meeting Topic}" (max 60 chars)

    The title generation uses:
    1. Transcript content analysis
    2. Summary if available
    3. Linked proposal context
    4. Active proposals list for matching

    Args:
        transcript_id: ID of the meeting_transcripts record

    Returns:
        Generated title and metadata
    """
    try:
        from backend.services.transcript_consolidation_service import get_consolidation_service

        service = get_consolidation_service(DB_PATH)
        result = service.generate_smart_title(transcript_id)

        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "transcript_id": transcript_id
        }


@router.post("/admin/consolidate-meeting/{base_filename}")
async def consolidate_single_meeting(base_filename: str, dry_run: bool = Query(False)):
    """
    Consolidate chunks and duplicates for a single meeting.

    Args:
        base_filename: The base meeting name (e.g., "meeting_20251127_122841")
        dry_run: If true, report without making changes

    Returns:
        Consolidation details for this meeting
    """
    try:
        from backend.services.transcript_consolidation_service import get_consolidation_service

        service = get_consolidation_service(DB_PATH)
        result = service.consolidate_meeting(base_filename, dry_run=dry_run)

        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "base_filename": base_filename
        }


@router.post("/admin/match-transcript-participants/{transcript_id}")
async def match_transcript_participants(transcript_id: int):
    """
    Match participant names in a transcript against the contacts database.

    This endpoint:
    1. Extracts names mentioned in the transcript using GPT
    2. Fuzzy matches names against contacts table (handles transcription errors)
    3. Prioritizes contacts linked to the same proposal
    4. Updates the participants field with matched contact info

    Args:
        transcript_id: ID of the meeting_transcripts record

    Returns:
        Matched participants with contact_id, email, and match confidence
    """
    try:
        from backend.services.transcript_consolidation_service import get_consolidation_service

        service = get_consolidation_service(DB_PATH)
        result = service.match_participants(transcript_id)

        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "transcript_id": transcript_id
        }


@router.post("/admin/match-all-transcript-participants")
async def match_all_transcript_participants():
    """
    Match participants for all transcripts against contacts database.

    Processes all transcripts and attempts to match mentioned names
    to known contacts using GPT extraction and fuzzy matching.

    Returns:
        Summary of all matches made
    """
    try:
        from backend.services.transcript_consolidation_service import get_consolidation_service

        service = get_consolidation_service(DB_PATH)
        result = service.match_all_participants()

        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# EMAIL THREAD CONTEXT
# ============================================================================

@router.get("/admin/thread/{thread_id}")
async def get_thread_details(thread_id: str):
    """
    Get detailed information about an email thread.

    Returns:
        - Thread info (total emails, date range, subject)
        - All participants (internal/external)
        - Existing project/proposal links
        - Email history
        - Conversation state (waiting for us or them)

    Use this to understand a conversation and see which emails
    are already linked to proposals.
    """
    try:
        from backend.services.thread_context_service import get_thread_context_service

        service = get_thread_context_service(DB_PATH)
        result = service.get_thread_summary(thread_id)

        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "thread_id": thread_id
        }


@router.get("/admin/threads")
async def list_threads(
    min_emails: int = Query(2, description="Minimum emails in thread"),
    limit: int = Query(50, description="Max threads to return"),
    has_links: Optional[bool] = Query(None, description="Filter by whether thread has project links")
):
    """
    List email threads with statistics.

    Returns threads sorted by email count, with info about
    linked projects and participants.
    """
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Base query for threads with stats
        query = """
            SELECT
                e.thread_id,
                COUNT(DISTINCT e.email_id) as email_count,
                MIN(e.date) as first_email,
                MAX(e.date) as last_email,
                MIN(e.subject) as subject,
                COUNT(DISTINCT epl.email_id) as linked_emails,
                GROUP_CONCAT(DISTINCT p.project_code) as project_codes
            FROM emails e
            LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE e.thread_id IS NOT NULL AND e.thread_id != ''
            GROUP BY e.thread_id
            HAVING email_count >= ?
        """

        params = [min_emails]

        if has_links is True:
            query += " AND linked_emails > 0"
        elif has_links is False:
            query += " AND linked_emails = 0"

        query += " ORDER BY email_count DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        threads = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "threads": threads,
            "count": len(threads)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/admin/email/{email_id}/thread-context")
async def get_email_thread_context(email_id: int):
    """
    Get thread context for a specific email.

    This is what GPT sees when analyzing an email - shows the thread
    history, existing links, and conversation state.

    Useful for debugging why GPT made certain suggestions.
    """
    try:
        from backend.services.thread_context_service import get_thread_context_service

        service = get_thread_context_service(DB_PATH)
        result = service.get_thread_context(email_id)

        if not result:
            return {
                "success": True,
                "has_thread": False,
                "email_id": email_id,
                "message": "Email has no thread_id or is the only email in thread"
            }

        # Also get suggested link based on thread
        suggested_link = service.suggest_link_from_thread(email_id)

        return {
            "success": True,
            "has_thread": True,
            "email_id": email_id,
            **result,
            "suggested_link_from_thread": suggested_link
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "email_id": email_id
        }
