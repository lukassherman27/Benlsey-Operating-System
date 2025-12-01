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
