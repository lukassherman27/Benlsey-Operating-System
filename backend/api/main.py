#!/usr/bin/env python3
"""
Bensley Intelligence Platform - FastAPI Backend

Updated to use service layer and correct database schema.
Start with: uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
Access docs at: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from services.proposal_service import ProposalService
from services.email_service import EmailService
from services.milestone_service import MilestoneService
from services.financial_service import FinancialService
from services.rfi_service import RFIService
from services.file_service import FileService
from services.context_service import ContextService
from services.meeting_service import MeetingService
from services.outreach_service import OutreachService
from services.override_service import OverrideService
from services.training_service import TrainingService
from services.proposal_query_service import ProposalQueryService

# Initialize FastAPI app
app = FastAPI(
    title="Bensley Intelligence API",
    description="AI-powered operations platform for Bensley Design Studios",
    version="2.0.0"
)

# Add CORS middleware for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get database path
DB_PATH = os.path.expanduser("~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db")

# Initialize services
proposal_service = ProposalService()
email_service = EmailService()
milestone_service = MilestoneService(DB_PATH)
financial_service = FinancialService(DB_PATH)
rfi_service = RFIService(DB_PATH)
file_service = FileService(DB_PATH)
context_service = ContextService(DB_PATH)
meeting_service = MeetingService(DB_PATH)
outreach_service = OutreachService(DB_PATH)
override_service = OverrideService(DB_PATH)
training_service = TrainingService(DB_PATH)
proposal_query_service = ProposalQueryService()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class DashboardStatsResponse(BaseModel):
    """Dashboard statistics"""
    total_proposals: int
    active_projects: int
    total_emails: int
    categorized_emails: int
    needs_review: int
    total_attachments: int
    training_progress: Dict[str, Any]
    proposals: Dict[str, int]  # Proposal counts breakdown
    revenue: Dict[str, float]  # Revenue breakdown

class ProposalResponse(BaseModel):
    """Proposal response model"""
    proposal_id: int
    project_code: str
    project_name: str
    status: Optional[str] = None
    health_score: Optional[float] = None
    days_since_contact: Optional[int] = None
    is_active_project: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class EmailResponse(BaseModel):
    """Email response model"""
    email_id: int
    subject: str
    sender_email: str
    date: str
    snippet: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    importance_score: Optional[float] = None
    project_code: Optional[str] = None

class CreateProposalRequest(BaseModel):
    """Request model for creating a new proposal"""
    project_code: str = Field(..., description="Project code (e.g., '25 BK-099')")
    project_name: str = Field(..., description="Project name")
    estimated_fee_usd: Optional[float] = Field(None, description="Estimated fee in USD")
    proposal_submitted_date: Optional[str] = Field(None, description="Date proposal was submitted (YYYY-MM-DD)")
    decision_expected_date: Optional[str] = Field(None, description="Expected decision date (YYYY-MM-DD)")
    win_probability: Optional[float] = Field(None, ge=0, le=100, description="Win probability (0-100)")
    status: str = Field(default="proposal", description="Status (default: 'proposal')")
    is_active_project: int = Field(default=0, description="0 for pipeline proposal, 1 for active project")
    client_name: Optional[str] = Field(None, description="Client name")
    description: Optional[str] = Field(None, description="Optional notes/description")

    @validator('win_probability')
    def validate_win_probability(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('win_probability must be between 0 and 100')
        return v

class UpdateProposalRequest(BaseModel):
    """Request model for updating an existing proposal"""
    project_name: Optional[str] = Field(None, description="Project name")
    total_fee_usd: Optional[float] = Field(None, description="Total fee or estimated value")
    status: Optional[str] = Field(None, description="Status (e.g., 'proposal', 'active_project', 'completed')")
    is_active_project: Optional[int] = Field(None, description="0 for pipeline proposal, 1 for active project")
    win_probability: Optional[float] = Field(None, ge=0, le=100, description="Win probability (0-100)")
    proposal_submitted_date: Optional[str] = Field(None, description="Date proposal was submitted (YYYY-MM-DD)")
    decision_expected_date: Optional[str] = Field(None, description="Expected decision date (YYYY-MM-DD)")
    contract_signed_date: Optional[str] = Field(None, description="Contract signed date (YYYY-MM-DD)")
    next_action: Optional[str] = Field(None, description="Next action or milestone")
    client_name: Optional[str] = Field(None, description="Client name")
    description: Optional[str] = Field(None, description="Notes/description")
    paid_to_date_usd: Optional[float] = Field(None, description="Amount paid to date")

    @validator('win_probability')
    def validate_win_probability(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('win_probability must be between 0 and 100')
        return v

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Bensley Intelligence Platform API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "dashboard": "/api/dashboard/stats",
            "proposals": "/api/proposals",
            "emails": "/api/emails",
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection by getting proposal count
        proposal_stats = proposal_service.get_dashboard_stats()
        email_stats = email_service.get_email_stats()

        return {
            "status": "healthy",
            "database": "connected",
            "proposals_in_db": proposal_stats.get('total_proposals', 0),
            "emails_in_db": email_stats.get('total_emails', 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.get("/api/briefing/daily")
async def get_daily_briefing():
    """
    Executive daily briefing - actionable intelligence for Bill

    Returns prioritized list of what needs attention today,
    business health summary, and insights.
    """
    try:
        from datetime import datetime, timedelta

        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Get all proposals with health metrics
            cursor.execute("""
                SELECT proposal_id, project_code, project_name, status,
                       health_score, days_since_contact, last_contact_date,
                       next_action, outstanding_usd, total_fee_usd
                FROM projects
                WHERE is_active_project = 1 AND status = 'proposal'
                ORDER BY health_score ASC NULLS LAST
            """)

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_name": row[2],
                    "status": row[3],
                    "health_score": row[4],
                    "days_since_contact": row[5],
                    "last_contact_date": row[6],
                    "next_action": row[7],
                    "outstanding_usd": row[8],
                    "total_fee_usd": row[9]
                })

            # Categorize urgent items
            urgent = []
            needs_attention = []

            for p in proposals:
                days = p["days_since_contact"] or 999

                # URGENT: No contact in 18+ days
                if days >= 18:
                    urgent.append({
                        "type": "no_contact",
                        "priority": "high",
                        "project_code": p["project_code"],
                        "project_name": p["project_name"],
                        "action": f"Call client - {p['next_action'] or 'follow up'}",
                        "context": f"{days} days no contact",
                        "detail": p["next_action"] or "Check project status"
                    })

                # NEEDS ATTENTION: 7-17 days
                elif days >= 7:
                    needs_attention.append({
                        "type": "follow_up",
                        "project_code": p["project_code"],
                        "project_name": p["project_name"],
                        "action": f"Follow up: {p['next_action'] or 'contact client'}",
                        "context": f"{days} days since last contact"
                    })

            # Business health calculation
            at_risk = len([p for p in proposals if p["health_score"] and p["health_score"] < 50])
            total_outstanding = sum([p["outstanding_usd"] or 0 for p in proposals])
            total_revenue = sum([p["total_fee_usd"] or 0 for p in proposals])

            # Determine overall health status
            risk_percent = (at_risk / len(proposals) * 100) if proposals else 0
            if risk_percent > 30 or total_outstanding > total_revenue * 0.5:
                health_status = "needs_attention"
            elif risk_percent > 15:
                health_status = "caution"
            else:
                health_status = "healthy"

            # Generate insights
            insights = []
            if at_risk > 0:
                insights.append(f"{at_risk} projects need immediate attention")
            if total_outstanding > 1000000:
                insights.append(f"${total_outstanding/1000000:.1f}M outstanding - review payment schedule")

            # Recent wins (emails received this week, approvals, etc.)
            wins = []
            # TODO: Add logic for detecting wins from emails/payments

            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "business_health": {
                    "status": health_status,
                    "summary": f"{at_risk} projects at risk, ${total_outstanding/1000000:.1f}M outstanding"
                },
                "urgent": urgent[:5],  # Top 5 most urgent
                "needs_attention": needs_attention[:10],
                "insights": insights,
                "wins": wins,
                "metrics": {
                    "total_projects": len(proposals),
                    "at_risk": at_risk,
                    "revenue": total_revenue,
                    "outstanding": total_outstanding
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate daily briefing: {str(e)}")

@app.get("/api/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats():
    """
    Get real-time dashboard statistics

    Returns:
        - Total proposals count
        - Active projects count
        - At-risk and follow-up counts
        - Total emails count
        - Categorized emails count
        - Emails needing review (category='general')
        - Total attachments count
        - Training progress stats
        - Revenue breakdown (total contracts, paid, outstanding, remaining)
    """
    try:
        # Get proposal statistics
        proposal_stats = proposal_service.get_dashboard_stats()

        # Get email statistics
        email_stats = email_service.get_email_stats()

        # Get training data progress and attachments
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Count human-verified training samples
            cursor.execute("""
                SELECT COUNT(*) FROM training_data
                WHERE human_verified = 1
            """)
            verified_count = cursor.fetchone()[0] or 0

            # Count total training samples
            cursor.execute("SELECT COUNT(*) FROM training_data")
            total_training = cursor.fetchone()[0] or 0

            # Count attachments
            cursor.execute("SELECT COUNT(*) FROM email_attachments")
            attachment_count = cursor.fetchone()[0] or 0

            # Count emails needing review (category='general')
            cursor.execute("""
                SELECT COUNT(*) FROM email_content
                WHERE category = 'general'
            """)
            needs_review_count = cursor.fetchone()[0] or 0

            # Count at-risk proposals (health_score < 50)
            cursor.execute("""
                SELECT COUNT(*) FROM projects
                WHERE health_score IS NOT NULL AND health_score < 50
                AND is_active_project = 1 AND status = 'proposal'
            """)
            at_risk_count = cursor.fetchone()[0] or 0

            # Count proposals needing follow-up (14+ days no contact)
            cursor.execute("""
                SELECT COUNT(*) FROM projects
                WHERE days_since_contact >= 14
                AND is_active_project = 1 AND status = 'proposal'
            """)
            needs_follow_up_count = cursor.fetchone()[0] or 0

            # Get revenue breakdown from active projects
            cursor.execute("""
                SELECT
                    SUM(total_fee_usd) as total_contracts,
                    SUM(paid_to_date_usd) as paid,
                    SUM(outstanding_usd) as outstanding,
                    SUM(remaining_work_usd) as remaining
                FROM projects
                WHERE is_active_project = 1 AND status = 'proposal'
            """)
            revenue_row = cursor.fetchone()

        # Calculate training progress
        training_goal = 5000
        training_progress = {
            "verified": verified_count,
            "total": total_training,
            "goal": training_goal,
            "percentage": round((verified_count / training_goal) * 100, 1) if training_goal > 0 else 0
        }

        # Proposal breakdown
        proposals_breakdown = {
            "total": proposal_stats.get('total_proposals', 0),
            "active": proposal_stats.get('active_projects', 0),
            "at_risk": at_risk_count,
            "needs_follow_up": needs_follow_up_count
        }

        # Revenue breakdown
        revenue_breakdown = {
            "total_contracts": round(revenue_row[0] or 0.0, 2),
            "paid": round(revenue_row[1] or 0.0, 2),
            "outstanding": round(revenue_row[2] or 0.0, 2),
            "remaining": round(revenue_row[3] or 0.0, 2)
        }

        return DashboardStatsResponse(
            total_proposals=proposal_stats.get('total_proposals', 0),
            active_projects=proposal_stats.get('active_projects', 0),
            total_emails=email_stats.get('total_emails', 0),
            categorized_emails=email_stats.get('processed', 0),
            needs_review=needs_review_count,
            total_attachments=attachment_count,
            training_progress=training_progress,
            proposals=proposals_breakdown,
            revenue=revenue_breakdown
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

# ============================================================================
# PROPOSAL ENDPOINTS
# ============================================================================

@app.post("/api/proposals", status_code=201)
async def create_proposal(request: CreateProposalRequest):
    """
    Create a new proposal

    Creates a pipeline proposal that can later be converted to an active project.
    Validates project_code uniqueness and win_probability range.
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Check if project_code already exists
            cursor.execute("SELECT proposal_id FROM projects WHERE project_code = ?", (request.project_code,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Project code '{request.project_code}' already exists")

            # Insert new proposal
            cursor.execute("""
                INSERT INTO projects (
                    project_code, project_name, total_fee_usd,
                    proposal_submitted_date, decision_expected_date, win_probability,
                    status, is_active_project, client_name, description,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                request.project_code,
                request.project_name,
                request.estimated_fee_usd,
                request.proposal_submitted_date,
                request.decision_expected_date,
                request.win_probability,
                request.status,
                request.is_active_project,
                request.client_name,
                request.description
            ))

            proposal_id = cursor.lastrowid
            conn.commit()

            # Fetch the created proposal
            cursor.execute("""
                SELECT proposal_id, project_code, project_name, status,
                       total_fee_usd, win_probability, is_active_project,
                       proposal_submitted_date, decision_expected_date,
                       client_name, description, created_at
                FROM projects WHERE proposal_id = ?
            """, (proposal_id,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to retrieve created proposal")

            return {
                "proposal_id": row[0],
                "project_code": row[1],
                "project_name": row[2],
                "status": row[3],
                "estimated_fee_usd": row[4],
                "win_probability": row[5],
                "is_active_project": row[6],
                "proposal_submitted_date": row[7],
                "decision_expected_date": row[8],
                "client_name": row[9],
                "description": row[10],
                "created_at": row[11]
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create proposal: {str(e)}")

@app.patch("/api/proposals/{identifier}")
async def update_proposal(identifier: str, request: UpdateProposalRequest):
    """
    Update an existing proposal

    Supports partial updates - only provided fields will be changed.
    Use this to convert proposals to active projects or update any field.

    Args:
        identifier: Proposal ID (int) or Project Code (string like "BK-033")
        request: Fields to update (all optional)
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Find the proposal
            try:
                proposal_id = int(identifier)
                cursor.execute("SELECT proposal_id FROM projects WHERE proposal_id = ?", (proposal_id,))
            except ValueError:
                cursor.execute("SELECT proposal_id FROM projects WHERE project_code = ?", (identifier,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Proposal not found")

            proposal_id = row[0]

            # Build UPDATE query dynamically based on provided fields
            updates = []
            params = []

            for field, value in request.dict(exclude_unset=True).items():
                if value is not None:
                    updates.append(f"{field} = ?")
                    params.append(value)

            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")

            # Always update the updated_at timestamp
            updates.append("updated_at = datetime('now')")
            params.append(proposal_id)

            query = f"UPDATE projects SET {', '.join(updates)} WHERE proposal_id = ?"
            cursor.execute(query, params)
            conn.commit()

            # Fetch and return updated proposal
            cursor.execute("""
                SELECT proposal_id, project_code, project_name, status,
                       total_fee_usd, win_probability, is_active_project,
                       proposal_submitted_date, decision_expected_date,
                       contract_signed_date, next_action, client_name,
                       description, paid_to_date_usd, updated_at
                FROM projects WHERE proposal_id = ?
            """, (proposal_id,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated proposal")

            return {
                "proposal_id": row[0],
                "project_code": row[1],
                "project_name": row[2],
                "status": row[3],
                "total_fee_usd": row[4],
                "win_probability": row[5],
                "is_active_project": row[6],
                "proposal_submitted_date": row[7],
                "decision_expected_date": row[8],
                "contract_signed_date": row[9],
                "next_action": row[10],
                "client_name": row[11],
                "description": row[12],
                "paid_to_date_usd": row[13],
                "updated_at": row[14]
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update proposal: {str(e)}")

@app.get("/api/proposals")
async def list_proposals(
    status: Optional[str] = None,
    is_active_project: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("health_score", regex="^(proposal_id|project_code|project_name|status|health_score|days_since_contact|is_active_project|created_at|updated_at)$"),
    sort_order: str = Query("ASC", regex="^(ASC|DESC)$")
):
    """
    List all proposals with optional filtering and pagination

    Args:
        status: Filter by status
        is_active_project: Filter by active project flag
        page: Page number (default 1)
        per_page: Results per page (default 20, max 100)
        sort_by: Column to sort by
        sort_order: ASC or DESC

    Returns:
        Paginated list of proposals
    """
    try:
        result = proposal_service.get_all_proposals(
            status=status,
            is_active_project=is_active_project,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposals: {str(e)}")

@app.get("/api/proposals/stats")
async def get_proposal_stats():
    """Get proposal statistics"""
    try:
        stats = proposal_service.get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal stats: {str(e)}")

@app.get("/api/proposals/at-risk")
async def get_at_risk_proposals(
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get proposals at risk (health_score < 50)

    Args:
        limit: Maximum number of proposals (for simple queries)
        page: Page number (for pagination)
        per_page: Results per page

    Returns:
        List of at-risk proposals sorted by health_score (lowest first)
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Count total at-risk proposals
            cursor.execute("""
                SELECT COUNT(*) FROM projects
                WHERE health_score IS NOT NULL AND health_score < 50
                AND is_active_project = 1 AND status = 'proposal'
            """)
            total = cursor.fetchone()[0] or 0

            # Get at-risk proposals with financial data
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT
                    proposal_id,
                    project_code,
                    project_name,
                    client_company,
                    health_score,
                    days_since_contact,
                    last_contact_date,
                    next_action,
                    status,
                    total_fee_usd,
                    outstanding_usd,
                    contact_person,
                    created_at,
                    updated_at
                FROM projects
                WHERE health_score IS NOT NULL AND health_score < 50
                AND is_active_project = 1 AND status = 'proposal'
                ORDER BY health_score ASC
                LIMIT ? OFFSET ?
            """, (per_page, offset))

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_name": row[2],
                    "client_company": row[3],
                    "health_score": row[4],
                    "days_since_contact": row[5],
                    "last_contact_date": row[6],
                    "next_action": row[7],
                    "status": row[8],
                    "total_fee_usd": row[9],
                    "outstanding_usd": row[10],
                    "contact_person": row[11],
                    "created_at": row[12],
                    "updated_at": row[13]
                })

            return {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
                "data": proposals[:limit] if limit < per_page else proposals
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get at-risk proposals: {str(e)}")

@app.get("/api/proposals/needs-follow-up")
async def get_needs_follow_up_proposals(
    min_days: int = Query(14, ge=1),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get proposals needing follow-up (no contact in X days)

    Args:
        min_days: Minimum days since contact (default 14)
        limit: Maximum number of proposals
        page: Page number
        per_page: Results per page

    Returns:
        List of proposals sorted by days_since_contact (most urgent first)
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Count total needing follow-up
            cursor.execute("""
                SELECT COUNT(*) FROM projects
                WHERE days_since_contact >= ?
                AND is_active_project = 1 AND status = 'proposal'
            """, (min_days,))
            total = cursor.fetchone()[0] or 0

            # Get proposals needing follow-up
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT
                    proposal_id,
                    project_code,
                    project_name,
                    client_company,
                    health_score,
                    days_since_contact,
                    last_contact_date,
                    next_action,
                    status,
                    total_fee_usd,
                    outstanding_usd,
                    contact_person,
                    created_at,
                    updated_at
                FROM projects
                WHERE days_since_contact >= ?
                AND is_active_project = 1 AND status = 'proposal'
                ORDER BY days_since_contact DESC
                LIMIT ? OFFSET ?
            """, (min_days, per_page, offset))

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_name": row[2],
                    "client_company": row[3],
                    "health_score": row[4],
                    "days_since_contact": row[5],
                    "last_contact_date": row[6],
                    "next_action": row[7],
                    "status": row[8],
                    "total_fee_usd": row[9],
                    "outstanding_usd": row[10],
                    "contact_person": row[11],
                    "created_at": row[12],
                    "updated_at": row[13]
                })

            return {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
                "min_days_threshold": min_days,
                "data": proposals[:limit] if limit < per_page else proposals
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get follow-up proposals: {str(e)}")

@app.get("/api/proposals/top-value")
async def get_top_value_proposals(
    limit: int = Query(10, ge=1, le=100),
    active_only: bool = Query(True)
):
    """
    Get highest value proposals

    Args:
        limit: Maximum number of proposals (default 10)
        active_only: Only show active projects (default True)

    Returns:
        List of proposals sorted by total_fee_usd (highest first)
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Build query
            sql = """
                SELECT
                    proposal_id,
                    project_code,
                    project_name,
                    client_company,
                    health_score,
                    days_since_contact,
                    status,
                    total_fee_usd,
                    paid_to_date_usd,
                    outstanding_usd,
                    remaining_work_usd,
                    contact_person,
                    is_active_project,
                    created_at,
                    updated_at
                FROM projects
            """

            params = []
            if active_only:
                sql += " WHERE is_active_project = 1 AND status = 'proposal'"

            sql += " ORDER BY total_fee_usd DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_name": row[2],
                    "client_company": row[3],
                    "health_score": row[4],
                    "days_since_contact": row[5],
                    "status": row[6],
                    "total_fee_usd": row[7],
                    "paid_to_date_usd": row[8],
                    "outstanding_usd": row[9],
                    "remaining_work_usd": row[10],
                    "contact_person": row[11],
                    "is_active_project": bool(row[12]),
                    "created_at": row[13],
                    "updated_at": row[14]
                })

            return {
                "total": len(proposals),
                "limit": limit,
                "active_only": active_only,
                "data": proposals
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top value proposals: {str(e)}")

@app.get("/api/proposals/recent-activity")
async def get_proposals_recent_activity(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get proposals with recent email activity

    Returns proposals that have received emails in the last N days
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Get proposals with recent emails
            cursor.execute("""
                SELECT DISTINCT
                    p.proposal_id,
                    p.project_code,
                    p.project_name,
                    e.subject as last_email_subject,
                    e.date as last_email_date
                FROM projects p
                JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
                JOIN emails e ON epl.email_id = e.email_id
                WHERE e.date >= datetime('now', '-' || ? || ' days')
                  AND p.is_active_project = 1 AND p.status = 'proposal'
                ORDER BY e.date DESC
                LIMIT ?
            """, (days, limit))

            activities = []
            for row in cursor.fetchall():
                activities.append({
                    "project_code": row[1],
                    "project_name": row[2],
                    "last_email_subject": row[3] or "",
                    "last_email_date": row[4]
                })

            return {
                "data": activities,
                "pagination": {
                    "page": 1,
                    "per_page": limit,
                    "total": len(activities),
                    "pages": 1
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent activity: {str(e)}")

@app.get("/api/proposals/{identifier}")
async def get_proposal(identifier: str):
    """
    Get detailed information about a specific proposal

    Args:
        identifier: Proposal ID (int) or Project Code (string like "BK-033")

    Returns:
        Proposal details with linked emails and timeline
    """
    try:
        # Try to parse as integer first (proposal_id)
        try:
            proposal_id = int(identifier)
            proposal = proposal_service.get_proposal_by_id(proposal_id)
        except ValueError:
            # It's a project code string
            with proposal_service.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT proposal_id, project_code, project_name, status,
                           total_fee_usd, paid_to_date_usd, outstanding_usd,
                           health_score, days_since_contact, last_contact_date,
                           next_action, contract_signed_date, is_active_project
                    FROM projects
                    WHERE project_code = ?
                """, (identifier,))
                row = cursor.fetchone()
                if row:
                    proposal = {
                        "proposal_id": row[0],
                        "project_code": row[1],
                        "project_name": row[2],
                        "status": row[3],
                        "total_fee_usd": row[4],
                        "paid_to_date_usd": row[5],
                        "outstanding_usd": row[6],
                        "health_score": row[7],
                        "days_since_contact": row[8],
                        "last_contact_date": row[9],
                        "next_action": row[10],
                        "contract_signed_date": row[11],
                        "is_active_project": row[12]
                    }
                    proposal_id = row[0]
                else:
                    proposal = None

        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")

        # Get linked emails
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    e.email_id,
                    e.subject,
                    e.sender_email,
                    e.date,
                    e.snippet,
                    ec.category,
                    epl.confidence_score
                FROM email_proposal_links epl
                JOIN emails e ON epl.email_id = e.email_id
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE epl.proposal_id = ?
                ORDER BY e.date DESC
                LIMIT 10
            """, (proposal_id,))

            emails = []
            for row in cursor.fetchall():
                emails.append({
                    "email_id": row[0],
                    "subject": row[1],
                    "sender": row[2],
                    "date": row[3],
                    "snippet": row[4],
                    "category": row[5],
                    "confidence": row[6]
                })

        proposal['linked_emails'] = emails
        proposal['email_count'] = len(emails)

        return proposal

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal: {str(e)}")

# ============================================================================
# EMAIL ENDPOINTS
# ============================================================================

@app.get("/api/emails")
async def list_emails(
    search_query: Optional[str] = None,
    category: Optional[str] = None,
    proposal_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("date", regex="^(date|sender_email|subject|email_id)$"),
    sort_order: str = Query("DESC", regex="^(ASC|DESC)$")
):
    """
    List all emails with optional filtering and pagination

    Args:
        search_query: Search in subject and sender
        category: Filter by category
        proposal_id: Filter by linked proposal
        page: Page number (default 1)
        per_page: Results per page (default 20, max 100)
        sort_by: Column to sort by
        sort_order: ASC or DESC

    Returns:
        Paginated list of emails
    """
    try:
        result = email_service.get_all_emails(
            search_query=search_query,
            category=category,
            proposal_id=proposal_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get emails: {str(e)}")

@app.get("/api/emails/uncategorized")
async def get_uncategorized_emails(
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get emails that need categorization (category='general')

    Args:
        limit: Maximum number of emails to return (default 10, max 100)

    Returns:
        List of uncategorized emails needing review
    """
    try:
        result = email_service.get_all_emails(
            category='general',
            page=1,
            per_page=limit,
            sort_by='date',
            sort_order='DESC'
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get uncategorized emails: {str(e)}")

@app.get("/api/emails/{email_id}")
async def get_email(email_id: int):
    """
    Get detailed information about a specific email

    Args:
        email_id: Email ID

    Returns:
        Email details with content, attachments, and linked proposals
    """
    try:
        email = email_service.get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        # Get attachments and linked proposals
        with email_service.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    attachment_id,
                    filename,
                    file_type,
                    classification
                FROM email_attachments
                WHERE email_id = ?
            """, (email_id,))

            attachments = []
            for row in cursor.fetchall():
                attachments.append({
                    "attachment_id": row[0],
                    "filename": row[1],
                    "file_type": row[2],
                    "classification": row[3]
                })

            # Get linked proposals
            cursor.execute("""
                SELECT
                    p.proposal_id,
                    p.project_code,
                    p.project_name,
                    epl.confidence_score
                FROM email_proposal_links epl
                JOIN projects p ON epl.proposal_id = p.proposal_id
                WHERE epl.email_id = ?
            """, (email_id,))

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_name": row[2],
                    "confidence": row[3]
                })

        email['attachments'] = attachments
        email['linked_proposals'] = proposals

        return email

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email: {str(e)}")

@app.get("/api/emails/stats")
async def get_email_stats():
    """Get email statistics"""
    try:
        stats = email_service.get_email_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email stats: {str(e)}")

# ============================================================================
# ATTACHMENTS ENDPOINTS
# ============================================================================

@app.get("/api/attachments")
async def list_attachments(
    email_id: Optional[int] = None,
    file_type: Optional[str] = None,
    classification: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """
    List email attachments with optional filtering

    Args:
        email_id: Filter by email ID
        file_type: Filter by file type (pdf, docx, etc.)
        classification: Filter by classification
        limit: Maximum results (default 50, max 500)

    Returns:
        List of attachments
    """
    try:
        with email_service.get_connection() as conn:
            cursor = conn.cursor()

            sql = """
                SELECT
                    ea.attachment_id,
                    ea.email_id,
                    ea.filename,
                    ea.file_type,
                    ea.classification,
                    e.subject,
                    e.sender_email,
                    e.date
                FROM email_attachments ea
                JOIN emails e ON ea.email_id = e.email_id
                WHERE 1=1
            """
            params = []

            if email_id:
                sql += " AND ea.email_id = ?"
                params.append(email_id)

            if file_type:
                sql += " AND ea.file_type = ?"
                params.append(file_type)

            if classification:
                sql += " AND ea.classification = ?"
                params.append(classification)

            sql += " ORDER BY e.date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)

            attachments = []
            for row in cursor.fetchall():
                attachments.append({
                    "attachment_id": row[0],
                    "email_id": row[1],
                    "filename": row[2],
                    "file_type": row[3],
                    "classification": row[4],
                    "email_subject": row[5],
                    "email_sender": row[6],
                    "email_date": row[7]
                })

            return {
                "total": len(attachments),
                "attachments": attachments
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get attachments: {str(e)}")

# ============================================================================
# TRAINING DATA ENDPOINTS
# ============================================================================

@app.get("/api/training/stats")
async def get_training_stats():
    """Get training data statistics"""
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Overall stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN human_verified = 1 THEN 1 ELSE 0 END) as verified,
                    COUNT(DISTINCT task_type) as task_types
                FROM training_data
            """)
            row = cursor.fetchone()

            total = row[0] or 0
            verified = row[1] or 0
            task_types = row[2] or 0

            # By task type
            cursor.execute("""
                SELECT
                    task_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN human_verified = 1 THEN 1 ELSE 0 END) as verified
                FROM training_data
                GROUP BY task_type
            """)

            by_task_type = {}
            for row in cursor.fetchall():
                by_task_type[row[0]] = {
                    "total": row[1],
                    "verified": row[2]
                }

            return {
                "total_samples": total,
                "verified_samples": verified,
                "task_types_count": task_types,
                "verification_rate": round((verified / total * 100), 1) if total > 0 else 0,
                "by_task_type": by_task_type,
                "goal": 5000,
                "progress_to_goal": round((verified / 5000 * 100), 1) if verified > 0 else 0
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training stats: {str(e)}")

# ============================================================================
# OPERATIONS COMMAND CENTER ENDPOINTS
# ============================================================================

@app.get("/api/dashboard/decision-tiles")
async def get_decision_tiles():
    """
    Get decision tiles for Operations Command Center

    Returns aggregated data for:
    - Proposals needing outreach
    - Unanswered RFIs
    - Meetings due soon
    - Overdue milestones
    - Outstanding payments
    """
    try:
        # Proposals needing outreach (no contact in >14 days)
        proposals_needing_outreach = []
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT proposal_id, project_code, project_name, days_since_contact
                FROM projects
                WHERE is_active_project = 0 AND status = 'proposal'
                  AND days_since_contact > 14
                ORDER BY days_since_contact DESC
                LIMIT 10
            """)
            for row in cursor.fetchall():
                proposals_needing_outreach.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_name": row[2],
                    "days_since_contact": row[3]
                })

        # Unanswered RFIs
        unanswered_rfis = rfi_service.get_unanswered_rfis()

        # Upcoming meetings (next 7 days)
        upcoming_meetings = meeting_service.get_upcoming_meetings(days_ahead=7)

        # Overdue milestones
        overdue_milestones = milestone_service.get_overdue_milestones()

        # Overdue payments
        overdue_payments = financial_service.get_overdue_payments()

        return {
            "proposals_needing_outreach": {
                "count": len(proposals_needing_outreach),
                "items": proposals_needing_outreach
            },
            "unanswered_rfis": {
                "count": len(unanswered_rfis),
                "items": unanswered_rfis[:10]  # Limit to 10
            },
            "upcoming_meetings": {
                "count": len(upcoming_meetings),
                "items": upcoming_meetings
            },
            "overdue_milestones": {
                "count": len(overdue_milestones),
                "items": overdue_milestones[:10]
            },
            "overdue_payments": {
                "count": len(overdue_payments),
                "items": overdue_payments[:10]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get decision tiles: {str(e)}")

@app.get("/api/proposals/{identifier}/timeline")
async def get_proposal_timeline(identifier: str):
    """
    Get milestone timeline for a specific proposal
    Shows expected vs actual dates with delay tracking
    Args:
        identifier: Proposal ID (int) or Project Code (string like "BK-033")
    """
    try:
        # Convert to proposal_id
        try:
            proposal_id = int(identifier)
        except ValueError:
            # It's a project code, lookup proposal_id
            with proposal_service.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT proposal_id FROM projects WHERE project_code = ?", (identifier,))
                row = cursor.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Proposal not found")
                proposal_id = row[0]

        timeline = milestone_service.get_timeline_data(proposal_id)
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")

@app.get("/api/proposals/{identifier}/health")
async def get_proposal_health(identifier: str):
    """
    Get health metrics and breakdown for a specific proposal
    Args:
        identifier: Proposal ID (int) or Project Code (string like "BK-033")
    """
    try:
        # Get proposal by code or id
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()
            try:
                proposal_id = int(identifier)
                cursor.execute("""
                    SELECT proposal_id, project_code, project_name, health_score,
                           days_since_contact, last_contact_date, next_action
                    FROM projects WHERE proposal_id = ?
                """, (proposal_id,))
            except ValueError:
                cursor.execute("""
                    SELECT proposal_id, project_code, project_name, health_score,
                           days_since_contact, last_contact_date, next_action
                    FROM projects WHERE project_code = ?
                """, (identifier,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Proposal not found")

            return {
                "proposal_id": row[0],
                "project_code": row[1],
                "project_name": row[2],
                "health_score": row[3],
                "days_since_contact": row[4],
                "last_contact_date": row[5],
                "next_action": row[6],
                "health_factors": {
                    "email_frequency": "normal" if row[4] and row[4] < 30 else "low",
                    "response_rate": "good",
                    "engagement_trend": "stable"
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health: {str(e)}")

@app.get("/api/proposals/{proposal_id}/financials")
async def get_proposal_financials(proposal_id: int):
    """
    Get financial summary for a specific proposal
    Includes payment schedule, invoices, and outstanding amounts
    """
    try:
        financials = financial_service.get_financial_summary(proposal_id)
        return financials
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get financials: {str(e)}")

@app.get("/api/proposals/{proposal_id}/workspace")
async def get_proposal_workspace(proposal_id: int):
    """
    Get workspace data for a specific proposal
    Includes files, notes, tasks, meetings
    """
    try:
        # Get file summary
        files = file_service.get_workspace_summary(proposal_id)

        # Get context summary (notes, tasks, reminders)
        context = context_service.get_context_summary(proposal_id)

        # Get meeting summary
        meetings = meeting_service.get_meeting_summary(proposal_id)

        # Get outreach summary
        outreach = outreach_service.get_outreach_summary(proposal_id)

        return {
            "proposal_id": proposal_id,
            "files": files,
            "context": context,
            "meetings": meetings,
            "outreach": outreach
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workspace: {str(e)}")

@app.get("/api/proposals/{proposal_id}/rfis")
async def get_proposal_rfis(proposal_id: int):
    """Get all RFIs for a specific proposal"""
    try:
        rfis = rfi_service.get_rfis_by_proposal(proposal_id)
        summary = rfi_service.get_rfi_summary(proposal_id)

        return {
            "summary": summary,
            "rfis": rfis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RFIs: {str(e)}")

@app.post("/api/context/submit")
async def submit_context(
    proposal_id: int,
    context_text: str,
    context_type: str = "note",
    priority: str = "normal",
    assigned_to: Optional[str] = None,
    due_date: Optional[str] = None
):
    """
    Submit context/note for a proposal
    This is the "Command Prompt" feature that triggers agent workflows
    """
    try:
        context_id = context_service.create_context({
            "proposal_id": proposal_id,
            "context_type": context_type,
            "context_text": context_text,
            "priority": priority,
            "assigned_to": assigned_to,
            "due_date": due_date,
            "created_by": "lukas"
        })

        return {
            "success": True,
            "context_id": context_id,
            "message": "Context submitted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit context: {str(e)}")

# ============================================================================
# MILESTONE ENDPOINTS
# ============================================================================

@app.get("/api/milestones")
async def list_milestones(
    proposal_id: Optional[int] = None,
    status: Optional[str] = None
):
    """List milestones with optional filtering"""
    try:
        if proposal_id:
            milestones = milestone_service.get_milestones_by_proposal(proposal_id)
        else:
            # Get all overdue or upcoming milestones
            if status == "overdue":
                milestones = milestone_service.get_overdue_milestones()
            elif status == "upcoming":
                milestones = milestone_service.get_upcoming_milestones(days_ahead=30)
            else:
                raise HTTPException(status_code=400, detail="proposal_id or status parameter required")

        return {"total": len(milestones), "milestones": milestones}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get milestones: {str(e)}")

@app.post("/api/milestones")
async def create_milestone(
    proposal_id: int,
    milestone_type: str,
    milestone_name: str,
    expected_date: str,
    description: Optional[str] = None,
    responsible_party: Optional[str] = None
):
    """Create a new milestone"""
    try:
        milestone_id = milestone_service.create_milestone({
            "proposal_id": proposal_id,
            "milestone_type": milestone_type,
            "milestone_name": milestone_name,
            "expected_date": expected_date,
            "description": description,
            "responsible_party": responsible_party
        })

        return {"success": True, "milestone_id": milestone_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create milestone: {str(e)}")

# ============================================================================
# RFI ENDPOINTS
# ============================================================================

@app.get("/api/rfis")
async def list_rfis(
    proposal_id: Optional[int] = None,
    status: Optional[str] = None
):
    """List RFIs with optional filtering"""
    try:
        if proposal_id:
            rfis = rfi_service.get_rfis_by_proposal(proposal_id)
        elif status:
            rfis = rfi_service.get_rfis_by_status(status)
        else:
            rfis = rfi_service.get_unanswered_rfis()

        return {"total": len(rfis), "rfis": rfis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RFIs: {str(e)}")

@app.post("/api/rfis")
async def create_rfi(
    proposal_id: int,
    question: str,
    asked_by: str,
    asked_date: str,
    priority: str = "normal",
    category: Optional[str] = None
):
    """Create a new RFI"""
    try:
        rfi_id = rfi_service.create_rfi({
            "proposal_id": proposal_id,
            "question": question,
            "asked_by": asked_by,
            "asked_date": asked_date,
            "priority": priority,
            "category": category
        })

        return {"success": True, "rfi_id": rfi_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create RFI: {str(e)}")

# ============================================================================
# MEETING ENDPOINTS
# ============================================================================

@app.get("/api/meetings")
async def list_meetings(
    proposal_id: Optional[int] = None,
    upcoming: bool = False
):
    """List meetings"""
    try:
        if upcoming:
            meetings = meeting_service.get_upcoming_meetings(days_ahead=30)
        elif proposal_id:
            meetings = meeting_service.get_meetings_by_proposal(proposal_id)
        else:
            meetings = meeting_service.get_todays_meetings()

        return {"total": len(meetings), "meetings": meetings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get meetings: {str(e)}")

@app.post("/api/meetings")
async def create_meeting(
    proposal_id: int,
    meeting_type: str,
    meeting_title: str,
    scheduled_date: str,
    duration_minutes: int = 60,
    location: Optional[str] = None,
    meeting_url: Optional[str] = None
):
    """Create a new meeting"""
    try:
        meeting_id = meeting_service.create_meeting({
            "proposal_id": proposal_id,
            "meeting_type": meeting_type,
            "meeting_title": meeting_title,
            "scheduled_date": scheduled_date,
            "duration_minutes": duration_minutes,
            "location": location,
            "meeting_url": meeting_url
        })

        return {"success": True, "meeting_id": meeting_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")

# ============================================================================
# ANALYTICS & DASHBOARD ENDPOINTS (FOR CODEX FRONTEND)
# ============================================================================

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Get analytics data for dashboard overview"""
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Get proposal stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active_project = 1 THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN days_since_contact > 14 AND is_active_project = 1 THEN 1 ELSE 0 END) as need_followup,
                    SUM(CASE WHEN is_active_project = 1 AND health_score < 50 THEN 1 ELSE 0 END) as at_risk,
                    AVG(CASE WHEN is_active_project = 1 AND health_score IS NOT NULL THEN health_score ELSE NULL END) as avg_health
                FROM projects
                WHERE status = 'proposal'
            """)
            proposal_row = cursor.fetchone()

            # Get email stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN ec.category IS NOT NULL THEN 1 ELSE 0 END) as categorized
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
            """)
            email_row = cursor.fetchone()

            # Get document/attachment stats
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM attachments
            """)
            doc_row = cursor.fetchone()

            return {
                "proposals": {
                    "total": proposal_row[0] or 0,
                    "active_projects": proposal_row[1] or 0,
                    "need_followup": proposal_row[2] or 0,
                    "at_risk": proposal_row[3] or 0,
                    "avg_health_score": round(proposal_row[4], 2) if proposal_row[4] else 0.0
                },
                "emails": {
                    "total": email_row[0] or 0,
                    "categorized": email_row[1] or 0,
                    "uncategorized": (email_row[0] or 0) - (email_row[1] or 0)
                },
                "documents": {
                    "total_documents": doc_row[0] or 0
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@app.get("/api/query/suggestions")
async def get_query_suggestions():
    """Get suggested queries for the query panel"""
    return {
        "suggestions": [
            "Show me all active projects",
            "Which proposals need follow-up?",
            "List all emails from last week",
            "What's the health score distribution?"
        ]
    }

@app.get("/api/proposals/by-code/{project_code}")
async def get_proposal_by_code(project_code: str):
    """Get proposal details by project code (e.g., BK-033)"""
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects WHERE project_code = ?
            """, (project_code,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Proposal not found")

            return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal: {str(e)}")

@app.get("/api/proposals/by-code/{project_code}/health")
async def get_proposal_health_by_code(project_code: str):
    """Get proposal health metrics by project code"""
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    proposal_id,
                    project_code,
                    health_score,
                    days_since_contact,
                    status
                FROM projects
                WHERE project_code = ?
            """, (project_code,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Proposal not found")

            return {
                "proposal_id": row[0],
                "project_code": row[1],
                "health_score": row[2],
                "days_since_contact": row[3],
                "status": row[4]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal health: {str(e)}")

@app.get("/api/proposals/by-code/{project_code}/timeline")
async def get_proposal_timeline_by_code(project_code: str):
    """Get milestone timeline by project code - ENHANCED with context fields"""
    try:
        # First get proposal details
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT proposal_id, project_name, contact_person
                FROM projects
                WHERE project_code = ?
            """, (project_code,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Proposal not found")

            proposal_id, project_name, pm = row[0], row[1], row[2] or "Unassigned"

        # Get milestones with enhanced context
        milestones = milestone_service.get_milestones_by_proposal(proposal_id)

        # Enhance each milestone with context fields
        timeline_events = []
        for m in milestones:
            event = {
                "type": "milestone",
                "milestone_name": m.get("milestone_name"),
                "expected_date": m.get("expected_date"),
                "actual_date": m.get("actual_date"),
                "status": m.get("status", "pending"),

                # NEW CONTEXT FIELDS
                "delay_reason": m.get("delay_reason"),
                "delay_days": m.get("delay_days", 0),
                "responsible_party": m.get("responsible_party"),
                "milestone_owner": m.get("responsible_party") or pm or "Unassigned",
                "expected_vs_actual_days": m.get("delay_days", 0),
                "notes": m.get("notes"),
                "project_code": project_code,
                "project_name": project_name
            }
            timeline_events.append(event)

        return {
            "proposal": {
                "project_code": project_code,
                "project_name": project_name,
                "status": "active"
            },
            "timeline": timeline_events,
            "stats": {
                "timeline_events": len(timeline_events)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")

@app.get("/api/proposals/by-code/{project_code}/briefing")
async def get_proposal_briefing(project_code: str):
    """
    Comprehensive pre-meeting briefing for a proposal
    Returns everything Bill needs to know before a meeting
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Get proposal details
            cursor.execute("""
                SELECT
                    proposal_id, project_code, project_name, client_company,
                    status, project_phase, win_probability, health_score, contact_person,
                    last_contact_date, days_since_contact, next_action
                FROM projects
                WHERE project_code = ?
            """, (project_code,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Proposal not found")

            proposal_id = row[0]

            # Get health status
            health_score = row[7]
            health_status = "healthy" if health_score and health_score >= 70 else \
                           "at_risk" if health_score and health_score >= 50 else \
                           "critical" if health_score else "unknown"

            # Get recent emails (join through email_proposal_links)
            cursor.execute("""
                SELECT e.subject, e.sender_email, e.date, ec.category, ec.ai_summary
                FROM email_proposal_links epl
                JOIN emails e ON epl.email_id = e.email_id
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE epl.proposal_id = ?
                ORDER BY e.date DESC
                LIMIT 5
            """, (proposal_id,))
            recent_emails = [
                {
                    "date": email[2],
                    "subject": email[0],
                    "sender": email[1],
                    "category": email[3] or "general",
                    "snippet": email[4][:100] if email[4] else "No summary available"
                }
                for email in cursor.fetchall()
            ]

            # Get milestones
            milestones = milestone_service.get_milestones_by_proposal(proposal_id)
            upcoming_milestones = [
                {
                    "milestone_name": m["milestone_name"],
                    "expected_date": m["expected_date"],
                    "status": m["status"],
                    "responsible_party": m.get("responsible_party", "bensley")
                }
                for m in milestones[:5]
            ]

            # Get RFIs
            rfis = rfi_service.get_rfis_by_proposal(proposal_id)
            open_rfis = [
                {
                    "rfi_number": rfi["rfi_number"],
                    "question": rfi["question"],
                    "status": rfi["status"],
                    "priority": rfi.get("priority", "normal"),
                    "asked_date": rfi["asked_date"]
                }
                for rfi in rfis if rfi["status"] != "answered"
            ]

            # Get financials
            financials = financial_service.get_financials_by_proposal(proposal_id)
            total_value = sum(f.get("amount", 0) for f in financials)
            paid = sum(f.get("amount", 0) for f in financials if f.get("status") == "paid")
            outstanding = total_value - paid

            # Get documents count by type (join through email_proposal_links and emails)
            # Note: Using email_attachments table, not attachments
            cursor.execute("""
                SELECT COUNT(DISTINCT ea.attachment_id) as total
                FROM email_proposal_links epl
                JOIN emails e ON epl.email_id = e.email_id
                JOIN email_attachments ea ON e.email_id = ea.email_id
                WHERE epl.proposal_id = ?
            """, (proposal_id,))
            doc_count = cursor.fetchone()[0] or 0

            # Get document breakdown by type
            cursor.execute("""
                SELECT ea.document_type, COUNT(DISTINCT ea.attachment_id) as count
                FROM email_proposal_links epl
                JOIN emails e ON epl.email_id = e.email_id
                JOIN email_attachments ea ON e.email_id = ea.email_id
                WHERE epl.proposal_id = ?
                GROUP BY ea.document_type
            """, (proposal_id,))

            doc_by_type = {
                "contracts": 0,
                "presentations": 0,
                "drawings": 0,
                "renderings": 0,
                "correspondence": 0,
                "design_document": 0,
                "other": 0
            }
            for row in cursor.fetchall():
                doc_type = row[0] or "other"
                count = row[1]
                if doc_type in doc_by_type:
                    doc_by_type[doc_type] = count
                else:
                    doc_by_type["other"] += count

            return {
                "client": {
                    "name": row[3] or "Unknown client",
                    "contact": "Contact TBD",
                    "email": "contact@client.com",
                    "last_contact_date": row[9],
                    "days_since_contact": row[10] or 0,
                    "next_action": row[11] or "No action specified"
                },
                "project": {
                    "code": row[1],
                    "name": row[2],
                    "phase": row[5] or "Unknown",
                    "status": row[4],
                    "win_probability": row[6] or 0,
                    "health_score": health_score or 0,
                    "health_status": health_status,
                    "pm": row[8] or "Unassigned"
                },
                "submissions": [],  # Empty - file tracking not implemented yet
                "financials": {
                    "total_contract_value": total_value,
                    "currency": "USD",
                    "initial_payment_received": paid,
                    "outstanding_balance": outstanding,
                    "next_payment": None,  # TODO: Implement payment schedule
                    "overdue_amount": 0
                },
                "milestones": upcoming_milestones,
                "open_issues": {
                    "rfis": open_rfis,
                    "blockers": [],  # TODO: Implement blockers tracking
                    "internal_tasks": []  # TODO: Implement task tracking
                },
                "recent_emails": recent_emails,
                "documents_breakdown": {
                    "total": doc_count,
                    "by_type": doc_by_type
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get briefing: {str(e)}")

@app.get("/api/dashboard/decision-tiles")
async def get_decision_tiles():
    """
    Enhanced decision tiles with operational counts
    Shows what needs Bill's attention TODAY
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Proposals needing outreach (14+ days no contact)
            cursor.execute("""
                SELECT project_code, project_name, contact_person, days_since_contact, next_action
                FROM projects
                WHERE days_since_contact >= 14
                AND is_active_project = 0 AND status = 'proposal'
                ORDER BY days_since_contact DESC
                LIMIT 10
            """)
            needs_outreach = [
                {
                    "project_code": row[0],
                    "project_name": row[1],
                    "pm": row[2],
                    "days_since_contact": row[3],
                    "next_action": row[4]
                }
                for row in cursor.fetchall()
            ]

            # Count overdue milestones
            cursor.execute("""
                SELECT COUNT(*) FROM project_milestones
                WHERE planned_date < date('now')
                AND status != 'completed'
            """)
            overdue_milestones_count = cursor.fetchone()[0] or 0

            # Get overdue milestone details
            cursor.execute("""
                SELECT
                    m.milestone_name, m.planned_date, m.project_code
                FROM project_milestones m
                WHERE m.planned_date < date('now')
                AND m.status != 'completed'
                ORDER BY m.planned_date ASC
                LIMIT 10
            """)
            overdue_milestones = [
                {
                    "milestone_name": row[0],
                    "expected_date": row[1],
                    "delay_days": (datetime.now().date() - datetime.strptime(row[1], '%Y-%m-%d').date()).days if row[1] else 0,
                    "project_code": row[2],
                    "project_name": row[2]  # Use code as fallback for name
                }
                for row in cursor.fetchall()
            ]

            # Count unanswered RFIs
            cursor.execute("""
                SELECT COUNT(*) FROM project_rfis
                WHERE status = 'unanswered'
            """)
            unanswered_rfis_count = cursor.fetchone()[0] or 0

            # Get unanswered RFI details
            cursor.execute("""
                SELECT
                    r.rfi_number, r.question, r.asked_date,
                    p.project_code, p.project_name
                FROM project_rfis r
                JOIN projects p ON r.proposal_id = p.proposal_id
                WHERE r.status = 'unanswered'
                ORDER BY r.asked_date ASC
                LIMIT 10
            """)
            unanswered_rfis = [
                {
                    "rfi_number": row[0],
                    "question": row[1],
                    "asked_date": row[2],
                    "project_code": row[3],
                    "project_name": row[4]
                }
                for row in cursor.fetchall()
            ]

            # Count upcoming meetings (next 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM project_meetings
                WHERE scheduled_date BETWEEN date('now') AND date('now', '+7 days')
            """)
            upcoming_meetings_count = cursor.fetchone()[0] or 0

            # Get upcoming meeting details
            cursor.execute("""
                SELECT
                    m.meeting_title, m.scheduled_date, m.meeting_type,
                    p.project_code, p.project_name
                FROM project_meetings m
                JOIN projects p ON m.proposal_id = p.proposal_id
                WHERE m.scheduled_date BETWEEN date('now') AND date('now', '+7 days')
                ORDER BY m.scheduled_date ASC
                LIMIT 10
            """)
            upcoming_meetings = [
                {
                    "meeting_title": row[0],
                    "scheduled_date": row[1],
                    "meeting_type": row[2],
                    "project_code": row[3],
                    "project_name": row[4]
                }
                for row in cursor.fetchall()
            ]

            # Count invoices awaiting payment
            cursor.execute("""
                SELECT COUNT(*), SUM(amount)
                FROM project_financials
                WHERE status = 'pending'
                AND payment_type = 'invoice'
            """)
            invoice_row = cursor.fetchone()
            invoices_count = invoice_row[0] or 0
            invoices_amount = invoice_row[1] or 0

            return {
                "proposals_needing_outreach": {
                    "count": len(needs_outreach),
                    "description": "Proposals with no contact in 14+ days",
                    "items": needs_outreach
                },
                "needs_outreach": {
                    "count": len(needs_outreach),
                    "description": "Proposals with no contact in 14+ days",
                    "items": needs_outreach
                },
                "unanswered_rfis": {
                    "count": unanswered_rfis_count,
                    "description": "RFIs awaiting response",
                    "items": unanswered_rfis
                },
                "overdue_milestones": {
                    "count": overdue_milestones_count,
                    "description": "Milestones past expected date",
                    "items": overdue_milestones
                },
                "upcoming_meetings": {
                    "count": upcoming_meetings_count,
                    "description": "Meetings scheduled in next 7 days",
                    "items": upcoming_meetings
                },
                "invoices_awaiting_payment": {
                    "count": invoices_count,
                    "total_amount": invoices_amount,
                    "description": "Outstanding invoices",
                    "items": []
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get decision tiles: {str(e)}")

@app.get("/api/admin/system-health")
async def get_system_health():
    """
    System health metrics for internal monitoring
    NOT for Bill - this is for Lukas/team
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Email processing stats
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

            # Proposal stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active_project = 1 THEN 1 ELSE 0 END) as active
                FROM projects
                WHERE status = 'proposal'
            """)
            proposal_stats = cursor.fetchone()

            # Document stats
            cursor.execute("SELECT COUNT(*) FROM attachments")
            doc_count = cursor.fetchone()[0] or 0

            return {
                "email_processing": {
                    "total_emails": total_emails,
                    "processed": processed,
                    "unprocessed": unprocessed,
                    "categorized_percent": round((processed / total_emails * 100), 1) if total_emails > 0 else 0,
                    "processing_rate": "~50/hour"  # Placeholder
                },
                "model_training": {
                    "training_samples": processed,
                    "target_samples": 5000,
                    "completion_percent": min(100, round((processed / 5000 * 100), 1)),
                    "model_accuracy": 0.87  # Placeholder
                },
                "database": {
                    "total_proposals": proposal_stats[0] or 0,
                    "active_projects": proposal_stats[1] or 0,
                    "total_documents": doc_count,
                    "last_sync": "2025-01-14T10:30:00Z"  # Placeholder
                },
                "api_health": {
                    "uptime_seconds": 86400,  # Placeholder
                    "requests_last_hour": 342,  # Placeholder
                    "avg_response_time_ms": 45  # Placeholder
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")

# ============================================================================
# MANUAL OVERRIDES ENDPOINTS
# ============================================================================

class ManualOverrideCreate(BaseModel):
    """Request model for creating a manual override"""
    proposal_id: Optional[int] = None
    project_code: Optional[str] = None
    scope: str  # emails, documents, billing, rfis, scheduling, general
    instruction: str
    author: str = "bill"
    source: str = "dashboard_context_modal"
    urgency: str = "informational"  # informational, urgent
    tags: Optional[List[str]] = None

class ManualOverrideUpdate(BaseModel):
    """Request model for updating a manual override"""
    status: Optional[str] = None  # active, applied, archived
    applied_by: Optional[str] = None
    applied_at: Optional[str] = None
    instruction: Optional[str] = None
    urgency: Optional[str] = None
    scope: Optional[str] = None
    tags: Optional[List[str]] = None

class TrainingVerification(BaseModel):
    """Request model for verifying training data"""
    is_correct: bool
    feedback: Optional[str] = None
    corrected_output: Optional[str] = None

class BulkVerification(BaseModel):
    """Request model for bulk verification"""
    training_ids: List[int]
    is_correct: bool
    feedback: Optional[str] = None

# ============================================================================
# API ENDPOINTS - MANUAL OVERRIDES
# ============================================================================

@app.post("/api/manual-overrides")
async def create_manual_override(override: ManualOverrideCreate):
    """
    Create a new manual override
    Tracks Bill's manual instructions for proposals
    """
    try:
        override_id = override_service.create_override(override.dict())

        # Get the created override to return it
        created = override_service.get_override_by_id(override_id)

        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create override: {str(e)}")

@app.get("/api/manual-overrides")
async def get_manual_overrides(
    project_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get filtered list of manual overrides with pagination

    Filters:
    - project_code: Filter by project
    - status: active, applied, archived
    - scope: emails, documents, billing, rfis, scheduling, general
    - author: bill, lukas, etc.
    """
    try:
        result = override_service.get_overrides(
            project_code=project_code,
            status=status,
            scope=scope,
            author=author,
            page=page,
            per_page=per_page
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overrides: {str(e)}")

@app.get("/api/manual-overrides/{override_id}")
async def get_manual_override_by_id(override_id: int):
    """Get a specific manual override by ID"""
    try:
        override = override_service.get_override_by_id(override_id)
        if not override:
            raise HTTPException(status_code=404, detail="Override not found")
        return override
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get override: {str(e)}")

@app.patch("/api/manual-overrides/{override_id}")
async def update_manual_override(override_id: int, update: ManualOverrideUpdate):
    """
    Update a manual override
    Use this to mark overrides as applied or archived
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in update.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        success = override_service.update_override(override_id, update_data)

        if not success:
            raise HTTPException(status_code=404, detail="Override not found")

        # Return updated override
        updated = override_service.get_override_by_id(override_id)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update override: {str(e)}")

@app.post("/api/manual-overrides/{override_id}/apply")
async def apply_manual_override(override_id: int, applied_by: str = "system"):
    """
    Mark an override as applied
    Convenience endpoint for marking overrides as completed
    """
    try:
        success = override_service.mark_as_applied(override_id, applied_by)

        if not success:
            raise HTTPException(status_code=404, detail="Override not found")

        updated = override_service.get_override_by_id(override_id)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply override: {str(e)}")

# ============================================================================
# API ENDPOINTS - TRAINING DATA VERIFICATION
# ============================================================================

@app.get("/api/training/unverified")
async def get_unverified_training(
    task_type: Optional[str] = Query(None, description="Filter by task type: classify, extract, summarize"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    max_confidence: Optional[float] = Query(None, ge=0, le=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get unverified AI training data for human review

    Returns AI decisions (email categorization, entity extraction, etc.)
    that need Bill's approval or correction.
    """
    try:
        result = training_service.get_unverified_training(
            task_type=task_type,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            page=page,
            per_page=per_page
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch training data: {str(e)}")

@app.get("/api/training/{training_id}")
async def get_training_by_id(training_id: int):
    """Get a specific training record by ID"""
    try:
        training = training_service.get_training_by_id(training_id)

        if not training:
            raise HTTPException(status_code=404, detail="Training record not found")

        return training
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch training record: {str(e)}")

@app.post("/api/training/{training_id}/verify")
async def verify_training(training_id: int, verification: TrainingVerification):
    """
    Verify a training record as correct or incorrect

    This creates a feedback loop where Bill can:
    - Approve AI decisions (is_correct=true)
    - Correct mistakes (is_correct=false + corrected_output)
    - Provide feedback for learning
    """
    try:
        success = training_service.verify_training(
            training_id=training_id,
            is_correct=verification.is_correct,
            feedback=verification.feedback,
            corrected_output=verification.corrected_output
        )

        if not success:
            raise HTTPException(status_code=404, detail="Training record not found")

        updated = training_service.get_training_by_id(training_id)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify training: {str(e)}")

@app.post("/api/training/verify/bulk")
async def bulk_verify_training(bulk: BulkVerification):
    """
    Bulk verify multiple training records at once

    Useful for approving multiple similar AI decisions quickly:
    - Approve 20 correctly categorized emails at once
    - Mark multiple extractions as correct
    """
    try:
        count = training_service.bulk_verify(
            training_ids=bulk.training_ids,
            is_correct=bulk.is_correct,
            feedback=bulk.feedback
        )

        return {
            "verified_count": count,
            "training_ids": bulk.training_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk verify: {str(e)}")

@app.get("/api/training/stats")
async def get_training_stats():
    """
    Get verification statistics

    Shows:
    - Overall verification progress (6,409 unverified)
    - Stats by task type (classify, extract, summarize)
    - Stats by confidence level (high, medium, low)
    """
    try:
        stats = training_service.get_verification_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")

@app.get("/api/training/incorrect")
async def get_incorrect_predictions(
    task_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get training records that were marked as incorrect

    Useful for:
    - Understanding common AI mistakes
    - Finding patterns in errors
    - Improving prompts based on failures
    """
    try:
        result = training_service.get_incorrect_predictions(
            task_type=task_type,
            page=page,
            per_page=per_page
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch incorrect predictions: {str(e)}")

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))

    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║   Bensley Intelligence Platform API v2.0                 ║
    ╚══════════════════════════════════════════════════════════╝

    🚀 Starting server...
    📡 API:  http://localhost:{port}
    📚 Docs: http://localhost:{port}/docs
    🔍 Health: http://localhost:{port}/health
    📊 Dashboard: http://localhost:{port}/api/dashboard/stats

    Press Ctrl+C to stop
    """)

    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
# ============================================================================
# PHASE 2 ENDPOINTS - Email Intelligence & Bulk Operations
# ============================================================================

@app.get("/api/proposals/by-code/{project_code}/emails/timeline")
async def get_proposal_emails_timeline(project_code: str):
    """
    Get chronological email timeline for a proposal

    Returns list of emails with date, subject, sender, category, snippet, attachments_count
    """
    try:
        # Get proposal by code
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Find proposal
            cursor.execute("""
                SELECT proposal_id, project_code, project_name
                FROM projects
                WHERE project_code = ?
            """, (project_code,))

            proposal_row = cursor.fetchone()
            if not proposal_row:
                raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

            proposal_id, code, name = proposal_row

            # Get emails timeline
            cursor.execute("""
                SELECT
                    e.email_id,
                    e.date,
                    e.subject,
                    e.sender_email,
                    ec.category,
                    e.body_preview as snippet,
                    (SELECT COUNT(*) FROM email_attachments ea WHERE ea.email_id = e.email_id) as attachments_count
                FROM emails e
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE epl.proposal_id = ?
                ORDER BY e.date DESC
            """, (proposal_id,))

            emails = []
            for row in cursor.fetchall():
                emails.append({
                    "email_id": row[0],
                    "date": row[1],
                    "subject": row[2] or "",
                    "sender": row[3] or "",
                    "category": row[4] or "general",
                    "snippet": row[5] or "",
                    "attachments_count": row[6] or 0
                })

            return {
                "proposal": {
                    "project_code": code,
                    "project_name": name
                },
                "emails": emails
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email timeline: {str(e)}")


@app.get("/api/proposals/by-code/{project_code}/emails/summary")
async def get_proposal_emails_summary(project_code: str):
    """
    Get AI-generated summary of all emails for a proposal

    Returns aggregated summary, key points, and last contact date
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Find proposal
            cursor.execute("""
                SELECT proposal_id, project_code
                FROM projects
                WHERE project_code = ?
            """, (project_code,))

            proposal_row = cursor.fetchone()
            if not proposal_row:
                raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

            proposal_id, code = proposal_row

            # Get email summaries and extract key points
            cursor.execute("""
                SELECT
                    ec.ai_summary,
                    e.date,
                    e.subject
                FROM email_content ec
                JOIN emails e ON ec.email_id = e.email_id
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                WHERE epl.proposal_id = ?
                ORDER BY e.date DESC
                LIMIT 10
            """, (proposal_id,))

            summaries = cursor.fetchall()

            if not summaries:
                return {
                    "proposal": {"project_code": code},
                    "summary": "No emails found for this proposal.",
                    "key_points": [],
                    "last_contact": None
                }

            # Aggregate summaries
            key_points = []
            for summary, date, subject in summaries:
                if summary:
                    # Extract first sentence as key point
                    first_sentence = summary.split('.')[0].strip()
                    if first_sentence and len(first_sentence) > 10:
                        key_points.append(first_sentence)

            # Create overall summary
            summary_text = f"Found {len(summaries)} recent emails. "
            if key_points:
                summary_text += f"Key topics discussed: {', '.join(key_points[:3])}."

            return {
                "proposal": {"project_code": code},
                "summary": summary_text,
                "key_points": key_points[:5],
                "last_contact": summaries[0][1] if summaries else None
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email summary: {str(e)}")


@app.get("/api/proposals/by-code/{project_code}/contacts")
async def get_proposal_contacts(project_code: str):
    """
    Get extracted contacts from proposal emails

    Returns list of contacts with name, email, role, last_contact_date, importance
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Find proposal
            cursor.execute("""
                SELECT proposal_id, project_code
                FROM projects
                WHERE project_code = ?
            """, (project_code,))

            proposal_row = cursor.fetchone()
            if not proposal_row:
                raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

            proposal_id, code = proposal_row

            # Extract contacts from emails
            cursor.execute("""
                SELECT DISTINCT
                    e.sender_email,
                    e.sender_name,
                    MAX(e.date) as last_contact_date,
                    COUNT(*) as email_count
                FROM emails e
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                WHERE epl.proposal_id = ?
                  AND e.sender_email IS NOT NULL
                  AND e.sender_email != ''
                GROUP BY e.sender_email, e.sender_name
                ORDER BY email_count DESC, last_contact_date DESC
            """, (proposal_id,))

            contacts = []
            for row in cursor.fetchall():
                sender_email, sender_name, last_date, email_count = row

                # Determine importance based on email count
                if email_count > 5:
                    importance = "primary"
                elif email_count > 2:
                    importance = "regular"
                else:
                    importance = "occasional"

                # Extract name from email if sender_name is empty
                name = sender_name or sender_email.split('@')[0].replace('.', ' ').title()

                contacts.append({
                    "name": name,
                    "email": sender_email,
                    "role": "Contact",  # Could be enhanced with role detection
                    "last_contact_date": last_date,
                    "importance": importance
                })

            return {
                "proposal": {"project_code": code},
                "contacts": contacts
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contacts: {str(e)}")


@app.get("/api/proposals/by-code/{project_code}/attachments")
async def get_proposal_attachments(project_code: str):
    """
    Get email attachments for a proposal

    Returns list of attachments with file_name, document_type, uploaded_at, source_email_id
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Find proposal
            cursor.execute("""
                SELECT proposal_id, project_code
                FROM projects
                WHERE project_code = ?
            """, (project_code,))

            proposal_row = cursor.fetchone()
            if not proposal_row:
                raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

            proposal_id, code = proposal_row

            # Get attachments from linked emails
            cursor.execute("""
                SELECT DISTINCT
                    ea.attachment_id,
                    ea.filename as file_name,
                    ea.mime_type,
                    ea.created_at as uploaded_at,
                    ea.email_id as source_email_id,
                    ea.filepath
                FROM email_attachments ea
                JOIN email_proposal_links epl ON ea.email_id = epl.email_id
                WHERE epl.proposal_id = ?
                ORDER BY ea.created_at DESC
            """, (proposal_id,))

            attachments = []
            for row in cursor.fetchall():
                attachment_id, file_name, mime_type, uploaded_at, source_email_id, filepath = row

                # Guess document type from filename/mimetype
                file_name_lower = (file_name or "").lower()
                if "contract" in file_name_lower:
                    doc_type = "contract"
                elif "sow" in file_name_lower or "scope" in file_name_lower:
                    doc_type = "sow"
                elif "invoice" in file_name_lower:
                    doc_type = "invoice"
                elif "design" in file_name_lower or "render" in file_name_lower:
                    doc_type = "design"
                elif mime_type and "pdf" in mime_type:
                    doc_type = "document"
                elif mime_type and "image" in mime_type:
                    doc_type = "image"
                else:
                    doc_type = "other"

                attachments.append({
                    "attachment_id": attachment_id,
                    "file_name": file_name,
                    "document_type": doc_type,
                    "uploaded_at": uploaded_at,
                    "source_email_id": source_email_id
                })

            return {
                "proposal": {"project_code": code},
                "attachments": attachments
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get attachments: {str(e)}")


@app.patch("/api/proposals/bulk")
async def bulk_update_proposals(updates: Dict[str, Any]):
    """
    Bulk update multiple proposals

    Request body:
    {
        "project_codes": ["24 BK-029", "25 BK-033"],
        "updates": {
            "status": "active",
            "pm": "Bill Bensley",
            "next_action": "Follow up",
            "tags": ["urgent"]
        }
    }
    """
    try:
        project_codes = updates.get("project_codes", [])
        update_fields = updates.get("updates", {})

        if not project_codes or not update_fields:
            raise HTTPException(status_code=400, detail="project_codes and updates are required")

        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Build UPDATE query dynamically
            set_clauses = []
            params = []

            if "status" in update_fields:
                set_clauses.append("status = ?")
                params.append(update_fields["status"])

            if "pm" in update_fields:
                set_clauses.append("pm = ?")
                params.append(update_fields["pm"])

            if "next_action" in update_fields:
                set_clauses.append("next_action = ?")
                params.append(update_fields["next_action"])

            if not set_clauses:
                raise HTTPException(status_code=400, detail="No valid update fields provided")

            set_clauses.append("updated_at = datetime('now')")

            # Add WHERE clause
            placeholders = ','.join(['?' for _ in project_codes])
            params.extend(project_codes)

            sql = f"""
                UPDATE projects
                SET {', '.join(set_clauses)}
                WHERE project_code IN ({placeholders})
            """

            cursor.execute(sql, params)
            conn.commit()

            updated_count = cursor.rowcount

            # Return updated proposals
            cursor.execute(f"""
                SELECT proposal_id, project_code, project_name, status, pm, next_action, updated_at
                FROM projects
                WHERE project_code IN ({placeholders})
            """, project_codes)

            updated_proposals = []
            for row in cursor.fetchall():
                updated_proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_name": row[2],
                    "status": row[3],
                    "pm": row[4],
                    "next_action": row[5],
                    "updated_at": row[6]
                })

            return {
                "updated": updated_count,
                "proposals": updated_proposals
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk update proposals: {str(e)}")


@app.post("/api/emails/bulk-category")
async def bulk_categorize_emails(updates: Dict[str, Any]):
    """
    Bulk update email categories

    Request body:
    {
        "email_ids": [123, 456, 789],
        "category": "proposal",
        "subcategory": "design"
    }
    """
    try:
        email_ids = updates.get("email_ids", [])
        category = updates.get("category")
        subcategory = updates.get("subcategory")

        if not email_ids or not category:
            raise HTTPException(status_code=400, detail="email_ids and category are required")

        with email_service.get_connection() as conn:
            cursor = conn.cursor()

            # Update email_content table
            placeholders = ','.join(['?' for _ in email_ids])

            if subcategory:
                cursor.execute(f"""
                    UPDATE email_content
                    SET category = ?,
                        subcategory = ?
                    WHERE email_id IN ({placeholders})
                """, [category, subcategory] + email_ids)
            else:
                cursor.execute(f"""
                    UPDATE email_content
                    SET category = ?
                    WHERE email_id IN ({placeholders})
                """, [category] + email_ids)

            conn.commit()
            updated_count = cursor.rowcount

            # Return updated emails
            cursor.execute(f"""
                SELECT e.email_id, e.subject, ec.category, ec.subcategory
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE e.email_id IN ({placeholders})
            """, email_ids)

            updated_emails = []
            for row in cursor.fetchall():
                updated_emails.append({
                    "email_id": row[0],
                    "subject": row[1],
                    "category": row[2],
                    "subcategory": row[3]
                })

            return {
                "updated": updated_count,
                "emails": updated_emails
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk categorize emails: {str(e)}")

# ============================================================================
# INTELLIGENCE / AI SUGGESTIONS ENDPOINTS
# ============================================================================

from services.intelligence_service import IntelligenceService

@app.get("/api/intel/suggestions")
async def get_suggestions(
    status: str = Query("pending", description="Filter by status"),
    group: Optional[str] = Query(None, description="Filter by bucket: urgent, needs_attention, fyi"),
    limit: int = Query(100, description="Max results")
):
    """Get AI-generated suggestions filtered by status and priority bucket"""
    try:
        service = IntelligenceService()
        return service.get_suggestions(status=status, bucket=group, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


class DecisionRequest(BaseModel):
    decision: str = Field(..., description="approved, rejected, or snoozed")
    reason: Optional[str] = Field(None, description="Reason for reject/snooze")
    apply_now: bool = Field(True, description="Apply changes immediately")
    dry_run: bool = Field(False, description="Preview without applying")
    batch_ids: Optional[List[str]] = Field(None, description="Additional suggestion IDs to process")


@app.post("/api/intel/suggestions/{suggestion_id}/decision")
async def apply_decision(suggestion_id: str, request: DecisionRequest):
    """Apply a decision (approve/reject/snooze) to a suggestion"""
    try:
        service = IntelligenceService()
        return service.apply_decision(
            suggestion_id=suggestion_id,
            decision=request.decision,
            reason=request.reason,
            apply_now=request.apply_now,
            dry_run=request.dry_run,
            batch_ids=request.batch_ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply decision: {str(e)}")


@app.get("/api/intel/patterns")
async def get_patterns():
    """Get all detected patterns with statistics and samples"""
    try:
        service = IntelligenceService()
        return service.get_patterns()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")


@app.get("/api/intel/decisions")
async def get_decisions(limit: int = Query(50, description="Max decisions to return")):
    """Get recent decisions for audit trail"""
    try:
        service = IntelligenceService()
        return service.get_decisions(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get decisions: {str(e)}")


@app.get("/api/intel/training-data")
async def export_training_data(
    format: str = Query("ndjson", description="Export format"),
    limit: int = Query(1000, description="Max records")
):
    """Export training data for LLM fine-tuning"""
    try:
        service = IntelligenceService()
        data = service.export_training_data(format=format, limit=limit)

        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=data, media_type="application/x-ndjson")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export training data: {str(e)}")


# ================================
# Comprehensive Audit System API Endpoints (Phase 2)
# ================================

from backend.services.comprehensive_auditor import ComprehensiveAuditor
from backend.services.learning_service import LearningService
import sqlite3
import json

# Database connection helper for comprehensive audit endpoints
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

def get_db_connection():
    """Get database connection for comprehensive audit endpoints"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -------- Project Scope Endpoints --------

class ScopeRequest(BaseModel):
    disciplines: List[str]  # ['landscape', 'interiors', 'architecture']
    fee_breakdown: Optional[Dict[str, float]] = None  # {'landscape': 2000000, 'interiors': 1250000}
    scope_description: Optional[str] = None
    confirmed_by_user: bool = True


@app.get("/api/projects/{project_code}/scope")
async def get_project_scope(project_code: str):
    """Get project scope (disciplines and fee breakdown)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_scope WHERE project_code = ?
        """, (project_code,))

        scopes = []
        for row in cursor.fetchall():
            scopes.append({
                'scope_id': row['scope_id'],
                'discipline': row['discipline'],
                'fee_usd': row['fee_usd'],
                'percentage_of_total': row['percentage_of_total'],
                'scope_description': row['scope_description'],
                'confirmed_by_user': bool(row['confirmed_by_user']),
                'confidence': row['confidence'],
                'created_at': row['created_at']
            })

        conn.close()
        return {'project_code': project_code, 'scopes': scopes}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scope: {str(e)}")


@app.post("/api/projects/{project_code}/scope")
async def set_project_scope(project_code: str, request: ScopeRequest):
    """Add or update project scope"""
    try:
        import uuid
        from datetime import datetime

        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete existing scopes
        cursor.execute("DELETE FROM project_scope WHERE project_code = ?", (project_code,))

        # Get total fee for percentage calculation
        cursor.execute("""
            SELECT total_fee_usd FROM projects WHERE project_code = ?
        """, (project_code,))
        project = cursor.fetchone()
        total_fee = project['total_fee_usd'] if project else 0

        # Add new scopes
        for discipline in request.disciplines:
            scope_id = str(uuid.uuid4())
            fee_usd = request.fee_breakdown.get(discipline) if request.fee_breakdown else None
            percentage = (fee_usd / total_fee * 100) if (fee_usd and total_fee) else None

            cursor.execute("""
                INSERT INTO project_scope
                (scope_id, project_code, discipline, fee_usd, percentage_of_total,
                 scope_description, confirmed_by_user, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scope_id, project_code, discipline, fee_usd, percentage,
                request.scope_description, 1 if request.confirmed_by_user else 0,
                0.95, datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

        return {"success": True, "project_code": project_code, "disciplines": request.disciplines}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set scope: {str(e)}")


# -------- Fee Breakdown Endpoints --------

class FeeBreakdownRequest(BaseModel):
    phases: Dict[str, float]  # {'mobilization': 650000, 'concept': 580000, ...}
    confirmed_by_user: bool = True


@app.get("/api/projects/{project_code}/fee-breakdown")
async def get_fee_breakdown(project_code: str):
    """Get project fee breakdown by phase"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_fee_breakdown WHERE project_code = ?
            ORDER BY CASE phase
                WHEN 'mobilization' THEN 1
                WHEN 'concept' THEN 2
                WHEN 'schematic' THEN 3
                WHEN 'dd' THEN 4
                WHEN 'cd' THEN 5
                WHEN 'ca' THEN 6
                ELSE 7
            END
        """, (project_code,))

        breakdown = []
        for row in cursor.fetchall():
            breakdown.append({
                'breakdown_id': row['breakdown_id'],
                'phase': row['phase'],
                'phase_fee_usd': row['phase_fee_usd'],
                'percentage_of_total': row['percentage_of_total'],
                'payment_status': row['payment_status'],
                'confirmed_by_user': bool(row['confirmed_by_user']),
                'created_at': row['created_at']
            })

        conn.close()
        return {'project_code': project_code, 'breakdown': breakdown}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fee breakdown: {str(e)}")


@app.post("/api/projects/{project_code}/fee-breakdown")
async def set_fee_breakdown(project_code: str, request: FeeBreakdownRequest):
    """Set project fee breakdown by phase"""
    try:
        import uuid
        from datetime import datetime

        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete existing breakdown
        cursor.execute("DELETE FROM project_fee_breakdown WHERE project_code = ?", (project_code,))

        # Get total fee
        cursor.execute("""
            SELECT total_fee_usd FROM projects WHERE project_code = ?
        """, (project_code,))
        project = cursor.fetchone()
        total_fee = project['total_fee_usd'] if project else sum(request.phases.values())

        # Add new breakdown
        for phase, fee in request.phases.items():
            breakdown_id = str(uuid.uuid4())
            percentage = (fee / total_fee * 100) if total_fee else 0

            cursor.execute("""
                INSERT INTO project_fee_breakdown
                (breakdown_id, project_code, phase, phase_fee_usd, percentage_of_total,
                 payment_status, confirmed_by_user, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                breakdown_id, project_code, phase, fee, percentage,
                'pending', 1 if request.confirmed_by_user else 0,
                0.95, datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

        return {"success": True, "project_code": project_code, "phases": list(request.phases.keys())}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set fee breakdown: {str(e)}")


# -------- Timeline Endpoints --------

class TimelinePhase(BaseModel):
    phase: str
    expected_duration_months: float
    start_date: Optional[str] = None
    expected_end_date: Optional[str] = None
    presentation_date: Optional[str] = None
    status: str = 'not_started'


class TimelineRequest(BaseModel):
    phases: List[TimelinePhase]
    confirmed_by_user: bool = True


@app.get("/api/projects/{project_code}/timeline")
async def get_project_timeline(project_code: str):
    """Get project phase timeline"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_phase_timeline WHERE project_code = ?
            ORDER BY CASE phase
                WHEN 'mobilization' THEN 1
                WHEN 'concept' THEN 2
                WHEN 'schematic' THEN 3
                WHEN 'dd' THEN 4
                WHEN 'cd' THEN 5
                WHEN 'ca' THEN 6
                ELSE 7
            END
        """, (project_code,))

        timeline = []
        for row in cursor.fetchall():
            timeline.append({
                'timeline_id': row['timeline_id'],
                'phase': row['phase'],
                'expected_duration_months': row['expected_duration_months'],
                'start_date': row['start_date'],
                'expected_end_date': row['expected_end_date'],
                'actual_end_date': row['actual_end_date'],
                'presentation_date': row['presentation_date'],
                'status': row['status'],
                'delay_days': row['delay_days'],
                'notes': row['notes'],
                'confirmed_by_user': bool(row['confirmed_by_user'])
            })

        conn.close()
        return {'project_code': project_code, 'timeline': timeline}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@app.post("/api/projects/{project_code}/timeline")
async def set_project_timeline(project_code: str, request: TimelineRequest):
    """Set project phase timeline"""
    try:
        import uuid
        from datetime import datetime

        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete existing timeline
        cursor.execute("DELETE FROM project_phase_timeline WHERE project_code = ?", (project_code,))

        # Add new timeline
        for phase_data in request.phases:
            timeline_id = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO project_phase_timeline
                (timeline_id, project_code, phase, expected_duration_months,
                 start_date, expected_end_date, presentation_date, status,
                 confirmed_by_user, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timeline_id, project_code, phase_data.phase,
                phase_data.expected_duration_months,
                phase_data.start_date, phase_data.expected_end_date,
                phase_data.presentation_date, phase_data.status,
                1 if request.confirmed_by_user else 0,
                0.95, datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

        return {"success": True, "project_code": project_code, "phases": len(request.phases)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set timeline: {str(e)}")


# -------- Contract Terms Endpoints --------

class ContractRequest(BaseModel):
    contract_signed_date: Optional[str] = None
    contract_start_date: Optional[str] = None
    total_contract_term_months: Optional[int] = None
    contract_end_date: Optional[str] = None
    total_fee_usd: Optional[float] = None
    contract_type: Optional[str] = 'fixed_fee'
    payment_schedule: Optional[Dict] = None
    confirmed_by_user: bool = True


@app.get("/api/projects/{project_code}/contract")
async def get_contract_terms(project_code: str):
    """Get contract terms for a project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM contract_terms WHERE project_code = ?
        """, (project_code,))

        contract = cursor.fetchone()
        conn.close()

        if not contract:
            return {'project_code': project_code, 'contract': None}

        return {
            'project_code': project_code,
            'contract': {
                'contract_id': contract['contract_id'],
                'contract_signed_date': contract['contract_signed_date'],
                'contract_start_date': contract['contract_start_date'],
                'total_contract_term_months': contract['total_contract_term_months'],
                'contract_end_date': contract['contract_end_date'],
                'total_fee_usd': contract['total_fee_usd'],
                'contract_type': contract['contract_type'],
                'payment_schedule': json.loads(contract['payment_schedule']) if contract['payment_schedule'] else None,
                'confirmed_by_user': bool(contract['confirmed_by_user']),
                'created_at': contract['created_at']
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contract: {str(e)}")


@app.post("/api/projects/{project_code}/contract")
async def set_contract_terms(project_code: str, request: ContractRequest):
    """Set contract terms for a project"""
    try:
        import uuid
        from datetime import datetime

        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete existing contract
        cursor.execute("DELETE FROM contract_terms WHERE project_code = ?", (project_code,))

        contract_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO contract_terms
            (contract_id, project_code, contract_signed_date, contract_start_date,
             total_contract_term_months, contract_end_date, total_fee_usd,
             contract_type, payment_schedule, confirmed_by_user, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contract_id, project_code, request.contract_signed_date,
            request.contract_start_date, request.total_contract_term_months,
            request.contract_end_date, request.total_fee_usd,
            request.contract_type,
            json.dumps(request.payment_schedule) if request.payment_schedule else None,
            1 if request.confirmed_by_user else 0,
            0.95, datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return {"success": True, "project_code": project_code, "contract_id": contract_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set contract: {str(e)}")


# -------- Learning & Feedback Endpoints --------

class FeedbackRequest(BaseModel):
    question_type: str  # 'scope', 'fee_breakdown', 'timeline', etc.
    ai_suggestion: Dict
    user_correction: Dict
    context_provided: Optional[str] = None
    confidence_before: float


@app.post("/api/audit/feedback/{project_code}")
async def submit_feedback(project_code: str, request: FeedbackRequest):
    """Submit user feedback for continuous learning"""
    try:
        service = LearningService()
        context_id = service.log_user_feedback(
            project_code=project_code,
            question_type=request.question_type,
            ai_suggestion=request.ai_suggestion,
            user_correction=request.user_correction,
            context_provided=request.context_provided,
            confidence_before=request.confidence_before
        )

        return {
            "success": True,
            "context_id": context_id,
            "message": "Feedback logged and patterns extracted"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@app.get("/api/audit/learning-stats")
async def get_learning_stats():
    """Get learning system statistics"""
    try:
        service = LearningService()
        return service.get_learning_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning stats: {str(e)}")


@app.get("/api/audit/auto-apply-candidates")
async def get_auto_apply_candidates():
    """Get rules that are candidates for auto-apply"""
    try:
        service = LearningService()
        return {"candidates": service.suggest_auto_apply_candidates()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get candidates: {str(e)}")


@app.post("/api/audit/enable-auto-apply/{rule_id}")
async def enable_auto_apply(rule_id: str):
    """Enable auto-apply for a specific rule"""
    try:
        service = LearningService()
        success = service.enable_auto_apply_for_rule(rule_id)

        if success:
            return {"success": True, "rule_id": rule_id, "message": "Auto-apply enabled"}
        else:
            raise HTTPException(status_code=404, detail="Rule not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable auto-apply: {str(e)}")


# -------- Re-Audit Endpoints --------

@app.post("/api/audit/re-audit/{project_code}")
async def re_audit_project(project_code: str):
    """Re-audit a specific project"""
    try:
        auditor = ComprehensiveAuditor()

        # Get project
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT project_code, project_name, is_active_project, total_fee_usd, status
            FROM projects WHERE project_code = ?
        """, (project_code,))

        project = cursor.fetchone()
        conn.close()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project_dict = dict(project)

        # Run all audits
        scope_suggestions = auditor.verify_project_scope(project_dict)
        fee_suggestions = auditor.validate_fee_breakdown(project_dict)
        timeline_suggestions = auditor.validate_project_timeline(project_dict)
        invoice_suggestions = auditor.verify_invoice_linking(project_dict)
        contract_suggestions = auditor.verify_contract_terms(project_dict)

        all_suggestions = (scope_suggestions + fee_suggestions + timeline_suggestions +
                          invoice_suggestions + contract_suggestions)

        # Save suggestions
        for suggestion in all_suggestions:
            auditor._save_suggestion(suggestion)

        return {
            "success": True,
            "project_code": project_code,
            "suggestions_generated": len(all_suggestions),
            "breakdown": {
                "scope": len(scope_suggestions),
                "fee": len(fee_suggestions),
                "timeline": len(timeline_suggestions),
                "invoice": len(invoice_suggestions),
                "contract": len(contract_suggestions)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to re-audit project: {str(e)}")


@app.post("/api/audit/re-audit-all")
async def re_audit_all_projects():
    """Re-audit all projects"""
    try:
        auditor = ComprehensiveAuditor()
        results = auditor.audit_all_projects()

        return {
            "success": True,
            "projects_audited": results['stats']['projects_audited'],
            "total_suggestions": results['total_suggestions'],
            "breakdown": {
                "scope": results['stats']['scope_issues'],
                "fee": results['stats']['fee_issues'],
                "timeline": results['stats']['timeline_issues'],
                "invoice": results['stats']['invoice_issues'],
                "contract": results['stats']['contract_issues']
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to re-audit all: {str(e)}")


# ================================
# Financial Dashboard Endpoints
# ================================

@app.get("/api/finance/recent-payments")
async def get_recent_payments(limit: int = Query(5, description="Number of recent payments to return")):
    """Get recently paid invoices for dashboard widget"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent payments with project info
        cursor.execute("""
            SELECT
                i.invoice_id,
                i.invoice_number,
                i.invoice_amount as amount_usd,
                i.payment_date as paid_on,
                i.discipline,
                p.project_code,
                p.project_name
            FROM invoices i
            JOIN projects p ON i.project_id = p.proposal_id
            WHERE i.payment_date IS NOT NULL
              AND i.payment_amount > 0
            ORDER BY i.payment_date DESC
            LIMIT ?
        """, (limit,))

        payments = []
        for row in cursor.fetchall():
            payments.append({
                'invoice_id': row['invoice_id'],
                'invoice_number': row['invoice_number'],
                'project_code': row['project_code'],
                'project_name': row['project_name'],
                'discipline': row['discipline'] or 'General',
                'amount_usd': row['amount_usd'],
                'paid_on': row['paid_on']
            })

        conn.close()

        return {
            'payments': payments,
            'count': len(payments)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent payments: {str(e)}")


@app.get("/api/finance/projected-invoices")
async def get_projected_invoices(limit: int = Query(5, description="Number of upcoming invoices to show")):
    """
    Get upcoming projected invoices based on phase timelines and fee breakdowns

    Returns next N invoicing events across all active projects
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all active projects
        cursor.execute("""
            SELECT
                p.project_code,
                p.project_name,
                p.is_active_project
            FROM projects p
            WHERE p.is_active_project = 1
        """)

        active_projects = cursor.fetchall()
        projected_invoices = []

        for project in active_projects:
            project_code = project['project_code']

            # Get timeline for upcoming phases
            cursor.execute("""
                SELECT
                    phase,
                    presentation_date,
                    expected_end_date,
                    status
                FROM project_phase_timeline
                WHERE project_code = ?
                  AND status IN ('not_started', 'in_progress')
                  AND (presentation_date IS NOT NULL OR expected_end_date IS NOT NULL)
                ORDER BY
                    COALESCE(presentation_date, expected_end_date) ASC
            """, (project_code,))

            timeline = cursor.fetchall()

            # Get fee breakdown
            cursor.execute("""
                SELECT
                    phase,
                    phase_fee_usd,
                    payment_status
                FROM project_fee_breakdown
                WHERE project_code = ?
                  AND payment_status = 'pending'
            """, (project_code,))

            fees = {row['phase']: row for row in cursor.fetchall()}

            # Get scope info
            cursor.execute("""
                SELECT discipline
                FROM project_scope
                WHERE project_code = ?
            """, (project_code,))

            disciplines = [row['discipline'] for row in cursor.fetchall()]
            scope = ', '.join(disciplines) if disciplines else 'General'

            # Combine timeline with fees
            for phase_timeline in timeline:
                phase = phase_timeline['phase']

                if phase in fees:
                    fee_info = fees[phase]
                    invoice_date = phase_timeline['presentation_date'] or phase_timeline['expected_end_date']

                    if invoice_date:  # Only include if we have a date
                        projected_invoices.append({
                            'project_code': project_code,
                            'project_name': project['project_name'],
                            'phase': phase,
                            'presentation_date': invoice_date,
                            'projected_fee_usd': fee_info['phase_fee_usd'],
                            'scope': scope,
                            'status': phase_timeline['status']
                        })

        # Sort by date and limit
        projected_invoices.sort(key=lambda x: x['presentation_date'])
        limited_invoices = projected_invoices[:limit]

        # Calculate total
        total_projected = sum([inv['projected_fee_usd'] or 0 for inv in limited_invoices])

        conn.close()

        return {
            'invoices': limited_invoices,
            'count': len(limited_invoices),
            'total_projected_usd': total_projected
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projected invoices: {str(e)}")

# ============================================================================
# PROPOSAL QUERY ENDPOINTS - Intelligence System
# ============================================================================

@app.get("/api/query/search")
async def query_search_proposals(q: str):
    """
    Smart search for proposals/projects by code, name, or client
    Example: /api/query/search?q=BK-070
    """
    try:
        results = proposal_query_service.search_projects_and_proposals(q)
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/proposal/{project_code}/status")
async def query_proposal_status(project_code: str):
    """
    Get full status of a proposal including documents and emails
    Example: /api/query/proposal/BK-070/status
    """
    try:
        status = proposal_query_service.get_proposal_status(project_code)
        if not status:
            raise HTTPException(status_code=404, detail="Proposal not found")
        return {"success": True, "proposal": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/proposal/{project_code}/documents")
async def query_proposal_documents(project_code: str, doc_type: Optional[str] = None):
    """
    Get documents for a proposal (optionally filtered by type: 'scope')
    Example: /api/query/proposal/BK-070/documents?doc_type=scope
    """
    try:
        docs = proposal_query_service.get_project_documents(project_code, doc_type)
        return {"success": True, "documents": docs, "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/proposal/{project_code}/fee")
async def query_proposal_fee(project_code: str):
    """
    Get the contract fee for a project
    Example: /api/query/proposal/BK-070/fee
    """
    try:
        fee = proposal_query_service.get_project_fee(project_code)
        if fee is None:
            raise HTTPException(status_code=404, detail="Project not found or fee not available")
        return {"success": True, "project_code": project_code, "fee": fee}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/proposal/{project_code}/scope")
async def query_scope_of_work(project_code: str):
    """
    Get scope of work documents for a project
    Example: /api/query/proposal/BK-070/scope
    """
    try:
        docs = proposal_query_service.find_scope_of_work(project_code)
        return {"success": True, "scope_documents": docs, "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
