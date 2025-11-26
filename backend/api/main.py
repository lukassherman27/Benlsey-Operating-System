#!/usr/bin/env python3
"""
Bensley Intelligence Platform - FastAPI Backend

Updated to use service layer and correct database schema.
Start with: uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
Access docs at: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import os
import sys
import time
from datetime import datetime, timedelta
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
from services.query_service import QueryService
from services.contract_service import ContractService
from services.proposal_tracker_service import ProposalTrackerService
from services.training_data_service import TrainingDataService
from services.admin_service import AdminService
from services.email_intelligence_service import EmailIntelligenceService
from services.deliverables_service import DeliverablesService
from services.proposal_intelligence_service import ProposalIntelligenceService
from services.ai_learning_service import AILearningService
from services.follow_up_agent import FollowUpAgent

# Add project root to path for utils
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Bensley Intelligence API",
    description="AI-powered operations platform for Bensley Design Studios",
    version="2.0.0"
)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Bensley Intelligence API starting up")
    logger.info("API documentation available at /docs")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Bensley Intelligence API shutting down")

# Add CORS middleware for dashboard access
# Use environment variable for production deployment
ALLOWED_ORIGINS = os.getenv(
    'CORS_ORIGINS',
    'http://localhost:3000,http://localhost:3001,http://localhost:3002'
).split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.perf_counter()  # More accurate than datetime

    # Skip logging for health checks (reduces log spam)
    if request.url.path in ["/health", "/api/health"]:
        return await call_next(request)

    # Log request
    logger.info(f"{request.method} {request.url.path}")

    # Process request
    try:
        response = await call_next(request)
        duration = time.perf_counter() - start_time

        # Log response
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
        return response
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"{request.method} {request.url.path} - ERROR ({duration:.3f}s): {e}", exc_info=True)
        raise

# Get database path - use environment variable with fallback
DB_PATH = os.getenv(
    'BENSLEY_DB_PATH',
    os.path.join(
        Path(__file__).parent.parent.parent,
        "database",
        "bensley_master.db"
    )
)

# Validate database exists and create directory if needed
if not os.path.exists(DB_PATH):
    logger.warning(f"⚠️  Database not found at {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    logger.info(f"📁 Created database directory")

# Initialize services with error handling
try:
    logger.info(f"📂 Loading database from: {DB_PATH}")

    proposal_service = ProposalService(DB_PATH)
    email_service = EmailService(DB_PATH)
    milestone_service = MilestoneService(DB_PATH)
    financial_service = FinancialService(DB_PATH)
    rfi_service = RFIService(DB_PATH)
    file_service = FileService(DB_PATH)
    context_service = ContextService(DB_PATH)
    meeting_service = MeetingService(DB_PATH)
    outreach_service = OutreachService(DB_PATH)
    override_service = OverrideService(DB_PATH)
    training_service = TrainingService(DB_PATH)
    proposal_query_service = ProposalQueryService(DB_PATH)
    query_service = QueryService(DB_PATH)
    contract_service = ContractService(DB_PATH)
    proposal_tracker_service = ProposalTrackerService(DB_PATH)
    admin_service = AdminService(DB_PATH)
    training_data_service = TrainingDataService(DB_PATH)
    email_intelligence_service = EmailIntelligenceService(DB_PATH)
    deliverables_service = DeliverablesService(DB_PATH)
    proposal_intelligence_service = ProposalIntelligenceService(DB_PATH)
    ai_learning_service = AILearningService(DB_PATH)
    follow_up_agent = FollowUpAgent(DB_PATH)

    logger.info("✅ All services initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize services: {e}")
    raise RuntimeError(f"Cannot start API without database access: {e}")

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
    project_title: str
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
    project_title: str = Field(..., description="Project name")
    estimated_fee_usd: Optional[float] = Field(None, description="Estimated fee in USD")
    proposal_submitted_date: Optional[str] = Field(None, description="Date proposal was submitted (YYYY-MM-DD)")
    decision_expected_date: Optional[str] = Field(None, description="Expected decision date (YYYY-MM-DD)")
    win_probability: Optional[float] = Field(None, ge=0, le=100, description="Win probability (0-100)")
    status: str = Field(default="proposal", description="Status (default: 'proposal')")
    is_active_project: int = Field(default=0, description="0 for pipeline proposal, 1 for active project")
    client_name: Optional[str] = Field(None, description="Client name")
    description: Optional[str] = Field(None, description="Optional notes/description")

    @field_validator('win_probability')
    @classmethod
    def validate_win_probability(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('win_probability must be between 0 and 100')
        return v

class UpdateProposalRequest(BaseModel):
    """Request model for updating an existing proposal"""
    project_title: Optional[str] = Field(None, description="Project name")
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

    @field_validator('win_probability')
    @classmethod
    def validate_win_probability(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('win_probability must be between 0 and 100')
        return v

class ProposalStatusUpdateRequest(BaseModel):
    """Request to update proposal status"""
    new_status: str = Field(..., description="New status (won, lost, proposal, on_hold, cancelled)")
    status_date: Optional[str] = Field(None, description="Status change date (YYYY-MM-DD), defaults to today")
    changed_by: Optional[str] = Field(default="system", description="Who made the change")
    notes: Optional[str] = Field(None, description="Notes about the status change")
    source: Optional[str] = Field(default="manual", description="Source of change (manual, email, import, api)")

class StageContractRequest(BaseModel):
    """Request to stage a contract import for review"""
    project_code: str = Field(..., description="Project code (e.g., '25 BK-033')")
    client_name: Optional[str] = Field(None, description="Client company name")
    total_fee: Optional[float] = Field(None, description="Total fee in USD")
    contract_duration: Optional[int] = Field(None, description="Contract duration in months")
    contract_date: Optional[str] = Field(None, description="Contract date (YYYY-MM-DD)")
    payment_terms: Optional[int] = Field(None, description="Payment terms in days")
    late_interest: Optional[float] = Field(None, description="Late payment interest rate (%/month)")
    stop_work_days: Optional[int] = Field(None, description="Days before suspending work")
    restart_fee: Optional[float] = Field(None, description="Restart fee percentage")
    notes: Optional[str] = Field(None, description="Additional notes")
    pdf_source_path: Optional[str] = Field(None, description="Source PDF path")
    fee_breakdown: Optional[List[List]] = Field(None, description="Fee breakdown: [[discipline, phase, fee, pct], ...]")
    imported_by: str = Field(default="web_ui", description="Who is importing")

class ApproveImportRequest(BaseModel):
    """Request to approve a staged import"""
    approved_by: str = Field(..., description="Who is approving")
    notes: Optional[str] = Field(None, description="Approval notes")

class RejectImportRequest(BaseModel):
    """Request to reject a staged import"""
    rejected_by: str = Field(..., description="Who is rejecting")
    reason: str = Field(..., description="Reason for rejection")

class EditStagedImportRequest(BaseModel):
    """Request to edit a staged import"""
    updates: Dict[str, Any] = Field(..., description="Fields to update")
    edited_by: str = Field(..., description="Who is editing")


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

            # Get all active projects with health metrics
            cursor.execute("""
                SELECT project_id, project_code, project_title, status,
                       health_score, days_since_contact, last_proposal_activity_date,
                       notes, total_fee_usd
                FROM projects
                WHERE is_active_project = 1
                ORDER BY health_score ASC NULLS LAST
            """)

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "project_id": row[0],
                    "project_code": row[1],
                    "project_title": row[2],
                    "status": row[3],
                    "health_score": row[4],
                    "days_since_contact": row[5],
                    "last_contact_date": row[6],
                    "next_action": row[7],
                    "total_fee_usd": row[8]
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
                        "project_title": p["project_title"],
                        "action": f"Call client - {p['next_action'] or 'follow up'}",
                        "context": f"{days} days no contact",
                        "detail": p["next_action"] or "Check project status"
                    })

                # NEEDS ATTENTION: 7-17 days
                elif days >= 7:
                    needs_attention.append({
                        "type": "follow_up",
                        "project_code": p["project_code"],
                        "project_title": p["project_title"],
                        "action": f"Follow up: {p['next_action'] or 'contact client'}",
                        "context": f"{days} days since last contact"
                    })

            # Business health calculation
            at_risk = len([p for p in proposals if p["health_score"] and p["health_score"] < 50])
            total_revenue = sum([p["total_fee_usd"] or 0 for p in proposals])

            # Determine overall health status
            risk_percent = (at_risk / len(proposals) * 100) if proposals else 0
            if risk_percent > 30:
                health_status = "needs_attention"
            elif risk_percent > 15:
                health_status = "caution"
            else:
                health_status = "healthy"

            # Generate insights
            insights = []
            if at_risk > 0:
                insights.append(f"{at_risk} projects need immediate attention")
            if total_revenue > 5000000:
                insights.append(f"${total_revenue/1000000:.1f}M total revenue in active projects")

            # Recent wins (emails received this week, approvals, etc.)
            wins = []
            # TODO: Add logic for detecting wins from emails/payments

            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "business_health": {
                    "status": health_status,
                    "summary": f"{len(proposals)} active projects, {at_risk} at risk, ${total_revenue/1000000:.1f}M total value"
                },
                "urgent": urgent[:5],  # Top 5 most urgent
                "needs_attention": needs_attention[:10],
                "insights": insights,
                "wins": wins,
                "metrics": {
                    "active_projects": len(proposals),
                    "at_risk": at_risk,
                    "total_revenue": total_revenue
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

            # Count human-verified training samples (skip if table missing)
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM training_data
                    WHERE human_verified = 1
                """)
                verified_count = cursor.fetchone()[0] or 0

                # Count total training samples
                cursor.execute("SELECT COUNT(*) FROM training_data")
                total_training = cursor.fetchone()[0] or 0
            except:
                verified_count = 0
                total_training = 0

            # Count attachments (skip if table missing)
            try:
                cursor.execute("SELECT COUNT(*) FROM email_attachments")
                attachment_count = cursor.fetchone()[0] or 0
            except:
                attachment_count = 0

            # Count emails needing review (skip if table missing)
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM email_content
                    WHERE category = 'general'
                """)
                needs_review_count = cursor.fetchone()[0] or 0
            except:
                needs_review_count = 0

            # Count at-risk proposals (health_score < 50)
            cursor.execute("""
                SELECT COUNT(*) FROM projects
                WHERE health_score IS NOT NULL AND health_score < 50
                AND status = 'Active'
            """)
            at_risk_count = cursor.fetchone()[0] or 0

            # Count proposals needing follow-up (14+ days no contact)
            cursor.execute("""
                SELECT COUNT(*) FROM projects
                WHERE days_since_contact >= 14
                AND status = 'Active'
            """)
            needs_follow_up_count = cursor.fetchone()[0] or 0

            # FIX: Count active projects from projects table (not proposals)
            cursor.execute("""
                SELECT COUNT(*) FROM projects
                WHERE is_active_project = 1
            """)
            active_projects_count = cursor.fetchone()[0] or 0

            # Get revenue breakdown from invoices (accurate source of truth)
            cursor.execute("""
                SELECT
                    COALESCE(SUM(i.invoice_amount), 0) as total_invoiced,
                    COALESCE(SUM(i.payment_amount), 0) as paid,
                    COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as outstanding
                FROM invoices i
            """)
            invoice_row = cursor.fetchone()

            # Get contract value for active projects
            # FIXED: Use simple query without JOIN to avoid DISTINCT hack
            cursor.execute("""
                SELECT COALESCE(SUM(total_fee_usd), 0) as total_contracts
                FROM projects
                WHERE is_active_project = 1
            """)
            contract_row = cursor.fetchone()

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
            "active": active_projects_count,
            "at_risk": at_risk_count,
            "needs_follow_up": needs_follow_up_count
        }

        # Revenue breakdown (from actual invoice data)
        revenue_breakdown = {
            "total_contracts": round(contract_row[0] or 0.0, 2),
            "paid": round(invoice_row[1] or 0.0, 2),
            "outstanding": round(invoice_row[2] or 0.0, 2),
            "remaining": round((contract_row[0] or 0.0) - (invoice_row[0] or 0.0), 2)
        }

        return DashboardStatsResponse(
            total_proposals=proposal_stats.get('total_proposals', 0),
            active_projects=active_projects_count,
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

def _calculate_trend(current: float, previous: float) -> dict:
    """
    Calculate trend percentage and direction for KPIs
    Returns trend data with percentage, direction, and label
    """
    if previous == 0:
        if current == 0:
            return {"value": 0, "direction": "neutral", "label": "0%"}
        # If previous was 0 but current isn't, show as 100% increase
        return {"value": 100.0, "direction": "up", "label": "+100%"}

    trend_pct = ((current - previous) / previous) * 100

    return {
        "value": round(trend_pct, 1),
        "direction": "up" if trend_pct > 0 else ("down" if trend_pct < 0 else "neutral"),
        "label": f"+{trend_pct:.1f}%" if trend_pct > 0 else f"{trend_pct:.1f}%"
    }

@app.get("/api/dashboard/kpis")
async def get_dashboard_kpis():
    """
    Get real-time KPI metrics for dashboard with trend indicators
    Returns actual counts/values from database with 30-day comparison

    This endpoint provides accurate KPI data for the main dashboard cards:
    - Active Projects count
    - Active Proposals count (NOT zero!)
    - Remaining Contract Value (signed but not invoiced)
    - Outstanding Invoices (unpaid)
    - Revenue YTD (paid invoices this year)

    Each KPI includes trend data comparing current value to 30 days ago
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Calculate date 30 days ago for trend comparison
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            # ========================================
            # CURRENT VALUES (Now)
            # ========================================

            # 1. Active Projects (Current)
            # FIXED: Use is_active_project flag, not status='active'
            cursor.execute("""
                SELECT COUNT(*)
                FROM projects
                WHERE is_active_project = 1
            """)
            active_projects_current = cursor.fetchone()[0]

            # 2. Active Proposals (Current)
            cursor.execute("""
                SELECT COUNT(*)
                FROM proposals
                WHERE status IN ('active', 'sent', 'follow_up', 'drafting', 'first_contact')
                AND (on_hold = 0 OR on_hold IS NULL)
            """)
            active_proposals_current = cursor.fetchone()[0]

            # 3. Remaining Contract Value (Current)
            # FIXED: Use subqueries to avoid LEFT JOIN row duplication bug
            # Remaining = Total contract - ALL invoiced (paid or unpaid)
            # FIXED: Use is_active_project flag, not status='active'
            cursor.execute("""
                SELECT
                    (SELECT COALESCE(SUM(total_fee_usd), 0)
                     FROM projects WHERE is_active_project = 1) as total_contract_value,
                    (SELECT COALESCE(SUM(i.invoice_amount), 0)
                     FROM invoices i
                     JOIN projects p ON i.project_id = p.project_id
                     WHERE p.is_active_project = 1) as total_invoiced
            """)
            row = cursor.fetchone()
            total_contracts_current = row[0] if row else 0
            total_invoiced_current = row[1] if row else 0
            remaining_contract_value_current = total_contracts_current - total_invoiced_current

            # 4. Outstanding Invoices (Current)
            # FIXED: Account for partial payments using payment_amount column
            cursor.execute("""
                SELECT COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0)
                FROM invoices
                WHERE status != 'Paid'
            """)
            outstanding_invoices_current = cursor.fetchone()[0]

            # 5. Revenue YTD (Current)
            cursor.execute("""
                SELECT COALESCE(SUM(CAST(invoice_amount AS REAL)), 0)
                FROM invoices
                WHERE payment_date IS NOT NULL
                AND strftime('%Y', payment_date) = strftime('%Y', 'now')
            """)
            revenue_ytd_current = cursor.fetchone()[0]

            # ========================================
            # HISTORICAL VALUES (30 days ago)
            # ========================================

            # 1. Active Projects (30 days ago)
            # Count projects that were active 30 days ago
            # FIXED: Use is_active_project flag, not status='active'
            cursor.execute("""
                SELECT COUNT(*)
                FROM projects
                WHERE is_active_project = 1
                AND (date_created IS NULL OR date_created <= ?)
            """, (thirty_days_ago,))
            active_projects_prev = cursor.fetchone()[0]

            # 2. Active Proposals (30 days ago)
            # Count proposals that existed 30 days ago
            cursor.execute("""
                SELECT COUNT(*)
                FROM proposals
                WHERE status IN ('active', 'sent', 'follow_up', 'drafting', 'first_contact')
                AND (on_hold = 0 OR on_hold IS NULL)
                AND (created_at IS NULL OR created_at <= ?)
            """, (thirty_days_ago,))
            active_proposals_prev = cursor.fetchone()[0]

            # 3. Remaining Contract Value (30 days ago)
            # Calculate what was remaining 30 days ago
            # FIXED: Use subqueries to avoid LEFT JOIN row duplication bug
            # Remaining = Total contract - ALL invoiced (paid or unpaid) that existed 30 days ago
            # FIXED: Use is_active_project flag, not status='active'
            cursor.execute("""
                SELECT
                    (SELECT COALESCE(SUM(total_fee_usd), 0)
                     FROM projects
                     WHERE is_active_project = 1
                     AND (date_created IS NULL OR date_created <= ?)) as total_contract_value,
                    (SELECT COALESCE(SUM(i.invoice_amount), 0)
                     FROM invoices i
                     JOIN projects p ON i.project_id = p.project_id
                     WHERE p.is_active_project = 1
                     AND (p.date_created IS NULL OR p.date_created <= ?)
                     AND (i.invoice_date IS NULL OR i.invoice_date <= ?)) as total_invoiced
            """, (thirty_days_ago, thirty_days_ago, thirty_days_ago))
            row = cursor.fetchone()
            total_contracts_prev = row[0] if row else 0
            total_invoiced_prev = row[1] if row else 0
            remaining_contract_value_prev = total_contracts_prev - total_invoiced_prev

            # 4. Outstanding Invoices (30 days ago)
            # Invoices that were outstanding 30 days ago
            # FIXED: Account for partial payments using payment_amount column
            cursor.execute("""
                SELECT COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0)
                FROM invoices
                WHERE (invoice_date IS NULL OR invoice_date <= ?)
                AND (status != 'Paid' OR (payment_date IS NOT NULL AND payment_date > ?))
            """, (thirty_days_ago, thirty_days_ago))
            outstanding_invoices_prev = cursor.fetchone()[0]

            # 5. Revenue YTD (30 days ago)
            # Revenue that was paid by 30 days ago this year
            cursor.execute("""
                SELECT COALESCE(SUM(CAST(invoice_amount AS REAL)), 0)
                FROM invoices
                WHERE payment_date IS NOT NULL
                AND payment_date <= ?
                AND strftime('%Y', payment_date) = strftime('%Y', 'now')
            """, (thirty_days_ago,))
            revenue_ytd_prev = cursor.fetchone()[0]

            # ========================================
            # CALCULATE TRENDS
            # ========================================

            trends = {
                "active_projects": _calculate_trend(active_projects_current, active_projects_prev),
                "active_proposals": _calculate_trend(active_proposals_current, active_proposals_prev),
                "remaining_contract_value": _calculate_trend(remaining_contract_value_current, remaining_contract_value_prev),
                "outstanding_invoices": _calculate_trend(outstanding_invoices_current, outstanding_invoices_prev),
                "revenue_ytd": _calculate_trend(revenue_ytd_current, revenue_ytd_prev)
            }

            return {
                "active_projects": {
                    "value": active_projects_current,
                    "previous": active_projects_prev,
                    "trend": trends["active_projects"]
                },
                "active_proposals": {
                    "value": active_proposals_current,
                    "previous": active_proposals_prev,
                    "trend": trends["active_proposals"]
                },
                "remaining_contract_value": {
                    "value": round(remaining_contract_value_current, 2),
                    "previous": round(remaining_contract_value_prev, 2),
                    "trend": trends["remaining_contract_value"]
                },
                "outstanding_invoices": {
                    "value": round(outstanding_invoices_current, 2),
                    "previous": round(outstanding_invoices_prev, 2),
                    "trend": trends["outstanding_invoices"]
                },
                "revenue_ytd": {
                    "value": round(revenue_ytd_current, 2),
                    "previous": round(revenue_ytd_prev, 2),
                    "trend": trends["revenue_ytd"]
                },
                "timestamp": datetime.now().isoformat(),
                "currency": "USD",
                "trend_period_days": 30
            }

    except Exception as e:
        logger.error(f"Error calculating KPIs with trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPIs: {str(e)}")

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
                    project_code, project_title, total_fee_usd,
                    proposal_submitted_date, decision_expected_date, win_probability,
                    status, is_active_project, client_name, description,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                request.project_code,
                request.project_title,
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
                SELECT proposal_id, project_code, project_title, status,
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
                "project_title": row[2],
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
                cursor.execute("SELECT proposal_id FROM proposals WHERE proposal_id = ?", (proposal_id,))
            except ValueError:
                cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (identifier,))

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

            query = f"UPDATE proposals SET {', '.join(updates)} WHERE proposal_id = ?"
            cursor.execute(query, params)
            conn.commit()

            # Fetch and return updated proposal
            cursor.execute("""
                SELECT proposal_id, project_code, project_name, status,
                       project_value, win_probability, is_active_project,
                       proposal_sent_date, updated_at
                FROM proposals WHERE proposal_id = ?
            """, (proposal_id,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated proposal")

            return {
                "proposal_id": row[0],
                "project_code": row[1],
                "project_name": row[2],
                "status": row[3],
                "project_value": row[4],
                "win_probability": row[5],
                "is_active_project": row[6],
                "proposal_sent_date": row[7],
                "updated_at": row[8]
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
    sort_by: str = Query("health_score", regex="^(proposal_id|project_code|project_title|status|health_score|days_since_contact|is_active_project|created_at|updated_at)$"),
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
                AND is_active_project = 1
            """)
            total = cursor.fetchone()[0] or 0

            # Get at-risk proposals with financial data
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT
                    proposal_id,
                    project_code,
                    project_title,
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
                AND is_active_project = 1
                ORDER BY health_score ASC
                LIMIT ? OFFSET ?
            """, (per_page, offset))

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_title": row[2],
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
                AND is_active_project = 1
            """, (min_days,))
            total = cursor.fetchone()[0] or 0

            # Get proposals needing follow-up
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT
                    proposal_id,
                    project_code,
                    project_title,
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
                AND is_active_project = 1
                ORDER BY days_since_contact DESC
                LIMIT ? OFFSET ?
            """, (min_days, per_page, offset))

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_title": row[2],
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

@app.get("/api/proposals/weekly-changes")
async def get_weekly_changes(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
):
    """
    Get proposal pipeline changes for Bill's weekly reports

    Returns what changed in the proposals pipeline in the specified period,
    grouped by change type: new proposals, status changes, stalled proposals,
    and won proposals.

    Args:
        days: Number of days to look back (default 7, max 90)

    Returns:
        Dict containing:
        - period: Start and end dates for the reporting period
        - summary: Aggregate counts and total pipeline value
        - new_proposals: Proposals created in the period
        - status_changes: Proposals with status changes in the period
        - stalled_proposals: Proposals with no contact in 21+ days
        - won_proposals: Proposals won/signed in the period

    Example:
        GET /api/proposals/weekly-changes?days=7
    """
    try:
        result = proposal_service.get_weekly_changes(days=days)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get weekly changes: {str(e)}"
        )

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
                    project_title,
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
                sql += " WHERE is_active_project = 1"

            sql += " ORDER BY total_fee_usd DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_title": row[2],
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
                    p.project_title,
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
                    "project_title": row[2],
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
                    SELECT proposal_id, project_code, project_title, status,
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
                        "project_title": row[2],
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

@app.post("/api/proposals/{project_code}/status")
async def update_proposal_status(
    project_code: str,
    request: ProposalStatusUpdateRequest
):
    """
    Update proposal status and record in history

    Args:
        project_code: Project code (e.g., '25 BK-001')
        request: Status update details

    Returns:
        Success status and updated proposal
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get current proposal
        cursor.execute("""
            SELECT proposal_id, project_code, status
            FROM proposals
            WHERE project_code = ?
        """, (project_code,))

        proposal = cursor.fetchone()
        if not proposal:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        proposal_id = proposal['proposal_id']
        old_status = proposal['status']
        new_status = request.new_status

        # Use provided date or default to today
        from datetime import date
        status_date = request.status_date or date.today().isoformat()

        # Update proposal status
        cursor.execute("""
            UPDATE proposals
            SET status = ?,
                last_status_change = ?,
                status_changed_by = ?,
                updated_at = datetime('now')
            WHERE project_code = ?
        """, (new_status, status_date, request.changed_by, project_code))

        # Record in history
        cursor.execute("""
            INSERT INTO proposal_status_history
            (proposal_id, project_code, old_status, new_status, status_date,
             changed_by, notes, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (proposal_id, project_code, old_status, new_status, status_date,
              request.changed_by, request.notes, request.source))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Status updated from '{old_status}' to '{new_status}'",
            "project_code": project_code,
            "old_status": old_status,
            "new_status": new_status,
            "status_date": status_date
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")

@app.get("/api/proposals/{project_code}/history")
async def get_proposal_status_history(project_code: str):
    """
    Get status change history for a proposal

    Args:
        project_code: Project code (e.g., '25 BK-001')

    Returns:
        List of status changes chronologically
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get proposal ID
        cursor.execute("""
            SELECT proposal_id, project_name, status
            FROM proposals
            WHERE project_code = ?
        """, (project_code,))

        proposal = cursor.fetchone()
        if not proposal:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        # Get status history
        cursor.execute("""
            SELECT
                history_id,
                old_status,
                new_status,
                status_date,
                changed_by,
                notes,
                source,
                created_at
            FROM proposal_status_history
            WHERE project_code = ?
            ORDER BY status_date DESC, created_at DESC
        """, (project_code,))

        history = []
        for row in cursor.fetchall():
            history.append({
                "history_id": row['history_id'],
                "old_status": row['old_status'],
                "new_status": row['new_status'],
                "status_date": row['status_date'],
                "changed_by": row['changed_by'],
                "notes": row['notes'],
                "source": row['source'],
                "created_at": row['created_at']
            })

        conn.close()

        return {
            "project_code": project_code,
            "project_name": proposal['project_name'],
            "current_status": proposal['status'],
            "history_count": len(history),
            "history": history
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status history: {str(e)}")

@app.get("/api/proposals/metrics/conversion-rate")
async def get_conversion_rate_metrics(year: Optional[int] = Query(2025, description="Year to calculate metrics for")):
    """
    Get proposal conversion rate metrics for a specific year

    Returns:
    - total_proposals_sent: Total proposals sent in the year (all statuses)
    - contracts_won: Number of proposals with status='won'
    - conversion_rate: Percentage of proposals won
    - breakdown_by_status: Count of proposals by status
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Use project code pattern to identify proposals from specific year
        # Project codes are formatted as "YY BK-XXX" where YY is the last 2 digits of year
        year_prefix = f"{str(year)[-2:]} %"

        # Get total proposals for the year
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM proposals
            WHERE project_code LIKE ?
        """, (year_prefix,))
        total_result = cursor.fetchone()
        total_proposals = total_result['total'] if total_result else 0

        # Get won proposals
        cursor.execute("""
            SELECT COUNT(*) as won
            FROM proposals
            WHERE project_code LIKE ? AND status = 'won'
        """, (year_prefix,))
        won_result = cursor.fetchone()
        contracts_won = won_result['won'] if won_result else 0

        # Get breakdown by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM proposals
            WHERE project_code LIKE ?
            GROUP BY status
            ORDER BY count DESC
        """, (year_prefix,))
        breakdown = cursor.fetchall()

        # Calculate conversion rate
        conversion_rate = (contracts_won / total_proposals * 100) if total_proposals > 0 else 0

        result = {
            "year": year,
            "total_proposals_sent": total_proposals,
            "contracts_won": contracts_won,
            "conversion_rate": round(conversion_rate, 2),
            "breakdown_by_status": [
                {"status": row['status'], "count": row['count']}
                for row in breakdown
            ]
        }

        conn.close()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversion rate: {str(e)}")

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

@app.get("/api/emails/recent")
async def get_recent_emails(
    limit: int = Query(10, ge=1, le=50, description="Number of emails to return"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """
    Get most recent emails from last N days (CRITICAL for Claude 5 - Overview Dashboard)

    Args:
        limit: Number of recent emails to return (default 10, max 50)
        days: Number of days to look back (default 30, max 365)

    Returns:
        List of recent emails with project info from last N days, sorted DESC
    """
    try:
        emails = email_service.get_recent_emails(limit=limit, days=days)
        return {
            "success": True,
            "data": emails,
            "count": len(emails),
            "days": days
        }
    except Exception as e:
        logger.error(f"Failed to get recent emails: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get recent emails: {str(e)}")

@app.get("/api/emails/stats")
async def get_email_stats():
    """Get email statistics"""
    try:
        stats = email_service.get_email_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email stats: {str(e)}")

@app.get("/api/emails/project/{project_code}")
async def get_project_emails(
    project_code: str,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get all emails linked to a specific project (CRITICAL for Claude 3 - Active Projects)

    Args:
        project_code: Project code (e.g., 'BK-033')
        limit: Max number of emails to return (default 20, max 100)

    Returns:
        List of emails for the project
    """
    try:
        emails = email_service.get_emails_by_project(project_code=project_code, limit=limit)
        return {
            "success": True,
            "project_code": project_code,
            "data": emails,
            "count": len(emails)
        }
    except Exception as e:
        logger.error(f"Failed to get emails for project {project_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get project emails: {str(e)}")

@app.get("/api/emails/proposal/{proposal_id}")
async def get_proposal_emails(
    proposal_id: int,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get all emails linked to a specific proposal (CRITICAL for Claude 4 - Proposals Tracker)

    Args:
        proposal_id: Proposal ID
        limit: Max number of emails to return (default 20, max 100)

    Returns:
        List of emails for the proposal
    """
    try:
        emails = email_service.get_emails_by_proposal_id(proposal_id=proposal_id, limit=limit)
        return {
            "success": True,
            "proposal_id": proposal_id,
            "data": emails,
            "count": len(emails)
        }
    except Exception as e:
        logger.error(f"Failed to get emails for proposal {proposal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get proposal emails: {str(e)}")

@app.get("/api/emails/categories")
async def get_email_categories():
    """
    Get count of emails by category

    Returns:
        Dict mapping category names to counts
    """
    try:
        with email_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COALESCE(ec.category, 'uncategorized') as category,
                    COUNT(*) as count
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                GROUP BY ec.category
                ORDER BY count DESC
            """)

            result = {}
            for row in cursor.fetchall():
                result[row['category']] = row['count']

            return result
    except Exception as e:
        logger.error(f"Failed to get email categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.get("/api/emails/categories/list")
async def get_email_category_list():
    """
    Get list of email categories with counts and metadata

    Returns:
        List of categories with value, label, and count
    """
    try:
        with email_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COALESCE(ec.category, 'general') as category,
                    COUNT(*) as count
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                GROUP BY ec.category
                ORDER BY count DESC
            """)

            categories = []
            for row in cursor.fetchall():
                categories.append({
                    "value": row['category'],
                    "label": row['category'].replace('_', ' ').title(),
                    "count": row['count']
                })

            return {
                "success": True,
                "categories": categories,
                "total": len(categories)
            }
    except Exception as e:
        logger.error(f"Failed to get email category list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get category list: {str(e)}")

# IMPORTANT: validation-queue must come BEFORE /api/emails/{email_id} routes
# otherwise FastAPI matches "validation-queue" as an email_id integer and fails
@app.get("/api/emails/validation-queue")
async def get_email_validation_queue(
    status: Optional[str] = Query(None, description="unlinked|low_confidence|all"),
    priority: Optional[str] = Query(None, description="high|medium|low|all"),
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
    try:
        result = email_intelligence_service.get_validation_queue(
            status=status,
            priority=priority,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get validation queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get validation queue: {str(e)}")


@app.post("/api/emails/{email_id}/category")
async def update_email_category(
    email_id: int,
    body: Dict[str, Any]
):
    """
    Update email category (for training data)

    Args:
        email_id: Email ID
        body: Dict with 'category', optional 'subcategory', 'feedback'

    Returns:
        Success status with updated email info
    """
    try:
        category = body.get('category')
        subcategory = body.get('subcategory')
        feedback = body.get('feedback')

        if not category:
            raise HTTPException(status_code=400, detail="Category is required")

        result = email_service.update_email_category(
            email_id=email_id,
            new_category=category,
            subcategory=subcategory,
            feedback=feedback
        )

        return {
            "success": True,
            "message": "Category updated successfully",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update category for email {email_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update category: {str(e)}")

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
                    p.project_title,
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
                    "project_title": row[2],
                    "confidence": row[3]
                })

        email['attachments'] = attachments
        email['linked_proposals'] = proposals

        return email

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email: {str(e)}")

@app.get("/api/emails/project/{project_code}/summary")
async def get_project_email_summary(project_code: str, use_ai: bool = True):
    """
    Get AI-generated summary of all emails for a project

    Args:
        project_code: Project code (e.g., 'BK-033')
        use_ai: Whether to generate AI summary (default: True)

    Returns:
        Email chain summary with AI-generated insights
    """
    try:
        # Get structured email data
        email_data = email_service.get_email_chain_summary(project_code)

        if not email_data['emails']:
            return {
                "success": True,
                "project_code": project_code,
                "total_emails": 0,
                "summary": "No emails found for this project.",
                "key_points": [],
                "timeline": []
            }

        # Optionally generate AI summary
        ai_summary = None
        if use_ai and email_data['emails']:
            try:
                import anthropic
                import os

                # Prepare context for AI
                email_context = "\n\n".join([
                    f"Date: {email.get('date', 'Unknown')}\n"
                    f"From: {email.get('sender_email', 'Unknown')}\n"
                    f"Subject: {email.get('subject', 'No subject')}\n"
                    f"Content: {(email.get('body_preview') or email.get('snippet') or 'No content')[:500]}"
                    for email in email_data['emails'][:20]  # Limit to 20 most recent
                ])

                client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": f"""Analyze this email chain for project {project_code} and provide:

1. A 2-3 sentence executive summary
2. 3-5 key points (bullet points)
3. Current status/next steps
4. Any red flags or important dates

Email chain ({email_data['total_emails']} emails):
{email_context}

Respond in JSON format:
{{
  "executive_summary": "...",
  "key_points": ["...", "..."],
  "status": "...",
  "red_flags": ["..."],
  "important_dates": ["..."]
}}"""
                    }]
                )

                # Parse AI response
                ai_text = message.content[0].text
                import json
                ai_summary = json.loads(ai_text)

            except Exception as ai_error:
                logger.warning(f"AI summarization failed: {ai_error}")
                ai_summary = {
                    "executive_summary": f"Unable to generate AI summary. {email_data['total_emails']} emails in chain.",
                    "error": str(ai_error)
                }

        return {
            "success": True,
            "project_code": project_code,
            "total_emails": email_data['total_emails'],
            "date_range": email_data['date_range'],
            "email_groups": {k: len(v) for k, v in email_data['email_groups'].items()},
            "ai_summary": ai_summary,
            "recent_emails": email_data['emails'][-10:] if email_data['emails'] else []
        }

    except Exception as e:
        logger.error(f"Failed to get email summary for {project_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get email summary: {str(e)}")

@app.post("/api/emails/{email_id}/read")
async def mark_email_read(email_id: int):
    """
    Mark an email as read

    Args:
        email_id: Email ID to mark as read

    Returns:
        Success status
    """
    try:
        success = email_service.mark_email_read(email_id)
        if not success:
            raise HTTPException(status_code=404, detail="Email not found")

        return {
            "success": True,
            "message": f"Email {email_id} marked as read"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark email {email_id} as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to mark email as read: {str(e)}")

class EmailLinkRequest(BaseModel):
    """Request model for linking email to project"""
    project_code: str = Field(..., description="Project code to link to (e.g., 'BK-033')")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")

@app.post("/api/emails/{email_id}/link")
async def link_email_to_project(email_id: int, request: EmailLinkRequest):
    """
    Link an email to a project

    Args:
        email_id: Email ID to link
        request: Link request with project_code and confidence

    Returns:
        Link information
    """
    try:
        result = email_service.link_email_to_project(
            email_id=email_id,
            project_code=request.project_code,
            confidence=request.confidence,
            link_type='manual'
        )

        if not result:
            raise HTTPException(status_code=404, detail=f"Email {email_id} or project {request.project_code} not found")

        return {
            "success": True,
            "data": result,
            "message": f"Email {email_id} linked to project {request.project_code}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to link email {email_id} to project {request.project_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to link email: {str(e)}")


# ============================================================================
# EMAIL CATEGORY APPROVAL ENDPOINTS (RLHF)
# ============================================================================

class ApproveCategoryRequest(BaseModel):
    """Request model for approving email category"""
    approved_by: str = Field(default="bill", description="Who is approving")

class RejectCategoryRequest(BaseModel):
    """Request model for rejecting email category"""
    new_category: str = Field(..., description="The correct category")
    reason: Optional[str] = Field(None, description="Why the AI was wrong (trains AI)")
    rejected_by: str = Field(default="bill", description="Who is rejecting")

@app.post("/api/emails/{email_id}/approve-category")
async def approve_email_category(email_id: int, body: ApproveCategoryRequest):
    """
    Approve AI email categorization (marks as human-approved for RLHF)

    Args:
        email_id: Email ID
        body: Approval info

    Returns:
        Success status
    """
    try:
        with email_service.get_connection() as conn:
            cursor = conn.cursor()

            # Check email exists
            cursor.execute("SELECT email_id FROM emails WHERE email_id = ?", (email_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Email not found")

            # Update email_content to mark as approved
            cursor.execute("""
                UPDATE email_content
                SET human_approved = 1,
                    approved_by = ?,
                    approved_at = datetime('now')
                WHERE email_id = ?
            """, (body.approved_by, email_id))

            if cursor.rowcount == 0:
                # No email_content record, create minimal one
                cursor.execute("""
                    INSERT INTO email_content (email_id, human_approved, approved_by, approved_at)
                    VALUES (?, 1, ?, datetime('now'))
                """, (email_id, body.approved_by))

            conn.commit()

            # Log to training data
            try:
                training_service = TrainingDataService(DB_PATH)
                training_service.log_feedback(
                    feature_type='email_categorization',
                    feature_id=str(email_id),
                    helpful=True,
                    feedback_text="Category approved by user",
                    context={'approved_by': body.approved_by, 'email_id': email_id}
                )
            except Exception:
                pass  # Don't fail main operation

            return {
                "success": True,
                "message": "Category approved",
                "email_id": email_id,
                "training_logged": True
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve category for email {email_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve category: {str(e)}")

@app.post("/api/emails/{email_id}/reject-category")
async def reject_email_category(email_id: int, body: RejectCategoryRequest):
    """
    Reject AI email categorization and provide correct category (RLHF training)

    Args:
        email_id: Email ID
        body: Rejection info with correct category

    Returns:
        Success status
    """
    try:
        with email_service.get_connection() as conn:
            cursor = conn.cursor()

            # Get current category for training data
            cursor.execute("""
                SELECT ec.category
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE e.email_id = ?
            """, (email_id,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Email not found")

            old_category = row[0] if row else None

            # Update email_content with correct category
            cursor.execute("""
                UPDATE email_content
                SET category = ?,
                    human_approved = 1,
                    approved_by = ?,
                    approved_at = datetime('now')
                WHERE email_id = ?
            """, (body.new_category, body.rejected_by, email_id))

            if cursor.rowcount == 0:
                # No email_content record, create one
                cursor.execute("""
                    INSERT INTO email_content (email_id, category, human_approved, approved_by, approved_at)
                    VALUES (?, ?, 1, ?, datetime('now'))
                """, (email_id, body.new_category, body.rejected_by))

            conn.commit()

            # Log to training data - THIS IS CRITICAL FOR RLHF
            try:
                training_service = TrainingDataService(DB_PATH)
                training_service.log_feedback(
                    feature_type='email_categorization',
                    feature_id=str(email_id),
                    helpful=False,  # AI was WRONG
                    issue_type='wrong_category',
                    feedback_text=body.reason or f"Changed from {old_category} to {body.new_category}",
                    expected_value=body.new_category,
                    current_value=old_category,
                    context={
                        'rejected_by': body.rejected_by,
                        'email_id': email_id,
                        'old_category': old_category,
                        'new_category': body.new_category
                    }
                )
            except Exception:
                pass  # Don't fail main operation

            return {
                "success": True,
                "message": f"Category changed to {body.new_category}",
                "email_id": email_id,
                "old_category": old_category,
                "new_category": body.new_category,
                "training_logged": True
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject category for email {email_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reject category: {str(e)}")

@app.get("/api/emails/pending-approval")
async def get_emails_pending_approval(
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get emails pending human approval of AI categorization

    Args:
        limit: Max emails to return
        category: Optional category filter

    Returns:
        List of emails needing approval
    """
    try:
        with email_service.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    e.email_id,
                    e.subject,
                    e.sender_email,
                    e.sender_name,
                    e.date,
                    e.snippet,
                    e.has_attachments,
                    ec.category as ai_category,
                    ec.subcategory,
                    ec.importance_score,
                    ec.sentiment,
                    ec.ai_summary,
                    ec.human_approved,
                    epl.project_code,
                    p.project_title as project_name,
                    epl.confidence as link_confidence
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
                LEFT JOIN projects p ON epl.project_code = p.project_code
                WHERE (ec.human_approved = 0 OR ec.human_approved IS NULL)
            """
            params = []

            if category:
                query += " AND ec.category = ?"
                params.append(category)

            query += """
                ORDER BY ec.importance_score DESC, e.date DESC
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            emails = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Get count of pending
            cursor.execute("""
                SELECT COUNT(*)
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE (ec.human_approved = 0 OR ec.human_approved IS NULL)
            """)
            total_pending = cursor.fetchone()[0]

            return {
                "success": True,
                "emails": emails,
                "count": len(emails),
                "total_pending": total_pending
            }
    except Exception as e:
        logger.error(f"Failed to get pending approval emails: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get pending emails: {str(e)}")


# ============================================================================
# EMAIL INTELLIGENCE ENDPOINTS
# ============================================================================

class EmailLinkUpdateRequest(BaseModel):
    """Request model for updating email link"""
    project_code: str = Field(..., description="Project code to link to")
    reason: str = Field(..., description="Reason for the change (trains AI)")
    updated_by: str = Field(default="bill", description="Who is making the change")


@app.get("/api/emails/{email_id}/details")
async def get_email_details(email_id: int):
    """
    Get complete email details including:
    - Basic email data
    - Current project link (if exists)
    - AI insights from email_content
    - Attachments
    - Thread information
    """
    try:
        result = email_intelligence_service.get_email_details(email_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Email not found"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get email details: {str(e)}")


@app.patch("/api/emails/{email_id}/link")
async def update_email_link(email_id: int, request: EmailLinkUpdateRequest):
    """
    Update email's project link

    This does 3 things:
    1. Updates email_project_links
    2. Logs to training_data (RLHF!)
    3. Returns success
    """
    try:
        result = email_intelligence_service.update_email_link(
            email_id=email_id,
            project_code=request.project_code,
            reason=request.reason,
            updated_by=request.updated_by
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to update link"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update email link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update link: {str(e)}")


@app.post("/api/emails/{email_id}/confirm-link")
async def confirm_email_link(
    email_id: int,
    confirmed_by: str = Query(default="bill", description="Who is confirming")
):
    """
    Confirm AI link is correct

    This:
    1. Sets confidence to 1.0
    2. Logs positive feedback to training_data
    """
    try:
        result = email_intelligence_service.confirm_email_link(
            email_id=email_id,
            confirmed_by=confirmed_by
        )

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "No link found"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to confirm email link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to confirm link: {str(e)}")


@app.delete("/api/emails/{email_id}/link")
async def unlink_email(
    email_id: int,
    reason: str = Query(..., description="Why this link is wrong"),
    updated_by: str = Query(default="bill", description="Who is unlinking")
):
    """
    Remove project link from email

    Logs to training_data that AI was wrong
    """
    try:
        result = email_intelligence_service.unlink_email(
            email_id=email_id,
            reason=reason,
            updated_by=updated_by
        )

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "No link to remove"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unlink email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to unlink email: {str(e)}")


@app.get("/api/projects/{project_code}/emails")
async def get_project_email_timeline(
    project_code: str,
    include_attachments: bool = Query(True, description="Include attachments"),
    include_threads: bool = Query(True, description="Include thread grouping")
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
    try:
        result = email_intelligence_service.get_project_email_timeline(
            project_code=project_code,
            include_attachments=include_attachments,
            include_threads=include_threads
        )

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Project not found"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project email timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@app.get("/api/projects/linking-list")
async def get_projects_for_linking(limit: int = Query(500, ge=1, le=1000)):
    """
    Get list of projects for the email link dropdown

    Returns projects sorted by:
    1. Active projects first
    2. Then by project code (descending)
    """
    try:
        projects = email_intelligence_service.get_projects_for_linking(limit=limit)
        return {"success": True, "projects": projects}
    except Exception as e:
        logger.error(f"Failed to get projects for linking: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")


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

# Removed duplicate - using enhanced version below at line 2090

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
                    SELECT proposal_id, project_code, project_title, health_score,
                           days_since_contact, last_contact_date, next_action
                    FROM projects WHERE proposal_id = ?
                """, (proposal_id,))
            except ValueError:
                cursor.execute("""
                    SELECT proposal_id, project_code, project_title, health_score,
                           days_since_contact, last_contact_date, next_action
                    FROM projects WHERE project_code = ?
                """, (identifier,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Proposal not found")

            return {
                "proposal_id": row[0],
                "project_code": row[1],
                "project_title": row[2],
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
    project_code: Optional[str] = Query(None, description="Filter by project code"),
    status: Optional[str] = Query(None, description="Filter by status: pending, complete, overdue, upcoming"),
    upcoming_days: Optional[int] = Query(None, description="Show milestones due within N days (e.g., 14 for 2 weeks)"),
    limit: int = Query(50, description="Maximum records to return")
):
    """
    List milestones with optional filtering.

    Enhanced filters:
    - project_code: Filter by project
    - status: pending, complete, overdue, or upcoming
    - upcoming_days: Show milestones due within N days

    NOTE: Some milestones may have NULL planned_date. These are still returned
    but sorted to the end.
    """
    import sqlite3
    from datetime import date, timedelta

    try:
        # If only proposal_id provided, use existing service
        if proposal_id and not project_code and not upcoming_days:
            milestones = milestone_service.get_milestones_by_proposal(proposal_id)
            return {"total": len(milestones), "milestones": milestones}

        # Use direct query for enhanced filtering
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT milestone_id, project_id, project_code, phase,
                   milestone_name, milestone_type, planned_date,
                   actual_date, status, notes, created_at
            FROM project_milestones
            WHERE 1=1
        """
        params = []
        today = date.today()

        if project_code:
            query += " AND (project_code = ? OR project_code LIKE ?)"
            params.extend([project_code, f"%{project_code}%"])

        if upcoming_days is not None:
            future_date = (today + timedelta(days=upcoming_days)).isoformat()
            today_str = today.isoformat()
            query += " AND planned_date IS NOT NULL AND planned_date >= ? AND planned_date <= ?"
            params.extend([today_str, future_date])
        elif status:
            if status == "overdue":
                today_str = today.isoformat()
                query += " AND status != 'complete' AND planned_date IS NOT NULL AND planned_date < ?"
                params.append(today_str)
            elif status == "upcoming":
                future_date = (today + timedelta(days=30)).isoformat()
                today_str = today.isoformat()
                query += " AND planned_date IS NOT NULL AND planned_date >= ? AND planned_date <= ?"
                params.extend([today_str, future_date])
            elif status in ("pending", "complete"):
                query += " AND status = ?"
                params.append(status)
            else:
                # Unknown status, filter anyway
                query += " AND status = ?"
                params.append(status)

        # Sort: milestones with dates first, then by date
        query += " ORDER BY CASE WHEN planned_date IS NULL THEN 1 ELSE 0 END, planned_date ASC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        milestones = [dict(row) for row in rows]
        conn.close()

        # Add computed fields
        today_str = today.isoformat()
        for m in milestones:
            if m.get('planned_date') and m.get('status') != 'complete':
                m['is_overdue'] = m['planned_date'] < today_str
                if not m['is_overdue']:
                    days_until = (date.fromisoformat(m['planned_date']) - today).days
                    m['days_until_due'] = days_until
                else:
                    days_overdue = (today - date.fromisoformat(m['planned_date'])).days
                    m['days_overdue'] = days_overdue
            else:
                m['is_overdue'] = False

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
    project_code: Optional[str] = Query(None, description="Filter by project code"),
    status: Optional[str] = Query(None, description="Filter by status: open, answered, overdue"),
    overdue_only: bool = Query(False, description="Show only overdue RFIs (date_due < today and status = 'open')"),
    limit: int = Query(50, description="Maximum records to return")
):
    """
    List RFIs with optional filtering.

    Enhanced filters:
    - project_code: Filter by project
    - status: Filter by status (open, answered, overdue)
    - overdue_only: Show only overdue RFIs

    An RFI is "overdue" if: status = 'open' AND date_due < today
    """
    import sqlite3
    from datetime import date

    try:
        # If proposal_id provided, use existing service
        if proposal_id and not project_code and not overdue_only:
            rfis = rfi_service.get_rfis_by_proposal(proposal_id)
            return {"total": len(rfis), "rfis": rfis}

        # Use direct query for enhanced filtering
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM rfis WHERE 1=1"
        params = []

        if project_code:
            query += " AND (project_code = ? OR project_code LIKE ?)"
            params.extend([project_code, f"%{project_code}%"])

        if overdue_only:
            today = date.today().isoformat()
            query += " AND status = 'open' AND date_due < ?"
            params.append(today)
        elif status:
            if status == 'overdue':
                today = date.today().isoformat()
                query += " AND status = 'open' AND date_due < ?"
                params.append(today)
            else:
                query += " AND status = ?"
                params.append(status)

        query += " ORDER BY date_due ASC, priority DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        rfis = [dict(row) for row in rows]
        conn.close()

        # Calculate overdue status for each RFI
        today = date.today().isoformat()
        for rfi in rfis:
            if rfi.get('status') == 'open' and rfi.get('date_due'):
                rfi['is_overdue'] = rfi['date_due'] < today
            else:
                rfi['is_overdue'] = False

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

@app.get("/api/rfis/overdue")
async def get_overdue_rfis():
    """
    Get all RFIs that are past their 48-hour SLA

    Returns RFIs sorted by how overdue they are (most overdue first)
    """
    try:
        overdue = rfi_service.get_overdue_rfis()
        return {
            "total": len(overdue),
            "rfis": overdue,
            "alert": f"{len(overdue)} RFI(s) overdue!" if overdue else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overdue RFIs: {str(e)}")

@app.get("/api/rfis/stats")
async def get_rfi_stats():
    """
    Get RFI statistics for dashboard

    Returns summary counts and alert status
    """
    try:
        stats = rfi_service.get_rfi_stats_for_dashboard()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RFI stats: {str(e)}")

@app.get("/api/rfis/{rfi_id}")
async def get_rfi_detail(rfi_id: int):
    """Get detailed information about a specific RFI"""
    try:
        rfi = rfi_service.get_rfi_by_id(rfi_id)
        if not rfi:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")
        return rfi
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RFI: {str(e)}")

@app.post("/api/rfis/{rfi_id}/respond")
async def mark_rfi_responded(rfi_id: int):
    """
    Mark an RFI as responded (simple checkbox workflow)

    This is the "boom, sent out, done" action for PMs.
    Just marks it as responded with current timestamp.
    """
    try:
        success = rfi_service.mark_responded(rfi_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")
        return {
            "success": True,
            "message": "RFI marked as responded",
            "rfi_id": rfi_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark RFI responded: {str(e)}")

@app.post("/api/rfis/{rfi_id}/close")
async def close_rfi(rfi_id: int):
    """Mark an RFI as closed (fully resolved)"""
    try:
        success = rfi_service.close_rfi(rfi_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")
        return {
            "success": True,
            "message": "RFI closed",
            "rfi_id": rfi_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close RFI: {str(e)}")

class RFIAssignRequest(BaseModel):
    """Request to assign PM to RFI"""
    pm_id: int = Field(..., description="Team member ID to assign")

@app.post("/api/rfis/{rfi_id}/assign")
async def assign_rfi_to_pm(rfi_id: int, request: RFIAssignRequest):
    """
    Assign an RFI to a specific PM

    Args:
        rfi_id: RFI to assign
        request.pm_id: Team member ID from team_members table
    """
    try:
        success = rfi_service.update_rfi(rfi_id, {"assigned_pm_id": request.pm_id})
        if not success:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")
        return {
            "success": True,
            "message": f"RFI assigned to PM {request.pm_id}",
            "rfi_id": rfi_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign RFI: {str(e)}")

@app.get("/api/rfis/by-project/{project_code}")
async def get_rfis_by_project(project_code: str):
    """Get all RFIs for a specific project by project code"""
    try:
        rfis = rfi_service.get_rfis_by_project(project_code)
        summary = rfi_service.get_rfi_summary(project_code)
        return {
            "project_code": project_code,
            "summary": summary,
            "rfis": rfis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RFIs: {str(e)}")

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
                SELECT proposal_id, project_title, contact_person
                FROM projects
                WHERE project_code = ?
            """, (project_code,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Proposal not found")

            proposal_id, project_title, pm = row[0], row[1], row[2] or "Unassigned"

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
                "project_title": project_title
            }
            timeline_events.append(event)

        return {
            "proposal": {
                "project_code": project_code,
                "project_title": project_title,
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
                    proposal_id, project_code, project_title, client_company,
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
                SELECT project_code, project_title, team_lead, days_since_contact, notes
                FROM projects
                WHERE days_since_contact >= 14
                AND is_active_project = 0 AND status = 'proposal'
                ORDER BY days_since_contact DESC
                LIMIT 10
            """)
            needs_outreach = [
                {
                    "project_code": row[0],
                    "project_title": row[1],
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
                    "project_title": row[2]  # Use code as fallback for name
                }
                for row in cursor.fetchall()
            ]

            # Count unanswered RFIs
            cursor.execute("""
                SELECT COUNT(*) FROM rfis
                WHERE status = 'unanswered'
            """)
            unanswered_rfis_count = cursor.fetchone()[0] or 0

            # Get unanswered RFI details
            cursor.execute("""
                SELECT
                    r.rfi_number, r.subject, r.date_sent,
                    p.project_code, p.project_title
                FROM rfis r
                JOIN projects p ON r.project_id = p.project_id
                WHERE r.status = 'unanswered'
                ORDER BY r.date_sent ASC
                LIMIT 10
            """)
            unanswered_rfis = [
                {
                    "rfi_number": row[0],
                    "question": row[1],
                    "asked_date": row[2],
                    "project_code": row[3],
                    "project_title": row[4]
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
                    p.project_code, p.project_title
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
                    "project_title": row[4]
                }
                for row in cursor.fetchall()
            ]

            # Count invoices awaiting payment
            cursor.execute("""
                SELECT
                    COUNT(*),
                    SUM(invoice_amount - COALESCE(payment_amount, 0))
                FROM invoices
                WHERE status NOT IN ('paid')
                AND (invoice_amount - COALESCE(payment_amount, 0)) > 0
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
                "rfis": {
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

@app.get("/api/admin/system-stats")
async def get_system_stats():
    """
    Comprehensive system statistics for the status dashboard

    Returns:
    - Email processing stats (total, processed, unprocessed, categories)
    - Email links quality (total, auto, manual, approved, low confidence)
    - Proposals breakdown (total, active, proposal, lost)
    - Projects stats
    - Financial data (contracts, invoices, revenue)
    - Database stats (size, tables, records)
    - API health
    """
    try:
        import os
        import time
        from datetime import datetime

        start_time = time.time()

        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Email stats with processing status
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

            # Email categories breakdown
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM emails
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """)
            categories = {row[0]: row[1] for row in cursor.fetchall()}

            # Email links stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN auto_linked = 1 THEN 1 ELSE 0 END) as auto,
                    SUM(CASE WHEN auto_linked = 0 THEN 1 ELSE 0 END) as manual,
                    SUM(CASE WHEN confidence_score < 0.7 THEN 1 ELSE 0 END) as low_confidence
                FROM email_proposal_links
            """)
            links_row = cursor.fetchone()

            # Count approved links (manual with high confidence or explicitly approved in match_reasons)
            cursor.execute("""
                SELECT COUNT(*)
                FROM email_proposal_links
                WHERE (auto_linked = 0 AND confidence_score >= 0.95)
                   OR match_reasons LIKE '%Approved by%'
            """)
            approved_count = cursor.fetchone()[0] or 0

            # Proposals breakdown
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'proposal' THEN 1 ELSE 0 END) as proposal,
                    SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost
                FROM proposals
            """)
            proposals_row = cursor.fetchone()

            # Projects stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active
                FROM projects
            """)
            projects_row = cursor.fetchone()

            # Financial data
            cursor.execute("SELECT COUNT(*) FROM contract_metadata")
            total_contracts = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM invoices")
            total_invoices = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(total_contract_value_usd) FROM contract_metadata WHERE total_contract_value_usd IS NOT NULL")
            total_revenue = cursor.fetchone()[0] or 0

            # Database stats
            db_path = "database/bensley_master.db"
            if os.path.exists(db_path):
                db_size_bytes = os.path.getsize(db_path)
                db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
            else:
                db_size_mb = 0

            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            total_tables = cursor.fetchone()[0] or 0

            # Total records across all tables (rough estimate)
            total_records = (
                total_emails +
                (proposals_row[0] or 0) +
                (projects_row[0] or 0) +
                total_contracts +
                total_invoices +
                (links_row[0] or 0)
            )

            return {
                "database": {
                    "size_mb": db_size_mb,
                    "tables": total_tables,
                    "total_records": total_records
                },
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
                "projects": {
                    "total": projects_row[0] or 0,
                    "active": projects_row[1] or 0
                },
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

    except Exception as e:
        logger.error(f"Failed to get system stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")

# ============================================================================
# ADMIN - DATA VALIDATION ENDPOINTS
# ============================================================================

class ApproveSuggestionRequest(BaseModel):
    """Request model for approving a validation suggestion"""
    reviewed_by: str = Field(..., description="Username or email of reviewer")
    review_notes: Optional[str] = Field(None, description="Optional notes about the approval")

class DenySuggestionRequest(BaseModel):
    """Request model for denying a validation suggestion"""
    reviewed_by: str = Field(..., description="Username or email of reviewer")
    review_notes: str = Field(..., description="Required notes explaining why denied")

class CreateEmailLinkRequest(BaseModel):
    """Request model for manually linking an email to a proposal"""
    email_id: int = Field(..., description="Email ID")
    proposal_id: int = Field(..., description="Proposal ID")
    user: str = Field(..., description="Username or email of user creating the link")

@app.get("/api/admin/validation/suggestions")
async def get_validation_suggestions(
    status: Optional[str] = Query(None, description="Filter by status (pending/approved/denied/applied)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get data validation suggestions with evidence

    Returns AI-generated suggestions for data corrections with:
    - Evidence from emails or other sources
    - Current vs suggested values
    - Confidence scores and reasoning
    - Status (pending/approved/denied/applied)
    """
    try:
        result = admin_service.get_validation_suggestions(
            status=status,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get validation suggestions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get validation suggestions: {str(e)}")

@app.get("/api/admin/validation/suggestions/{suggestion_id}")
async def get_validation_suggestion(suggestion_id: int):
    """
    Get single validation suggestion with full details
    """
    try:
        suggestion = admin_service.get_suggestion_by_id(suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found")
        return suggestion
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get suggestion {suggestion_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get suggestion: {str(e)}")

@app.post("/api/admin/validation/suggestions/{suggestion_id}/approve")
async def approve_validation_suggestion(
    suggestion_id: int,
    request: ApproveSuggestionRequest
):
    """
    Approve and apply a validation suggestion

    This will:
    1. Update the suggestion status to 'approved' then 'applied'
    2. Apply the change to the target entity (proposal/project/contract/invoice)
    3. Log the application in the suggestion_application_log
    4. Return success message with details
    """
    try:
        result = admin_service.approve_suggestion(
            suggestion_id=suggestion_id,
            reviewed_by=request.reviewed_by,
            review_notes=request.review_notes
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve suggestion {suggestion_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve suggestion: {str(e)}")

@app.post("/api/admin/validation/suggestions/{suggestion_id}/deny")
async def deny_validation_suggestion(
    suggestion_id: int,
    request: DenySuggestionRequest
):
    """
    Deny a validation suggestion

    Requires notes explaining why the suggestion was denied.
    """
    try:
        result = admin_service.deny_suggestion(
            suggestion_id=suggestion_id,
            reviewed_by=request.reviewed_by,
            review_notes=request.review_notes
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deny suggestion {suggestion_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to deny suggestion: {str(e)}")

# ============================================================================
# ADMIN - EMAIL LINK MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/admin/email-links")
async def get_email_links(
    project_code: Optional[str] = Query(None, description="Filter by project code"),
    confidence_min: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence score (0-1)"),
    link_type: Optional[str] = Query(None, description="Filter by link type (auto/manual/ai_suggested)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get email-to-proposal links with evidence and confidence scores

    Shows:
    - Email subject, sender, date
    - Linked project code and name
    - Confidence score (0-1)
    - Link type (auto/manual/ai_suggested)
    - Evidence/reasoning for the link
    """
    try:
        result = admin_service.get_email_links(
            project_code=project_code,
            confidence_min=confidence_min,
            link_type=link_type,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get email links: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get email links: {str(e)}")

@app.delete("/api/admin/email-links/{link_id}")
async def unlink_email(
    link_id: int,
    user: str = Query(..., description="Username or email of user removing the link")
):
    """
    Remove an email-to-proposal link
    """
    try:
        result = admin_service.unlink_email(link_id=link_id, user=user)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unlink email {link_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to unlink email: {str(e)}")

@app.post("/api/admin/email-links")
async def create_manual_email_link(request: CreateEmailLinkRequest):
    """
    Manually create an email-to-proposal link

    Creates a link with confidence=1.0 and link_type='manual'
    """
    try:
        result = admin_service.create_manual_link(
            email_id=request.email_id,
            proposal_id=request.proposal_id,
            user=request.user
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create manual link: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create manual link: {str(e)}")

class UpdateEmailLinkRequest(BaseModel):
    """Request model for updating an email-to-proposal link"""
    link_type: Optional[str] = Field(None, description="Link type (auto/manual/approved)")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score (0-1)")
    match_reasons: Optional[str] = Field(None, description="Reasoning for the link")
    user: Optional[str] = Field(None, description="Username or email of user updating the link")

@app.patch("/api/admin/email-links/{link_id}")
async def update_email_link(link_id: int, request: UpdateEmailLinkRequest):
    """
    Update an existing email-to-proposal link

    Use this to:
    - Approve AI-generated links (set link_type='approved', confidence_score=1.0)
    - Update confidence scores
    - Change link type
    - Update match reasoning
    """
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

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update email link {link_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update email link: {str(e)}")

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


@app.get("/api/training/feedback/stats")
async def get_feedback_stats(
    feature: Optional[str] = Query(None, description="Filter by feature name"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """
    Get feedback statistics for analysis

    Shows:
    - Total feedback count by feature
    - Helpful vs not helpful counts
    - Correction counts
    - Unique user counts

    Args:
        feature: Optional feature name filter
        days: Number of days to look back (default 30)

    Returns:
        Dict with stats and period_days
    """
    try:
        training_data_service = TrainingDataService(db_path=DB_PATH)
        stats = training_data_service.get_feedback_stats(feature=feature, days=days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback stats: {str(e)}")

@app.get("/api/training/feedback/corrections")
async def get_corrections_for_review(
    feature: Optional[str] = Query(None, description="Filter by feature name"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number to return")
):
    """
    Get recent corrections for review/analysis

    Useful for understanding what users are correcting:
    - Which AI categories are wrong most often
    - Common correction patterns
    - Training data for RLHF

    Args:
        feature: Optional feature name filter
        limit: Maximum number of corrections to return

    Returns:
        List of corrections with original/corrected values
    """
    try:
        training_data_service = TrainingDataService(db_path=DB_PATH)
        corrections = training_data_service.get_corrections_for_review(
            feature=feature,
            limit=limit
        )
        return {
            "success": True,
            "corrections": corrections,
            "count": len(corrections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get corrections: {str(e)}")

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
                SELECT proposal_id, project_code, project_title
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
                    "project_title": name
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
                SELECT proposal_id, project_code, project_title, status, pm, next_action, updated_at
                FROM projects
                WHERE project_code IN ({placeholders})
            """, project_codes)

            updated_proposals = []
            for row in cursor.fetchall():
                updated_proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_title": row[2],
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
    status: str = Query("pending", description="Filter by status: pending, approved, rejected, applied"),
    data_table: Optional[str] = Query(None, description="Filter by table: projects, proposals, emails, etc"),
    limit: int = Query(100, description="Max results")
):
    """Get AI-generated suggestions filtered by status and data table"""
    try:
        service = IntelligenceService()
        return service.get_suggestions(status=status, data_table=data_table, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


class DecisionRequest(BaseModel):
    decision: str = Field(..., description="approved or rejected")
    reason: Optional[str] = Field(None, description="Reason for decision")
    apply_now: bool = Field(True, description="Apply changes immediately")
    dry_run: bool = Field(False, description="Preview without applying")


@app.post("/api/intel/suggestions/{suggestion_id}/decision")
async def apply_decision(suggestion_id: int, request: DecisionRequest):
    """Apply a decision (approve/reject) to a suggestion"""
    try:
        service = IntelligenceService()
        return service.apply_decision(
            suggestion_id=suggestion_id,
            decision=request.decision,
            reason=request.reason,
            apply_now=request.apply_now,
            dry_run=request.dry_run
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
# Note: DB_PATH is already defined at the top of this file using OneDrive location

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

class AuditFeedbackRequest(BaseModel):
    question_type: str  # 'scope', 'fee_breakdown', 'timeline', etc.
    ai_suggestion: Dict
    user_correction: Dict
    context_provided: Optional[str] = None
    confidence_before: float


@app.post("/api/audit/feedback/{project_code}")
async def submit_feedback(project_code: str, request: AuditFeedbackRequest):
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
            SELECT project_code, project_title, is_active_project, total_fee_usd, status
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

        # Get recent payments with project info and discipline/phase from breakdown
        cursor.execute("""
            SELECT
                i.invoice_id,
                i.invoice_number,
                i.description,
                i.payment_amount as amount_usd,
                i.payment_date as paid_on,
                p.project_code,
                p.project_title,
                pfb.discipline,
                pfb.phase,
                pfb.scope
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            LEFT JOIN project_fee_breakdown pfb ON i.breakdown_id = pfb.breakdown_id
            WHERE i.payment_date IS NOT NULL
              AND i.payment_amount > 0
            ORDER BY i.payment_date DESC
            LIMIT ?
        """, (limit,))

        payments = []
        for row in cursor.fetchall():
            # Build discipline display from breakdown or fallback to description
            discipline = row['discipline'] or ''
            phase = row['phase'] or ''
            scope = row['scope'] or ''
            description = row['description'] or ''

            # Format: "Discipline - Phase" or "Discipline / Scope / Phase" or just description
            if discipline and phase:
                if scope:
                    discipline_display = f"{discipline} / {scope} / {phase}"
                else:
                    discipline_display = f"{discipline} - {phase}"
            elif description:
                discipline_display = description
            else:
                discipline_display = 'General'

            payments.append({
                'invoice_id': row['invoice_id'],
                'invoice_number': row['invoice_number'],
                'project_code': row['project_code'],
                'project_title': row['project_title'],
                'discipline': discipline_display,
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
                p.project_title,
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
                            'project_title': project['project_title'],
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


# ================================
# Enhanced Financial Dashboard Endpoints (Migration 023)
# ================================

@app.get("/api/finance/dashboard-metrics")
async def get_dashboard_metrics():
    """
    Get top-level financial metrics for dashboard overview

    Returns:
        - total_contract_value: Sum of all active project contracts
        - total_invoiced: Sum of all invoiced amounts
        - total_paid: Sum of all payments received
        - total_outstanding: Total invoiced but not paid (not overdue)
        - total_overdue: Total invoiced and past due date
        - total_remaining: Total uninvoiced contract value
        - active_project_count: Number of active projects
    """
    try:
        metrics = financial_service.get_dashboard_financial_metrics()
        return {
            'success': True,
            'metrics': metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard metrics: {str(e)}")


@app.get("/api/finance/projects-by-outstanding")
async def get_projects_by_outstanding(limit: int = Query(5, description="Number of projects to return")):
    """
    Get projects with highest outstanding amounts

    Returns list of projects sorted by outstanding_usd DESC
    """
    try:
        projects = financial_service.get_projects_by_outstanding(limit)
        return {
            'success': True,
            'projects': projects,
            'count': len(projects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects by outstanding: {str(e)}")


@app.get("/api/finance/oldest-unpaid-invoices")
async def get_oldest_unpaid_invoices(limit: int = Query(5, description="Number of invoices to return")):
    """
    Get oldest unpaid invoices (by days since invoice_date, not days overdue)

    Returns list of invoices sorted by days_outstanding DESC
    """
    try:
        invoices = financial_service.get_oldest_unpaid_invoices(limit)
        return {
            'success': True,
            'invoices': invoices,
            'count': len(invoices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get oldest unpaid invoices: {str(e)}")


@app.get("/api/finance/projects-by-remaining")
async def get_projects_by_remaining_value(limit: int = Query(5, description="Number of projects to return")):
    """
    Get projects with highest remaining uninvoiced contract value

    Returns list of projects sorted by total_remaining_usd DESC
    """
    try:
        projects = financial_service.get_projects_by_remaining_value(limit)
        return {
            'success': True,
            'projects': projects,
            'count': len(projects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects by remaining value: {str(e)}")


@app.get("/api/finance/invoice-aging")
async def get_invoice_aging_summary():
    """
    Get aging summary across all unpaid invoices
    Groups by aging buckets (Current, 1-30 days, 31-60 days, etc.)

    Returns:
        - aging_buckets: List of {aging_bucket, invoice_count, total_outstanding}
        - total_unpaid_invoices: Total count
        - total_unpaid_amount: Total outstanding amount
    """
    try:
        aging = financial_service.get_invoice_aging_summary()
        return {
            'success': True,
            'aging': aging
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get invoice aging: {str(e)}")


@app.get("/api/projects/{project_code}/financial-detail")
async def get_project_financial_detail(project_code: str):
    """
    Get comprehensive financial breakdown for a specific project

    Includes:
        - project_summary: Overall financial metrics
        - phase_breakdown: Financial status by discipline and phase
        - invoices: All invoices for this project
        - phase_links: Invoice-to-phase mappings for partial invoicing
    """
    try:
        detail = financial_service.get_project_financial_detail(project_code)

        if not detail:
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        return {
            'success': True,
            'project_code': project_code,
            **detail
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project financial detail: {str(e)}")


@app.get("/api/projects/{project_code}/hierarchy")
async def get_project_hierarchy(project_code: str):
    """
    Get hierarchical breakdown: Project → Discipline → Phase → Invoices

    Returns nested tree structure for visualizing project financial hierarchy:
    - Disciplines (Architecture, Interior, Landscape, etc.)
      - Phases (Mobilization, Concept Design, etc.)
        - Invoices applied to each phase
        - Financial progress (fee, invoiced, paid, remaining)

    Example: /api/projects/25-BK-033/hierarchy
    """
    try:
        hierarchy = financial_service.get_project_hierarchy(project_code)

        if not hierarchy.get('success'):
            raise HTTPException(
                status_code=404,
                detail=hierarchy.get('error', 'Project not found')
            )

        return hierarchy
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project hierarchy: {str(e)}"
        )


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

# ============================================================================
# NATURAL LANGUAGE QUERY ENDPOINTS - AI-Powered Queries
# ============================================================================

# ==================== Invoice Management ====================

from backend.services.invoice_service import InvoiceService

invoice_service = InvoiceService(DB_PATH)


@app.get("/api/invoices/stats")
async def get_invoice_stats():
    """Get revenue statistics from invoices"""
    try:
        stats = invoice_service.get_revenue_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/recent")
async def get_recent_payments(limit: int = Query(5, ge=1, le=50)):
    """Get recently paid invoices"""
    try:
        payments = invoice_service.get_recent_payments(limit)
        return {
            "success": True,
            "payments": payments,
            "count": len(payments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/outstanding")
async def get_outstanding_invoices():
    """Get all outstanding and overdue invoices"""
    try:
        invoices = invoice_service.get_outstanding_invoices()
        return {
            "success": True,
            "invoices": invoices,
            "count": len(invoices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/by-project/{project_code}")
async def get_project_invoices(project_code: str):
    """Get all invoices for a specific project"""
    try:
        invoices = invoice_service.get_invoices_by_project(project_code)
        return {
            "success": True,
            "project_code": project_code,
            "invoices": invoices,
            "count": len(invoices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/aging")
async def get_invoice_aging():
    """Get complete invoice aging data for dashboard widget"""
    try:
        aging_data = invoice_service.get_invoice_aging_data()
        return {
            "success": True,
            "data": aging_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/recent-paid")
async def get_recent_paid_invoices(limit: int = Query(5, ge=1, le=50)):
    """Get last N paid invoices (newest first)"""
    try:
        invoices = invoice_service.get_recent_paid_invoices(limit)
        return {
            "success": True,
            "data": invoices,
            "count": len(invoices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/largest-outstanding")
async def get_largest_outstanding_invoices(limit: int = Query(10, ge=1, le=50)):
    """Get largest outstanding invoices by amount"""
    try:
        invoices = invoice_service.get_largest_outstanding_invoices(limit)
        return {
            "success": True,
            "data": invoices,
            "count": len(invoices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/aging-breakdown")
async def get_aging_breakdown():
    """Get invoice aging breakdown (<30, 30-90, >90 days)"""
    try:
        breakdown = invoice_service.get_aging_breakdown()
        return {
            "success": True,
            "data": breakdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_aging_category(days: int) -> Dict[str, Any]:
    """Get color-coded aging category based on days outstanding"""
    if days <= 10:
        return {"bucket": "0-10 days", "color": "green", "severity": "current"}
    elif days <= 30:
        return {"bucket": "10-30 days", "color": "yellow", "severity": "warning"}
    elif days <= 90:
        return {"bucket": "30-90 days", "color": "orange", "severity": "urgent"}
    else:
        return {"bucket": "90+ days", "color": "red", "severity": "critical"}


@app.get("/api/invoices/top-outstanding")
async def get_top_outstanding_invoices():
    """Get top 10 outstanding unpaid invoices with project details"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.invoice_number,
                i.invoice_date,
                i.invoice_amount,
                COALESCE(i.payment_amount, 0) as payment_amount,
                (i.invoice_amount - COALESCE(i.payment_amount, 0)) as outstanding,
                CAST(JULIANDAY('now') - JULIANDAY(i.invoice_date) AS INTEGER) as days_outstanding,
                p.project_code,
                p.project_title as project_name,
                i.description as phase_info,
                i.status
            FROM invoices i
            LEFT JOIN projects p ON i.project_id = p.project_id
            WHERE i.status NOT IN ('paid', 'cancelled')
            AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
            ORDER BY outstanding DESC
            LIMIT 10
        """)

        invoices = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            days = row_dict['days_outstanding']
            invoices.append({
                "invoice_number": row_dict['invoice_number'],
                "invoice_date": row_dict['invoice_date'],
                "outstanding": row_dict['outstanding'],
                "days_outstanding": days,
                "project_code": row_dict['project_code'] or 'N/A',
                "project_name": row_dict['project_name'] or 'Unknown Project',
                "phase": row_dict['phase_info'] or 'N/A',
                "discipline": 'N/A',  # Not tracking discipline separately
                "aging_category": get_aging_category(days)
            })

        conn.close()
        return {"success": True, "invoices": invoices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/outstanding-filtered")
async def get_all_outstanding_invoices(
    project_code: Optional[str] = Query(None),
    min_days: Optional[int] = Query(None),
    max_days: Optional[int] = Query(None)
):
    """Get all outstanding invoices with filters"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build WHERE clause
        where_clauses = [
            "i.status NOT IN ('paid', 'cancelled')",
            "(i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0"
        ]
        params = []

        if project_code:
            where_clauses.append("p.project_code = ?")
            params.append(project_code)

        if min_days is not None:
            where_clauses.append("CAST(JULIANDAY('now') - JULIANDAY(i.invoice_date) AS INTEGER) >= ?")
            params.append(min_days)

        if max_days is not None:
            where_clauses.append("CAST(JULIANDAY('now') - JULIANDAY(i.invoice_date) AS INTEGER) <= ?")
            params.append(max_days)

        where_sql = " AND ".join(where_clauses)

        cursor.execute(f"""
            SELECT
                i.invoice_number,
                i.invoice_date,
                i.invoice_amount,
                COALESCE(i.payment_amount, 0) as payment_amount,
                (i.invoice_amount - COALESCE(i.payment_amount, 0)) as outstanding,
                CAST(JULIANDAY('now') - JULIANDAY(i.invoice_date) AS INTEGER) as days_outstanding,
                p.project_code,
                p.project_title as project_name,
                i.description as phase_info,
                i.status
            FROM invoices i
            LEFT JOIN projects p ON i.project_id = p.project_id
            WHERE {where_sql}
            ORDER BY i.invoice_date ASC
        """, params)

        invoices = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            days = row_dict['days_outstanding']
            invoices.append({
                "invoice_number": row_dict['invoice_number'],
                "invoice_date": row_dict['invoice_date'],
                "invoice_amount": row_dict['invoice_amount'],
                "payment_amount": row_dict['payment_amount'],
                "outstanding": row_dict['outstanding'],
                "days_outstanding": days,
                "project_code": row_dict['project_code'] or 'N/A',
                "project_name": row_dict['project_name'] or 'Unknown Project',
                "phase": row_dict['phase_info'] or 'N/A',
                "discipline": 'N/A',  # Not tracking discipline separately
                "aging_category": get_aging_category(days)
            })

        conn.close()
        return {
            "success": True,
            "invoices": invoices,
            "total_outstanding": sum(inv['outstanding'] for inv in invoices),
            "count": len(invoices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_code}/fee-breakdown")
async def get_project_fee_breakdown(project_code: str):
    """Get contract fee breakdown by discipline and phase for a project with financial summary"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get project info
        cursor.execute("""
            SELECT project_id, project_title, total_fee_usd
            FROM projects WHERE project_code = ?
        """, (project_code,))
        project_row = cursor.fetchone()

        project_info = dict(project_row) if project_row else {}

        # Get fee breakdowns with scope and calculated percentages
        cursor.execute("""
            SELECT
                pfb.breakdown_id,
                pfb.project_code,
                pfb.scope,
                pfb.discipline,
                pfb.phase,
                pfb.phase_fee_usd,
                pfb.percentage_of_total,
                pfb.created_at,
                pfb.updated_at,
                COALESCE(SUM(i.invoice_amount), 0) as total_invoiced,
                COALESCE(SUM(i.payment_amount), 0) as total_paid,
                CASE
                    WHEN pfb.phase_fee_usd > 0 THEN
                        ROUND(COALESCE(SUM(i.invoice_amount), 0) / pfb.phase_fee_usd * 100, 1)
                    ELSE 0
                END as percentage_invoiced,
                CASE
                    WHEN pfb.phase_fee_usd > 0 THEN
                        ROUND(COALESCE(SUM(i.payment_amount), 0) / pfb.phase_fee_usd * 100, 1)
                    ELSE 0
                END as percentage_paid
            FROM project_fee_breakdown pfb
            LEFT JOIN invoices i ON pfb.breakdown_id = i.breakdown_id
            WHERE pfb.project_code = ?
            GROUP BY pfb.breakdown_id
            ORDER BY
                CASE pfb.scope
                    WHEN 'indian-brasserie' THEN 1
                    WHEN 'mediterranean-restaurant' THEN 2
                    WHEN 'day-club' THEN 3
                    ELSE 4
                END,
                pfb.discipline,
                CASE pfb.phase
                    WHEN 'Mobilization' THEN 1
                    WHEN 'Conceptual Design' THEN 2
                    WHEN 'Design Development' THEN 3
                    WHEN 'Construction Documents' THEN 4
                    WHEN 'Construction Observation' THEN 5
                    ELSE 6
                END
        """, (project_code,))

        breakdowns = [dict(row) for row in cursor.fetchall()]

        # Calculate totals
        total_breakdown_fee = sum(b.get('phase_fee_usd', 0) or 0 for b in breakdowns)
        total_invoiced = sum(b.get('total_invoiced', 0) or 0 for b in breakdowns)
        total_paid = sum(b.get('total_paid', 0) or 0 for b in breakdowns)

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "project_title": project_info.get('project_title'),
            "contract_value": project_info.get('total_fee_usd', 0),
            "breakdowns": breakdowns,
            "summary": {
                "total_breakdown_fee": total_breakdown_fee,
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "total_outstanding": total_invoiced - total_paid,
                "remaining_to_invoice": total_breakdown_fee - total_invoiced,
                "percentage_invoiced": round(total_invoiced / total_breakdown_fee * 100, 1) if total_breakdown_fee > 0 else 0,
                "percentage_paid": round(total_paid / total_breakdown_fee * 100, 1) if total_breakdown_fee > 0 else 0
            },
            "count": len(breakdowns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_code}/fee-breakdown/check-duplicate")
async def check_duplicate_fee_breakdown(
    project_code: str,
    scope: Optional[str] = Query(None),
    discipline: str = Query(...),
    phase: str = Query(...)
):
    """Check if a fee breakdown already exists for the given project/scope/discipline/phase"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query to check for duplicate
        if scope:
            cursor.execute("""
                SELECT breakdown_id, scope, discipline, phase, phase_fee_usd, percentage_of_total
                FROM project_fee_breakdown
                WHERE project_code = ? AND scope = ? AND discipline = ? AND phase = ?
            """, (project_code, scope, discipline, phase))
        else:
            cursor.execute("""
                SELECT breakdown_id, scope, discipline, phase, phase_fee_usd, percentage_of_total
                FROM project_fee_breakdown
                WHERE project_code = ? AND (scope IS NULL OR scope = '') AND discipline = ? AND phase = ?
            """, (project_code, discipline, phase))

        existing = cursor.fetchone()
        conn.close()

        if existing:
            return {
                "exists": True,
                "existing_breakdown": dict(existing)
            }
        return {"exists": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/active")
async def get_active_projects():
    """Get all active projects (where first payment received) with invoice data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get projects with ACTUAL invoice totals calculated in SQL
        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown') as client_name,
                p.total_fee_usd as contract_value,
                p.status,
                p.current_phase as current_phase,
                p.project_id as project_id,
                COALESCE(SUM(i.invoice_amount), 0) as total_invoiced,
                COALESCE(SUM(i.payment_amount), 0) as paid_to_date_usd,
                (p.total_fee_usd - COALESCE(SUM(i.payment_amount), 0)) as outstanding_usd,
                CASE
                    WHEN p.total_fee_usd > 0 THEN
                        ROUND((COALESCE(SUM(i.invoice_amount), 0) / p.total_fee_usd * 100), 1)
                    ELSE 0
                END as percentage_invoiced
            FROM projects p
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            LEFT JOIN invoices i ON p.project_id = i.project_id
            WHERE p.is_active_project = 1 OR p.status IN ('active', 'active_project', 'Active')
            GROUP BY p.project_id, p.project_code, p.project_title, pr.client_company,
                     p.total_fee_usd, p.status, p.current_phase
            ORDER BY p.project_code DESC
        """)

        projects = []
        for row in cursor.fetchall():
            project = dict(row)
            project_code = project['project_code']

            # Get detailed invoice data for this project
            try:
                invoices = invoice_service.get_invoices_by_project(project_code)
            except:
                invoices = []

            # Find most recent invoice
            if invoices:
                last_invoice = max(invoices, key=lambda x: x.get('invoice_date') or '')
            else:
                last_invoice = None

            project['last_invoice'] = last_invoice
            # Note: total_invoiced and total_paid already calculated in SQL query above
            contract_value = project.get('contract_value') or 0
            total_invoiced = project.get('total_invoiced') or 0
            total_paid = project.get('paid_to_date_usd') or 0
            project['remaining_value'] = contract_value - total_invoiced
            project['invoice_history'] = invoices

            # Determine payment status
            if total_paid > 0:
                if total_invoiced > total_paid:
                    project['payment_status'] = 'outstanding'
                else:
                    project['payment_status'] = 'paid'
            else:
                project['payment_status'] = 'pending'

            projects.append(project)

        conn.close()

        return {
            "data": projects,
            "count": len(projects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_code}/financial-summary")
async def get_project_financial_summary(project_code: str):
    """Get financial summary for a project"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get project details
        cursor.execute("""
            SELECT project_code, project_title, client_name, contract_value
            FROM projects
            WHERE project_code = ?
        """, (project_code,))
        
        project_row = cursor.fetchone()
        if not project_row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")
        
        project = dict(project_row)
        
        # Get invoice data
        invoices = invoice_service.get_invoices_by_project(project_code)
        
        total_invoiced = sum(inv.get('amount_usd', 0) for inv in invoices)
        total_paid = sum(inv.get('payment_amount_usd', 0) for inv in invoices if inv.get('status') == 'paid')
        total_outstanding = total_invoiced - total_paid
        
        conn.close()
        
        return {
            "success": True,
            "project_code": project_code,
            "project_title": project.get('project_title'),
            "client_name": project.get('client_name'),
            "contract_value": project.get('contract_value', 0),
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "remaining_to_invoice": project.get('contract_value', 0) - total_invoiced,
            "invoices": invoices
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== End Invoice Management ====================


class NaturalLanguageQueryRequest(BaseModel):
    """Request model for natural language queries"""
    question: str = Field(..., description="Natural language question about the database")
    use_ai: bool = Field(True, description="Whether to use AI (True) or pattern matching (False)")


class ConversationMessage(BaseModel):
    """A single message in the conversation history"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    results_count: Optional[int] = Field(None, description="Number of results if applicable")
    sql: Optional[str] = Field(None, description="SQL query if applicable")


class ChatQueryRequest(BaseModel):
    """Request model for context-aware chat queries"""
    question: str = Field(..., description="Current question")
    conversation_history: List[ConversationMessage] = Field(default=[], description="Previous conversation messages")
    use_ai: bool = Field(True, description="Whether to use AI")


@app.post("/api/query/ask")
async def ask_natural_language_question(request: NaturalLanguageQueryRequest):
    """
    Ask a natural language question about the database.

    Uses GPT-4o to understand the question and generate appropriate SQL queries.

    Examples:
    - "What projects have we not contacted in over 30 days?"
    - "Show me all RFIs for BK-069"
    - "Which proposals have low health scores?"
    - "Find all emails about contracts from this month"
    """
    try:
        result = query_service.query(request.question, use_ai=request.use_ai)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/ask")
async def ask_natural_language_question_get(
    q: str = Query(..., description="Natural language question"),
    use_ai: bool = Query(True, description="Use AI (True) or pattern matching (False)")
):
    """
    Ask a natural language question about the database (GET method).

    Same as POST /api/query/ask but using GET for simpler frontend integration.

    Example: /api/query/ask?q=Show me all proposals from 2024
    """
    try:
        result = query_service.query(q, use_ai=use_ai)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/examples")
async def get_query_examples():
    """Get example queries to show users"""
    return {
        "examples": query_service.get_query_suggestions(),
        "ai_enabled": query_service.ai_enabled
    }


@app.post("/api/query/chat")
async def chat_query_with_context(request: ChatQueryRequest):
    """
    Ask a natural language question with conversation context.

    This endpoint supports follow-up questions by including previous
    conversation history. The AI uses context from previous queries
    to understand relative references like "those projects" or "what's the total?".

    Examples:
    - First: "Show me all active projects in Thailand"
    - Follow-up: "What's the total contract value?" (uses Thailand context)
    - Follow-up: "How many are behind schedule?" (still using Thailand context)
    """
    try:
        # Build context string from conversation history
        context_parts = []
        for msg in request.conversation_history[-5:]:  # Last 5 messages for context
            role_label = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{role_label}: {msg.content}")
            if msg.sql:
                context_parts.append(f"  (SQL: {msg.sql[:200]}...)" if len(msg.sql) > 200 else f"  (SQL: {msg.sql})")
            if msg.results_count is not None:
                context_parts.append(f"  (Found {msg.results_count} results)")

        # Use the query service with context
        result = query_service.query_with_context(
            question=request.question,
            conversation_context="\n".join(context_parts) if context_parts else None,
            use_ai=request.use_ai
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PATTERN-ENHANCED QUERY ENDPOINTS
# ============================================================================

@app.post("/api/query/ask-enhanced")
async def enhanced_query_with_patterns(
    question: str = Query(..., description="Natural language question"),
    use_patterns: bool = Query(True, description="Whether to use learned patterns")
):
    """
    Ask a natural language question using pattern-enhanced query generation.

    This endpoint uses learned patterns from previous corrections to improve
    SQL generation accuracy. It includes hints from the AI Learning System.

    Example: /api/query/ask-enhanced?question=Show me all active projects
    """
    try:
        if use_patterns:
            result = query_service.query_with_patterns(question)
        else:
            result = query_service.query(question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class QueryFeedbackRequest(BaseModel):
    question: str
    original_sql: str
    was_correct: bool
    corrected_sql: Optional[str] = None
    correction_reason: Optional[str] = None


@app.post("/api/query/feedback")
async def submit_query_feedback(request: QueryFeedbackRequest):
    """
    Submit feedback on a query result to help the AI learn.

    Use this endpoint to:
    1. Mark a query result as correct (positive feedback)
    2. Mark a query result as incorrect and provide corrections (for learning)

    The feedback is stored and used to generate hints for future queries.
    """
    try:
        result = query_service.record_query_feedback(
            question=request.question,
            original_sql=request.original_sql,
            was_correct=request.was_correct,
            corrected_sql=request.corrected_sql,
            correction_reason=request.correction_reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/intelligent-suggestions")
async def get_intelligent_query_suggestions(
    partial_query: str = Query("", description="Partial query for suggestions")
):
    """
    Get intelligent query suggestions based on learned patterns and history.

    Returns suggestions from:
    1. Learned patterns (most reliable queries)
    2. Recent successful queries
    3. Default example queries

    Use the partial_query parameter to filter suggestions as the user types.
    """
    try:
        suggestions = query_service.get_intelligent_suggestions(partial_query)
        return {
            "success": True,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/stats")
async def get_query_learning_stats():
    """
    Get statistics about query learning and pattern usage.

    Returns:
    - Number of active query patterns
    - Total feedback received
    - Query accuracy rate
    """
    try:
        stats = query_service.get_query_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROPOSAL INTELLIGENCE ENDPOINTS
# ============================================================================

@app.get("/api/intelligence/proposal/{project_code}")
async def get_proposal_intelligence(project_code: str):
    """
    Get comprehensive intelligence context for a proposal.

    Returns:
    - Proposal details with email/engagement metrics
    - Recent emails with AI summaries
    - Attachments
    - Status history
    - AI-generated summary of current state
    """
    try:
        result = proposal_intelligence_service.get_proposal_context(project_code)
        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('error', 'Not found'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/intelligence/attention")
async def get_proposals_needing_attention():
    """
    Get proposals that need attention (urgent, action needed, or follow-up).

    Returns proposals ordered by urgency:
    1. Urgent (has urgent emails)
    2. Action needed (has emails requiring action)
    3. Follow-up needed (no contact > 14 days)
    """
    try:
        proposals = proposal_intelligence_service.get_proposals_needing_attention()
        return {
            "success": True,
            "count": len(proposals),
            "proposals": proposals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GenerateEmailRequest(BaseModel):
    project_code: str
    tone: str = "professional"  # professional, friendly, urgent
    purpose: str = "follow_up"  # follow_up, check_status, schedule_meeting, send_update


@app.post("/api/intelligence/generate-email")
async def generate_follow_up_email(request: GenerateEmailRequest):
    """
    Generate a draft follow-up email based on proposal context.

    Uses AI to analyze email history and generate an appropriate
    follow-up email with proper tone and context.
    """
    try:
        result = proposal_intelligence_service.generate_follow_up_email(
            project_code=request.project_code,
            tone=request.tone,
            purpose=request.purpose
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AskQuestionRequest(BaseModel):
    question: str
    project_code: Optional[str] = None


@app.post("/api/intelligence/ask")
async def ask_proposal_question(request: AskQuestionRequest):
    """
    Ask a natural language question about proposals.

    If project_code is provided, focuses on that specific proposal.
    Otherwise, answers questions about all proposals.

    Examples:
    - "What's the status of Sabrah?"
    - "Which proposals need follow-up?"
    - "When was our last contact with Ritz Carlton?"
    """
    try:
        result = proposal_intelligence_service.answer_proposal_question(
            question=request.question,
            project_code=request.project_code
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/intelligence/weekly-summary")
async def get_weekly_summary():
    """
    Get a weekly summary of proposal activity.

    Returns:
    - Active proposals this week
    - Email statistics
    - Proposals needing attention
    """
    try:
        result = proposal_intelligence_service.get_weekly_summary()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AI LEARNING SYSTEM ENDPOINTS
# Human feedback loop for continuous AI improvement
# ============================================================================

class SuggestionAction(BaseModel):
    """Model for suggestion review actions"""
    reviewed_by: str
    notes: Optional[str] = None
    correction_data: Optional[Dict[str, Any]] = None


class TeachPatternRequest(BaseModel):
    """Model for teaching the AI new patterns"""
    pattern_name: str
    pattern_type: str  # 'client_preference', 'business_rule', etc.
    condition: Dict[str, Any]
    action: Dict[str, Any]
    taught_by: str


@app.get("/api/learning/suggestions")
async def get_pending_suggestions(
    limit: int = Query(20, ge=1, le=100),
    suggestion_type: Optional[str] = None,
    priority: Optional[str] = None
):
    """
    Get pending AI suggestions for human review.

    Returns suggestions the AI has generated that need approval/rejection.
    """
    try:
        suggestions = ai_learning_service.get_pending_suggestions(
            limit=limit,
            suggestion_type=suggestion_type,
            priority=priority
        )
        return {"success": True, "suggestions": suggestions, "count": len(suggestions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/suggestions/{suggestion_id}/approve")
async def approve_suggestion(suggestion_id: int, action: SuggestionAction):
    """
    Approve an AI suggestion and optionally apply changes.

    This also records the approval as training feedback.
    """
    try:
        result = ai_learning_service.approve_suggestion(
            suggestion_id=suggestion_id,
            reviewed_by=action.reviewed_by,
            apply_changes=True
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/suggestions/{suggestion_id}/reject")
async def reject_suggestion(suggestion_id: int, action: SuggestionAction):
    """
    Reject an AI suggestion.

    This records the rejection as training feedback to improve future suggestions.
    """
    try:
        result = ai_learning_service.reject_suggestion(
            suggestion_id=suggestion_id,
            reviewed_by=action.reviewed_by,
            reason=action.notes or "Rejected"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/suggestions/{suggestion_id}/modify")
async def modify_suggestion(suggestion_id: int, action: SuggestionAction):
    """
    Approve a suggestion with modifications.

    This is the most valuable feedback - it teaches the AI what was wrong
    and what the correct answer should have been.
    """
    try:
        if not action.correction_data:
            raise HTTPException(status_code=400, detail="correction_data required for modifications")

        result = ai_learning_service.modify_suggestion(
            suggestion_id=suggestion_id,
            reviewed_by=action.reviewed_by,
            correction_data=action.correction_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/scan-emails")
async def scan_emails_for_suggestions(
    hours: int = Query(168, ge=1, le=720, description="Hours of emails to scan"),
    limit: int = Query(50, ge=1, le=200, description="Max emails to process")
):
    """
    Scan recent emails and generate AI suggestions.

    This triggers the AI to analyze emails and create suggestions for:
    - New contacts detected
    - Follow-up reminders needed
    - Fee changes mentioned
    - Deadlines mentioned
    - Missing data detected
    """
    try:
        result = ai_learning_service.process_recent_emails_for_suggestions(
            hours=hours,
            limit=limit
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/teach-pattern")
async def teach_pattern(request: TeachPatternRequest):
    """
    Directly teach the AI a new pattern.

    Example: "When client_type is 'luxury', always use formal tone"
    """
    try:
        result = ai_learning_service.teach_pattern(
            pattern_name=request.pattern_name,
            pattern_type=request.pattern_type,
            condition=request.condition,
            action=request.action,
            taught_by=request.taught_by
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/patterns")
async def get_learned_patterns(
    pattern_type: Optional[str] = None,
    active_only: bool = True
):
    """
    Get all learned patterns.

    Shows what the AI has learned from human feedback.
    """
    try:
        patterns = ai_learning_service.get_learned_patterns(
            pattern_type=pattern_type,
            active_only=active_only
        )
        return {"success": True, "patterns": patterns, "count": len(patterns)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/stats")
async def get_learning_stats():
    """
    Get statistics on AI learning progress.

    Shows how many suggestions have been reviewed, accuracy rate, etc.
    """
    try:
        stats = ai_learning_service.get_learning_stats()
        return {"success": True, **stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/generate-rules")
async def generate_rules_from_feedback(
    min_evidence: int = Query(3, ge=1, le=10, description="Minimum corrections needed to create a rule")
):
    """
    Analyze accumulated human feedback and automatically generate learned patterns.

    This is the core of the learning system - it finds patterns in human
    corrections and creates rules that improve future AI behavior.
    """
    try:
        result = ai_learning_service.generate_rules_from_feedback(min_evidence)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/validate-patterns")
async def validate_learned_patterns(
    test_limit: int = Query(50, ge=10, le=200, description="Number of test cases")
):
    """
    Test learned patterns against recent suggestions to validate accuracy.

    Returns validation metrics showing if patterns are still effective.
    """
    try:
        result = ai_learning_service.validate_patterns(test_limit)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/decay-patterns")
async def decay_unused_patterns(
    days_threshold: int = Query(30, ge=7, le=90, description="Days before pattern confidence decays")
):
    """
    Reduce confidence of patterns that haven't been validated recently.

    Prevents stale patterns from over-influencing the system.
    """
    try:
        affected = ai_learning_service.decay_unused_patterns(days_threshold)
        return {"success": True, "patterns_decayed": affected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/check-suppression")
async def check_suggestion_suppression(
    suggestion_type: str = Query(..., description="Type of suggestion to check"),
    project_code: Optional[str] = Query(None, description="Project code to check")
):
    """
    Check if a suggestion type should be suppressed based on learned patterns.

    Used to preview what suggestions would be blocked.
    """
    try:
        should_suppress = ai_learning_service.should_suppress_suggestion(suggestion_type, project_code)
        return {"success": True, "should_suppress": should_suppress, "suggestion_type": suggestion_type, "project_code": project_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FOLLOW-UP AGENT ENDPOINTS
# ============================================================================

@app.get("/api/agent/follow-up/proposals")
async def get_proposals_needing_followup(
    days_threshold: int = Query(14, ge=1, le=90, description="Days since last contact"),
    include_analysis: bool = Query(True, description="Include detailed analysis"),
    limit: int = Query(50, ge=1, le=200, description="Max proposals to return")
):
    """
    Get all proposals that need follow-up with intelligent analysis.

    Returns proposals sorted by priority score with communication history,
    sentiment analysis, and recommended follow-up approach.
    """
    try:
        proposals = follow_up_agent.get_proposals_needing_followup(
            days_threshold=days_threshold,
            include_analysis=include_analysis,
            limit=limit
        )
        return {"success": True, "proposals": proposals, "count": len(proposals)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/follow-up/summary")
async def get_follow_up_summary():
    """
    Get summary of follow-up status across all proposals.

    Shows total active proposals, value at risk, urgency breakdown,
    and top priority proposals.
    """
    try:
        summary = follow_up_agent.get_follow_up_summary()
        return {"success": True, **summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/follow-up/draft/{proposal_id}")
async def draft_follow_up_email(
    proposal_id: int,
    tone: str = Query("professional", description="Email tone: professional, casual, formal")
):
    """
    Draft a personalized follow-up email using AI.

    Analyzes communication history and learned patterns to generate
    an appropriate follow-up email for the proposal.
    """
    try:
        draft = follow_up_agent.draft_follow_up_email(
            proposal_id=proposal_id,
            tone=tone,
            include_context=True
        )
        return {"success": True, **draft}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/follow-up/run-daily")
async def run_daily_follow_up_analysis():
    """
    Run daily follow-up analysis for all proposals.

    Identifies new proposals needing follow-up, generates suggestions,
    and drafts emails for critical cases.
    """
    try:
        results = follow_up_agent.run_daily_analysis()
        return {"success": True, **results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTRACT IMPORT STAGING ENDPOINTS
# ============================================================================

@app.post("/api/contracts/stage")
async def stage_contract_import(request: StageContractRequest):
    """
    Stage a contract import for review before committing to database.

    This allows reviewing all changes and editing before final approval.
    """
    try:
        contract_data = {
            'client_name': request.client_name,
            'total_fee': request.total_fee,
            'contract_duration': request.contract_duration,
            'contract_date': request.contract_date,
            'payment_terms': request.payment_terms,
            'late_interest': request.late_interest,
            'stop_work_days': request.stop_work_days,
            'restart_fee': request.restart_fee,
            'notes': request.notes,
            'pdf_source_path': request.pdf_source_path,
            'fee_breakdown': request.fee_breakdown or []
        }

        result = contract_service.stage_contract_import(
            request.project_code,
            contract_data,
            request.imported_by
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contracts/pending")
async def list_pending_imports(limit: int = Query(50, description="Max imports to return")):
    """Get all pending contract imports awaiting approval"""
    try:
        imports = contract_service.list_pending_imports(limit)
        return {"imports": imports, "count": len(imports)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contracts/pending/{import_id}")
async def get_staged_import(import_id: str):
    """Get full details of a specific staged import"""
    try:
        staged = contract_service.get_staged_import(import_id)
        if not staged:
            raise HTTPException(status_code=404, detail=f"Import {import_id} not found")
        return staged
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/contracts/pending/{import_id}/approve")
async def approve_import(import_id: str, request: ApproveImportRequest):
    """Approve a staged import and commit to production database"""
    try:
        result = contract_service.approve_import(
            import_id,
            request.approved_by,
            request.notes
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/contracts/pending/{import_id}/reject")
async def reject_import(import_id: str, request: RejectImportRequest):
    """Reject a staged import"""
    try:
        result = contract_service.reject_import(
            import_id,
            request.rejected_by,
            request.reason
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/contracts/pending/{import_id}")
async def edit_staged_import(import_id: str, request: EditStagedImportRequest):
    """Edit a staged import before approval"""
    try:
        result = contract_service.edit_staged_import(
            import_id,
            request.updates,
            request.edited_by
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROPOSAL TRACKER ENDPOINTS
# ============================================================================

@app.get("/api/proposal-tracker/stats")
async def get_proposal_tracker_stats():
    """Get proposal tracker statistics and overview"""
    try:
        stats = proposal_tracker_service.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proposal-tracker/list")
async def get_proposal_tracker_list(
    status: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    discipline: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
):
    """Get paginated proposal list with filters"""
    try:
        result = proposal_tracker_service.get_proposals_list(
            status=status,
            country=country,
            search=search,
            discipline=discipline,
            page=page,
            per_page=per_page
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proposal-tracker/disciplines")
async def get_proposal_tracker_disciplines():
    """Get proposal counts and values by discipline for filter dropdown"""
    try:
        disciplines = proposal_tracker_service.get_discipline_stats()
        return {"success": True, "disciplines": disciplines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proposal-tracker/countries")
async def get_proposal_tracker_countries():
    """Get unique list of countries for filtering"""
    try:
        countries = proposal_tracker_service.get_countries_list()
        return {"success": True, "countries": countries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proposal-tracker/{project_code}")
async def get_proposal_by_code(project_code: str):
    """Get single proposal details by project code"""
    try:
        proposal = proposal_tracker_service.get_proposal_by_code(project_code)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        return {"success": True, "proposal": proposal}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ProposalUpdateRequest(BaseModel):
    project_title: Optional[str] = None
    project_value: Optional[float] = None
    country: Optional[str] = None
    current_status: Optional[str] = None
    current_remark: Optional[str] = None
    project_summary: Optional[str] = None
    waiting_on: Optional[str] = None
    next_steps: Optional[str] = None
    proposal_sent_date: Optional[str] = None
    first_contact_date: Optional[str] = None
    proposal_sent: Optional[int] = None

    # Provenance tracking fields
    updated_by: Optional[str] = None
    source_type: Optional[str] = None  # 'manual', 'ai', 'email_parser', 'import'
    change_reason: Optional[str] = None


@app.put("/api/proposal-tracker/{project_code}")
async def update_proposal(project_code: str, request: ProposalUpdateRequest):
    """Update proposal fields"""
    try:
        updates = request.dict(exclude_unset=True)
        result = proposal_tracker_service.update_proposal(project_code, updates)

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proposal-tracker/{project_code}/history")
async def get_proposal_status_history(project_code: str):
    """Get status change history for a proposal"""
    try:
        history = proposal_tracker_service.get_status_history(project_code)
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proposal-tracker/{project_code}/emails")
async def get_proposal_email_intelligence(project_code: str):
    """Get AI-extracted email intelligence for a proposal"""
    try:
        emails = proposal_tracker_service.get_email_intelligence(project_code)
        return {"success": True, "emails": emails}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/proposal-tracker/generate-pdf")
async def generate_proposal_pdf():
    """Trigger PDF report generation"""
    try:
        result = proposal_tracker_service.trigger_pdf_generation()

        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('message'))

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRAINING / FEEDBACK ENDPOINTS (RLHF System)
# ============================================================================

class FeedbackRequest(BaseModel):
    """Request model for RLHF feedback"""
    feature_type: str = Field(..., description="Type of feature (e.g., 'kpi_outstanding_invoices', 'email_category')")
    feature_id: str = Field(..., description="ID of the feature instance")
    helpful: bool = Field(..., description="True if helpful, False if not")
    issue_type: Optional[str] = Field(None, description="Comma-separated list of issue types")
    feedback_text: Optional[str] = Field(None, description="REQUIRED explanation if helpful=False")
    expected_value: Optional[str] = Field(None, description="What user expected to see")
    current_value: Optional[str] = Field(None, description="What system actually shows")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")


@app.post("/api/training/feedback")
async def log_user_feedback(request: FeedbackRequest):
    """Log user feedback for RLHF training"""
    try:
        result = training_data_service.log_feedback(
            feature_type=request.feature_type,
            feature_id=request.feature_id,
            helpful=request.helpful,
            issue_type=request.issue_type,
            feedback_text=request.feedback_text,
            expected_value=request.expected_value,
            current_value=request.current_value,
            context=request.context
        )

        return result
    except ValueError as e:
        # This will catch the "feedback_text is REQUIRED when helpful=False" error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to log feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/training/feedback/stats")
async def get_feedback_statistics(
    feature_type: Optional[str] = Query(None, description="Filter by feature type"),
    days: int = Query(30, description="Number of days to look back")
):
    """Get feedback statistics"""
    try:
        return training_data_service.get_feedback_stats(feature_type=feature_type, days=days)
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/training/feedback/recent")
async def get_recent_feedback(
    feature_type: Optional[str] = Query(None, description="Filter by feature type"),
    helpful: Optional[bool] = Query(None, description="Filter by helpful status"),
    limit: int = Query(50, description="Max number to return")
):
    """Get recent feedback entries for review"""
    try:
        feedback = training_data_service.get_recent_feedback(
            feature_type=feature_type,
            helpful=helpful,
            limit=limit
        )
        return {
            "success": True,
            "feedback": feedback,
            "count": len(feedback)
        }
    except Exception as e:
        logger.error(f"Failed to get recent feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MANUAL DATA ENTRY ENDPOINTS - Projects, Invoices, Phase Fees
# ============================================================================

class CreateProjectRequest(BaseModel):
    """Request to create a new project"""
    project_code: str = Field(..., description="Project code (e.g. 25 BK-001)")
    project_title: str = Field(..., description="Project name/title")
    total_fee_usd: Optional[float] = Field(None, description="Total project fee in USD")
    status: Optional[str] = Field("active", description="Project status")
    is_active_project: int = Field(1, description="1 for active project, 0 for proposal")
    contract_signed_date: Optional[str] = Field(None, description="Contract signing date (YYYY-MM-DD)")
    country: Optional[str] = Field(None, description="Country")
    city: Optional[str] = Field(None, description="City")
    notes: Optional[str] = Field(None, description="Project notes")


class UpdateProjectRequest(BaseModel):
    """Request to update an existing project"""
    project_title: Optional[str] = Field(None, description="Project name/title")
    total_fee_usd: Optional[float] = Field(None, description="Total project fee in USD")
    status: Optional[str] = Field(None, description="Project status")
    is_active_project: Optional[int] = Field(None, description="1 for active project, 0 for proposal")
    contract_signed_date: Optional[str] = Field(None, description="Contract signing date")
    country: Optional[str] = Field(None, description="Country")
    city: Optional[str] = Field(None, description="City")
    notes: Optional[str] = Field(None, description="Project notes")
    contract_term_months: Optional[int] = Field(None, description="Contract term in months")
    team_lead: Optional[str] = Field(None, description="Project team lead")
    current_phase: Optional[str] = Field(None, description="Current project phase")
    target_completion: Optional[str] = Field(None, description="Target completion date")
    # Contract terms
    payment_due_days: Optional[int] = Field(None, description="Days until payment is due after invoice")
    payment_terms: Optional[str] = Field(None, description="Payment terms text")
    late_payment_interest_rate: Optional[float] = Field(None, description="Late payment interest rate")


class CreateInvoiceRequest(BaseModel):
    """Request to create a new invoice"""
    project_code: str = Field(..., description="Project code to link invoice to")
    breakdown_id: Optional[str] = Field(None, description="Phase/discipline breakdown ID to link this invoice to")
    invoice_number: str = Field(..., description="Invoice number (e.g. I25-001)")
    invoice_date: Optional[str] = Field(None, description="Invoice date (YYYY-MM-DD)")
    invoice_amount: float = Field(..., description="Invoice amount in USD")
    payment_date: Optional[str] = Field(None, description="Payment date (YYYY-MM-DD)")
    payment_amount: Optional[float] = Field(None, description="Amount paid")
    status: str = Field("outstanding", description="Invoice status (paid, outstanding, pending)")
    description: Optional[str] = Field(None, description="Invoice description (e.g. 'Interior - Concept Design')")


class UpdateInvoiceRequest(BaseModel):
    """Request to update an existing invoice"""
    breakdown_id: Optional[str] = Field(None, description="Phase/discipline breakdown ID")
    invoice_date: Optional[str] = Field(None, description="Invoice date")
    invoice_amount: Optional[float] = Field(None, description="Invoice amount")
    payment_date: Optional[str] = Field(None, description="Payment date")
    payment_amount: Optional[float] = Field(None, description="Amount paid")
    status: Optional[str] = Field(None, description="Invoice status")
    description: Optional[str] = Field(None, description="Invoice description")


class CreatePhaseFeeRequest(BaseModel):
    """Request to add a phase fee breakdown entry"""
    project_code: str = Field(..., description="Project code")
    discipline: str = Field(..., description="Discipline (Landscape, Architectural, Interior)")
    phase: str = Field(..., description="Phase name (e.g. 'Concept Design', 'Construction Documents')")
    phase_fee_usd: float = Field(..., description="Phase fee in USD")
    percentage_of_total: Optional[float] = Field(None, description="Percentage of total project fee")


class UpdatePhaseFeeRequest(BaseModel):
    """Request to update a phase fee breakdown entry"""
    phase_fee_usd: Optional[float] = Field(None, description="Phase fee in USD")
    percentage_of_total: Optional[float] = Field(None, description="Percentage of total fee")


@app.post("/api/projects")
async def create_project(request: CreateProjectRequest):
    """Create a new project manually"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if project code already exists
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (request.project_code,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail=f"Project {request.project_code} already exists")

        # Insert new project
        cursor.execute("""
            INSERT INTO projects (
                project_code, project_title, total_fee_usd, status,
                is_active_project, contract_signed_date, country, city, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.project_code,
            request.project_title,
            request.total_fee_usd,
            request.status,
            request.is_active_project,
            request.contract_signed_date,
            request.country,
            request.city,
            request.notes
        ))

        project_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Project {request.project_code} created successfully",
            "project_id": project_id,
            "project_code": request.project_code
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_code}")
async def get_project(project_code: str):
    """Get a single project by project code"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch project
        cursor.execute("""
            SELECT * FROM projects WHERE project_code = ?
        """, (project_code,))

        project = cursor.fetchone()
        conn.close()

        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        return {
            "success": True,
            "project": dict(project)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/projects/{project_code}")
async def update_project(project_code: str, request: UpdateProjectRequest):
    """Update an existing project"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if project exists
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_id = project[0]

        # Build dynamic UPDATE query for projects table
        updates = []
        values = []

        if request.project_title is not None:
            updates.append("project_title = ?")
            values.append(request.project_title)
        if request.total_fee_usd is not None:
            updates.append("total_fee_usd = ?")
            values.append(request.total_fee_usd)
        if request.status is not None:
            updates.append("status = ?")
            values.append(request.status)
        if request.is_active_project is not None:
            updates.append("is_active_project = ?")
            values.append(request.is_active_project)
        if request.contract_signed_date is not None:
            updates.append("contract_signed_date = ?")
            values.append(request.contract_signed_date)
        if request.country is not None:
            updates.append("country = ?")
            values.append(request.country)
        if request.city is not None:
            updates.append("city = ?")
            values.append(request.city)
        if request.notes is not None:
            updates.append("notes = ?")
            values.append(request.notes)
        if request.contract_term_months is not None:
            updates.append("contract_term_months = ?")
            values.append(request.contract_term_months)
        if request.team_lead is not None:
            updates.append("team_lead = ?")
            values.append(request.team_lead)
        if request.current_phase is not None:
            updates.append("current_phase = ?")
            values.append(request.current_phase)
        if request.target_completion is not None:
            updates.append("target_completion = ?")
            values.append(request.target_completion)

        if updates:
            # Execute update on projects table
            values.append(project_code)
            query = f"UPDATE projects SET {', '.join(updates)} WHERE project_code = ?"
            cursor.execute(query, values)

        # Handle contract_metadata table for contract terms
        has_contract_fields = any([
            request.payment_due_days is not None,
            request.payment_terms is not None,
            request.late_payment_interest_rate is not None
        ])

        if has_contract_fields:
            # Check if contract_metadata exists for this project
            cursor.execute("SELECT contract_id FROM contract_metadata WHERE project_id = ?", (project_id,))
            contract_meta = cursor.fetchone()

            if contract_meta:
                # Update existing contract_metadata
                contract_updates = []
                contract_values = []

                if request.payment_due_days is not None:
                    contract_updates.append("payment_due_days = ?")
                    contract_values.append(request.payment_due_days)
                if request.payment_terms is not None:
                    contract_updates.append("payment_terms = ?")
                    contract_values.append(request.payment_terms)
                if request.late_payment_interest_rate is not None:
                    contract_updates.append("late_payment_interest_rate = ?")
                    contract_values.append(request.late_payment_interest_rate)

                contract_values.append(project_id)
                query = f"UPDATE contract_metadata SET {', '.join(contract_updates)} WHERE project_id = ?"
                cursor.execute(query, contract_values)
            else:
                # Insert new contract_metadata
                cursor.execute("""
                    INSERT INTO contract_metadata (project_id, payment_due_days, payment_terms, late_payment_interest_rate)
                    VALUES (?, ?, ?, ?)
                """, (
                    project_id,
                    request.payment_due_days or 30,
                    request.payment_terms,
                    request.late_payment_interest_rate
                ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Project {project_code} updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/invoices")
async def create_invoice(request: CreateInvoiceRequest):
    """Create a new invoice manually"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get project_id from project_code
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (request.project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {request.project_code} not found")

        project_id = project[0]

        # Note: invoice_number is NOT unique - same invoice can have multiple entries for different phases/disciplines
        # Check if this exact combination already exists
        if request.breakdown_id:
            cursor.execute("""
                SELECT invoice_id FROM invoices
                WHERE invoice_number = ? AND breakdown_id = ?
            """, (request.invoice_number, request.breakdown_id))
            if cursor.fetchone():
                conn.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"Invoice {request.invoice_number} already exists for this phase/discipline"
                )

        # Insert new invoice
        cursor.execute("""
            INSERT INTO invoices (
                project_id, breakdown_id, invoice_number, invoice_date, invoice_amount,
                payment_date, payment_amount, status, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            request.breakdown_id,
            request.invoice_number,
            request.invoice_date,
            request.invoice_amount,
            request.payment_date,
            request.payment_amount,
            request.status,
            request.description
        ))

        invoice_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Invoice {request.invoice_number} created successfully",
            "invoice_id": invoice_id,
            "invoice_number": request.invoice_number
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create invoice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/invoices/{invoice_number}")
async def update_invoice(invoice_number: str, request: UpdateInvoiceRequest):
    """Update an existing invoice"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if invoice exists
        cursor.execute("SELECT invoice_id FROM invoices WHERE invoice_number = ?", (invoice_number,))
        invoice = cursor.fetchone()
        if not invoice:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found")

        # Build dynamic UPDATE query
        updates = []
        values = []

        if request.breakdown_id is not None:
            updates.append("breakdown_id = ?")
            values.append(request.breakdown_id)
        if request.invoice_date is not None:
            updates.append("invoice_date = ?")
            values.append(request.invoice_date)
        if request.invoice_amount is not None:
            updates.append("invoice_amount = ?")
            values.append(request.invoice_amount)
        if request.payment_date is not None:
            updates.append("payment_date = ?")
            values.append(request.payment_date)
        if request.payment_amount is not None:
            updates.append("payment_amount = ?")
            values.append(request.payment_amount)
        if request.status is not None:
            updates.append("status = ?")
            values.append(request.status)
        if request.description is not None:
            updates.append("description = ?")
            values.append(request.description)

        if not updates:
            conn.close()
            return {"success": True, "message": "No changes to apply"}

        # Execute update
        values.append(invoice_number)
        query = f"UPDATE invoices SET {', '.join(updates)} WHERE invoice_number = ?"
        cursor.execute(query, values)

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Invoice {invoice_number} updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update invoice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/phase-fees")
async def create_phase_fee(request: CreatePhaseFeeRequest):
    """Add a new phase fee breakdown entry"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if this exact entry already exists
        cursor.execute("""
            SELECT breakdown_id FROM project_fee_breakdown
            WHERE project_code = ? AND discipline = ? AND phase = ?
        """, (request.project_code, request.discipline, request.phase))

        if cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"Phase fee for {request.project_code} - {request.discipline} - {request.phase} already exists"
            )

        # Insert new phase fee
        cursor.execute("""
            INSERT INTO project_fee_breakdown (
                project_code, discipline, phase, phase_fee_usd, percentage_of_total
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            request.project_code,
            request.discipline,
            request.phase,
            request.phase_fee_usd,
            request.percentage_of_total
        ))

        breakdown_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Phase fee added for {request.project_code} - {request.discipline} - {request.phase}",
            "breakdown_id": breakdown_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create phase fee: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/phase-fees/{breakdown_id}")
async def update_phase_fee(breakdown_id: str, request: UpdatePhaseFeeRequest):
    """Update an existing phase fee breakdown entry"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if breakdown exists
        cursor.execute("SELECT breakdown_id FROM project_fee_breakdown WHERE breakdown_id = ?", (breakdown_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Phase fee breakdown {breakdown_id} not found")

        # Build dynamic UPDATE query
        updates = []
        values = []

        if request.phase_fee_usd is not None:
            updates.append("phase_fee_usd = ?")
            values.append(request.phase_fee_usd)
        if request.percentage_of_total is not None:
            updates.append("percentage_of_total = ?")
            values.append(request.percentage_of_total)

        if not updates:
            conn.close()
            return {"success": True, "message": "No changes to apply"}

        # Execute update
        values.append(breakdown_id)
        query = f"UPDATE project_fee_breakdown SET {', '.join(updates)} WHERE breakdown_id = ?"
        cursor.execute(query, values)

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Phase fee {breakdown_id} updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update phase fee: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MANUAL FINANCIAL DATA ENTRY API ENDPOINTS
# =============================================================================

class ProjectCreateRequest(BaseModel):
    project_code: str
    project_title: str
    total_fee_usd: float
    country: Optional[str] = "Unknown"
    city: Optional[str] = "Unknown"
    status: Optional[str] = "active"


class FeeBreakdownCreateRequest(BaseModel):
    project_code: str
    discipline: str
    phase: str
    phase_fee_usd: float
    percentage_of_total: float


class InvoiceCreateRequest(BaseModel):
    project_code: str
    invoice_number: str
    invoice_date: str
    invoice_amount: float
    payment_date: Optional[str] = None
    payment_amount: Optional[float] = None
    status: Optional[str] = "Outstanding"


@app.post("/api/projects")
async def create_project(request: ProjectCreateRequest):
    """
    Manual entry: Create a new project record
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if project already exists
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (request.project_code,))
        existing = cursor.fetchone()

        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Project {request.project_code} already exists")

        # Insert new project (set is_active_project=1 so it shows in Active Projects)
        cursor.execute("""
            INSERT INTO projects (
                project_code, project_title, total_fee_usd, country, city,
                status, is_active_project, source_type, created_by, date_created
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, 'manual_entry', 'bill', date('now'))
        """, (
            request.project_code,
            request.project_title,
            request.total_fee_usd,
            request.country,
            request.city,
            request.status
        ))

        project_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Created project {request.project_code} manually")

        return {
            "success": True,
            "project_id": project_id,
            "message": f"Project {request.project_code} created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/phase-fees")
async def create_fee_breakdown(request: FeeBreakdownCreateRequest):
    """
    Manual entry: Add phase/discipline fee breakdown
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify project exists
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (request.project_code,))
        project = cursor.fetchone()

        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {request.project_code} not found")

        # Insert fee breakdown
        import uuid
        breakdown_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO project_fee_breakdown (
                breakdown_id, project_code, discipline, phase,
                phase_fee_usd, percentage_of_total,
                payment_status, confirmed_by_user
            )
            VALUES (?, ?, ?, ?, ?, ?, 'pending', 1)
        """, (
            breakdown_id,
            request.project_code,
            request.discipline,
            request.phase,
            request.phase_fee_usd,
            request.percentage_of_total
        ))

        conn.commit()
        conn.close()

        logger.info(f"Created fee breakdown for {request.project_code}: {request.discipline} - {request.phase}")

        return {
            "success": True,
            "breakdown_id": breakdown_id,
            "message": f"Phase breakdown added for {request.project_code}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create fee breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/invoices")
async def create_invoice(request: InvoiceCreateRequest):
    """
    Manual entry: Add invoice and payment information
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get project_id from project_code
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (request.project_code,))
        project = cursor.fetchone()

        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {request.project_code} not found")

        project_id = project[0]

        # Insert invoice
        cursor.execute("""
            INSERT INTO invoices (
                project_id, invoice_number, invoice_date,
                invoice_amount, payment_amount, payment_date,
                status, source_type, created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'manual_entry', 'bill')
        """, (
            project_id,
            request.invoice_number,
            request.invoice_date,
            request.invoice_amount,
            request.payment_amount,
            request.payment_date,
            request.status
        ))

        invoice_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Created invoice {request.invoice_number} for {request.project_code}")

        return {
            "success": True,
            "invoice_id": invoice_id,
            "message": f"Invoice {request.invoice_number} created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create invoice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTACT MANAGEMENT ENDPOINTS
# ============================================================================

class ContactCreateRequest(BaseModel):
    """Request to create a new contact"""
    name: str = Field(..., description="Contact name")
    email: str = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    role: Optional[str] = Field(None, description="Contact role/title")
    client_id: int = Field(..., description="Client ID this contact belongs to")
    notes: Optional[str] = Field(None, description="Additional notes")


class ContactAssignRequest(BaseModel):
    """Request to assign a contact to a project"""
    contact_id: int = Field(..., description="Contact ID to assign")
    is_primary: bool = Field(False, description="Is this the primary contact?")
    role_on_project: Optional[str] = Field(None, description="Role on this project")
    notes: Optional[str] = Field(None, description="Assignment notes")


class ContactAssignmentUpdateRequest(BaseModel):
    """Request to update a contact assignment"""
    is_primary: Optional[bool] = Field(None, description="Is primary contact")
    role_on_project: Optional[str] = Field(None, description="Role on project")
    notes: Optional[str] = Field(None, description="Assignment notes")


@app.get("/api/contacts")
async def get_contacts(client_id: Optional[int] = None):
    """Get all contacts, optionally filtered by client_id"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if client_id:
            cursor.execute("""
                SELECT contact_id, client_id, email, name, role, phone, notes
                FROM contacts
                WHERE client_id = ?
                ORDER BY name
            """, (client_id,))
        else:
            cursor.execute("""
                SELECT contact_id, client_id, email, name, role, phone, notes
                FROM contacts
                ORDER BY name
            """)

        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                "contact_id": row[0],
                "client_id": row[1],
                "email": row[2],
                "name": row[3],
                "role": row[4],
                "phone": row[5],
                "notes": row[6]
            })

        conn.close()
        return {"success": True, "contacts": contacts}
    except Exception as e:
        logger.error(f"Failed to get contacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/contacts")
async def create_contact(request: ContactCreateRequest):
    """Create a new contact"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO contacts (client_id, email, name, role, phone, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.client_id,
            request.email,
            request.name,
            request.role,
            request.phone,
            request.notes
        ))

        contact_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "contact_id": contact_id,
            "message": f"Contact {request.name} created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create contact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_code}/contacts")
async def get_project_contacts(project_code: str):
    """Get all contacts assigned to a project"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get project_id from project_code
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_id = project[0]

        # Get all assigned contacts with assignment details
        cursor.execute("""
            SELECT
                c.contact_id,
                c.name,
                c.email,
                c.phone,
                c.role,
                c.notes as contact_notes,
                pca.assignment_id,
                pca.is_primary,
                pca.role_on_project,
                pca.notes as assignment_notes
            FROM project_contact_assignments pca
            JOIN contacts c ON pca.contact_id = c.contact_id
            WHERE pca.project_id = ?
            ORDER BY pca.is_primary DESC, c.name
        """, (project_id,))

        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                "contact_id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "role": row[4],
                "contact_notes": row[5],
                "assignment_id": row[6],
                "is_primary": bool(row[7]),
                "role_on_project": row[8],
                "assignment_notes": row[9]
            })

        conn.close()
        return {"success": True, "contacts": contacts}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project contacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_code}/contacts")
async def assign_contact_to_project(project_code: str, request: ContactAssignRequest):
    """Assign a contact to a project"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get project_id
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_id = project[0]

        # If this is set as primary, unset any other primary contacts
        if request.is_primary:
            cursor.execute("""
                UPDATE project_contact_assignments
                SET is_primary = 0
                WHERE project_id = ?
            """, (project_id,))

        # Create the assignment
        cursor.execute("""
            INSERT INTO project_contact_assignments
            (project_id, contact_id, is_primary, role_on_project, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (
            project_id,
            request.contact_id,
            request.is_primary,
            request.role_on_project,
            request.notes
        ))

        assignment_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "assignment_id": assignment_id,
            "message": "Contact assigned successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign contact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/projects/{project_code}/contacts/{contact_id}")
async def update_contact_assignment(
    project_code: str,
    contact_id: int,
    request: ContactAssignmentUpdateRequest
):
    """Update a contact assignment"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get project_id
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_id = project[0]

        # If setting as primary, unset other primary contacts
        if request.is_primary:
            cursor.execute("""
                UPDATE project_contact_assignments
                SET is_primary = 0
                WHERE project_id = ? AND contact_id != ?
            """, (project_id, contact_id))

        # Build dynamic UPDATE query
        updates = []
        values = []

        if request.is_primary is not None:
            updates.append("is_primary = ?")
            values.append(request.is_primary)
        if request.role_on_project is not None:
            updates.append("role_on_project = ?")
            values.append(request.role_on_project)
        if request.notes is not None:
            updates.append("notes = ?")
            values.append(request.notes)

        if updates:
            values.extend([project_id, contact_id])
            query = f"UPDATE project_contact_assignments SET {', '.join(updates)} WHERE project_id = ? AND contact_id = ?"
            cursor.execute(query, values)

        conn.commit()
        conn.close()

        return {"success": True, "message": "Assignment updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update assignment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_code}/contacts/{contact_id}")
async def remove_contact_from_project(project_code: str, contact_id: int):
    """Remove a contact from a project"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get project_id
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_id = project[0]

        # Delete the assignment
        cursor.execute("""
            DELETE FROM project_contact_assignments
            WHERE project_id = ? AND contact_id = ?
        """, (project_id, contact_id))

        conn.commit()
        conn.close()

        return {"success": True, "message": "Contact removed from project"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove contact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MEETINGS WIDGET ENDPOINT
# ============================================================================

@app.get("/api/dashboard/meetings")
async def get_upcoming_meetings(limit: int = Query(10, description="Number of meetings to return")):
    """
    Get upcoming meetings extracted from emails

    Returns emails that appear to be meeting invites/discussions
    with extracted date/time information where possible
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get meeting-related emails from recent period
        # Look for emails with meeting/call keywords in subject
        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.sender_name,
                e.date as email_date,
                e.snippet,
                ec.ai_summary,
                ec.key_points,
                epl.project_code,
                p.project_title
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
            LEFT JOIN projects p ON epl.project_code = p.project_code
            WHERE (
                e.subject LIKE '%meeting%' OR
                e.subject LIKE '%call%' OR
                e.subject LIKE '%zoom%' OR
                e.subject LIKE '%teams%' OR
                e.subject LIKE '%kick%off%' OR
                e.subject LIKE '%review%' OR
                e.subject LIKE '%discussion%'
            )
            ORDER BY e.date DESC
            LIMIT ?
        """, (limit,))

        meetings = []
        for row in cursor.fetchall():
            subject = row['subject'] or ''

            # Try to extract meeting type from subject
            meeting_type = 'Meeting'
            if 'call' in subject.lower():
                meeting_type = 'Call'
            elif 'zoom' in subject.lower():
                meeting_type = 'Zoom Call'
            elif 'teams' in subject.lower():
                meeting_type = 'Teams Meeting'
            elif 'kick' in subject.lower():
                meeting_type = 'Kick-off Meeting'
            elif 'review' in subject.lower():
                meeting_type = 'Review Meeting'

            meetings.append({
                'email_id': row['email_id'],
                'subject': subject,
                'meeting_type': meeting_type,
                'sender': row['sender_name'] or row['sender_email'],
                'email_date': row['email_date'],
                'snippet': row['snippet'],
                'ai_summary': row['ai_summary'],
                'project_code': row['project_code'],
                'project_title': row['project_title']
            })

        conn.close()

        # Count by meeting type
        type_counts = {}
        for m in meetings:
            t = m['meeting_type']
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            'success': True,
            'meetings': meetings,
            'count': len(meetings),
            'type_breakdown': type_counts
        }

    except Exception as e:
        logger.error(f"Failed to get meetings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get meetings: {str(e)}")


# ============================================================================
# DELIVERABLES & PM WORKLOAD ENDPOINTS
# ============================================================================

class DeliverableCreate(BaseModel):
    """Model for creating a deliverable"""
    project_code: str
    deliverable_name: str
    due_date: str
    phase: Optional[str] = None
    deliverable_type: Optional[str] = None
    assigned_pm: Optional[str] = None
    description: Optional[str] = None
    priority: str = 'normal'


class DeliverableStatusUpdate(BaseModel):
    """Model for updating deliverable status"""
    status: str
    notes: Optional[str] = None
    submitted_date: Optional[str] = None


class OverdueContext(BaseModel):
    """Model for adding context to overdue deliverable"""
    context: str
    context_by: str


class MilestoneGeneration(BaseModel):
    """Model for generating project milestones"""
    project_code: str
    contract_start_date: str
    disciplines: Optional[List[str]] = None
    skip_schematic: bool = True


@app.get("/api/deliverables")
async def get_deliverables(
    project_code: Optional[str] = None,
    status: Optional[str] = None,
    assigned_pm: Optional[str] = None,
    phase: Optional[str] = None
):
    """
    Get all deliverables with optional filters.

    Filters:
    - project_code: Filter by project
    - status: Filter by status (pending, in_progress, completed, submitted)
    - assigned_pm: Filter by assigned PM
    - phase: Filter by project phase
    """
    try:
        deliverables = deliverables_service.get_all_deliverables(
            project_code=project_code,
            status=status,
            assigned_pm=assigned_pm,
            phase=phase
        )
        return {
            "success": True,
            "deliverables": deliverables,
            "count": len(deliverables)
        }
    except Exception as e:
        logger.error(f"Failed to get deliverables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/deliverables/overdue")
async def get_overdue_deliverables():
    """Get all overdue deliverables"""
    try:
        overdue = deliverables_service.get_overdue_deliverables()
        return {
            "success": True,
            "overdue_deliverables": overdue,
            "count": len(overdue)
        }
    except Exception as e:
        logger.error(f"Failed to get overdue deliverables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/deliverables/upcoming")
async def get_upcoming_deliverables(days: int = 14):
    """
    Get deliverables due within specified days.

    Args:
        days: Number of days ahead to look (default: 14)
    """
    try:
        upcoming = deliverables_service.get_upcoming_deliverables(days_ahead=days)
        return {
            "success": True,
            "upcoming_deliverables": upcoming,
            "count": len(upcoming),
            "days_ahead": days
        }
    except Exception as e:
        logger.error(f"Failed to get upcoming deliverables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/deliverables/alerts")
async def get_deliverable_alerts():
    """
    Get all active alerts for deliverables.

    Returns alerts categorized by:
    - day_of: Due today (critical)
    - tomorrow: Due tomorrow (high)
    - this_week: Due within 7 days (medium)
    - two_weeks: Due within 14 days (low)
    - overdue: Past due date (critical)
    """
    try:
        alerts = deliverables_service.get_alerts()
        # Group by priority
        by_priority = {
            'critical': [a for a in alerts if a['priority'] == 'critical'],
            'high': [a for a in alerts if a['priority'] == 'high'],
            'medium': [a for a in alerts if a['priority'] == 'medium'],
            'low': [a for a in alerts if a['priority'] == 'low']
        }
        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts),
            "by_priority": by_priority
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/deliverables")
async def create_deliverable(deliverable: DeliverableCreate):
    """Create a new deliverable"""
    try:
        deliverable_id = deliverables_service.create_deliverable(
            project_code=deliverable.project_code,
            deliverable_name=deliverable.deliverable_name,
            due_date=deliverable.due_date,
            phase=deliverable.phase,
            deliverable_type=deliverable.deliverable_type,
            assigned_pm=deliverable.assigned_pm,
            description=deliverable.description,
            priority=deliverable.priority
        )
        return {
            "success": True,
            "deliverable_id": deliverable_id,
            "message": f"Created deliverable {deliverable_id}"
        }
    except Exception as e:
        logger.error(f"Failed to create deliverable: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/deliverables/{deliverable_id}/status")
async def update_deliverable_status(deliverable_id: int, update: DeliverableStatusUpdate):
    """
    Update deliverable status.

    Valid statuses: pending, in_progress, submitted, completed, approved
    """
    try:
        success = deliverables_service.update_deliverable_status(
            deliverable_id=deliverable_id,
            status=update.status,
            notes=update.notes,
            submitted_date=update.submitted_date
        )
        if not success:
            raise HTTPException(status_code=404, detail="Deliverable not found")
        return {
            "success": True,
            "message": f"Updated deliverable {deliverable_id} to {update.status}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update deliverable status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/deliverables/{deliverable_id}/context")
async def add_overdue_context(deliverable_id: int, context: OverdueContext):
    """
    Add context/explanation for an overdue deliverable.

    Use this to document why a deliverable is delayed (e.g., "Client busy with permitting").
    """
    try:
        success = deliverables_service.add_overdue_context(
            deliverable_id=deliverable_id,
            context=context.context,
            context_by=context.context_by
        )
        if not success:
            raise HTTPException(status_code=404, detail="Deliverable not found")
        return {
            "success": True,
            "message": f"Added context to deliverable {deliverable_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pm-workload")
async def get_pm_workload(pm_name: Optional[str] = None):
    """
    Get PM workload summary.

    Shows deliverable counts by status for each PM:
    - total_deliverables
    - pending_count
    - in_progress_count
    - completed_count
    - overdue_count
    - due_this_week
    - due_two_weeks
    """
    try:
        workload = deliverables_service.get_pm_workload(pm_name=pm_name)
        return {
            "success": True,
            "workload": workload,
            "pm_count": len(workload)
        }
    except Exception as e:
        logger.error(f"Failed to get PM workload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pm-list")
async def get_pm_list():
    """Get list of available PMs (team leads) for assignment"""
    try:
        pms = deliverables_service.get_pm_list()
        return {
            "success": True,
            "pms": pms,
            "count": len(pms)
        }
    except Exception as e:
        logger.error(f"Failed to get PM list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_code}/phase-status")
async def get_project_phase_status(project_code: str):
    """
    Get current phase status for a project.

    Compares actual progress against typical Bensley project timeline.
    Returns flags if project is behind typical schedule.
    """
    try:
        status = deliverables_service.get_project_phase_status(project_code)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        return {
            "success": True,
            **status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get phase status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_code}/inferred-pm")
async def get_inferred_pm(project_code: str):
    """
    Get the inferred PM for a project based on:
    1. Manual assignment (team_lead field)
    2. Email activity (who responds to RFIs)
    3. Schedule data (most assigned person)
    """
    try:
        pm = deliverables_service.infer_pm_for_project(project_code)
        return {
            "success": True,
            "project_code": project_code,
            "inferred_pm": pm
        }
    except Exception as e:
        logger.error(f"Failed to infer PM: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_code}/generate-milestones")
async def generate_project_milestones(project_code: str, request: MilestoneGeneration):
    """
    Generate standard milestone deliverables for a project.

    Creates deliverables based on Bensley's typical project lifecycle:
    - Mobilization (2-3 months)
    - Concept Design (3 months)
    - Schematic Design (1 month, optional)
    - Design Development (3-4 months)
    - Construction Drawings (3 months)
    - Construction Observation (ongoing)
    """
    try:
        created_ids = deliverables_service.generate_project_milestones(
            project_code=request.project_code,
            contract_start_date=request.contract_start_date,
            disciplines=request.disciplines,
            skip_schematic=request.skip_schematic
        )
        return {
            "success": True,
            "project_code": project_code,
            "deliverables_created": len(created_ids),
            "deliverable_ids": created_ids
        }
    except Exception as e:
        logger.error(f"Failed to generate milestones: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/deliverables/seed-from-milestones")
async def seed_deliverables_from_milestones():
    """
    One-time migration: Seed deliverables table from existing project_milestones data.

    This converts milestone records into deliverable records with:
    - Auto-inferred PM assignments
    - Status mapping (complete -> completed, etc.)
    - Preserves dates and notes
    """
    try:
        result = deliverables_service.seed_from_milestones()
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Failed to seed from milestones: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lifecycle-phases")
async def get_lifecycle_phases():
    """
    Get the standard Bensley project lifecycle phases template.

    Returns typical durations and deliverable types for each phase.
    """
    return {
        "success": True,
        "phases": DeliverablesService.LIFECYCLE_PHASES,
        "total_typical_months": sum(p['typical_duration_months'] for p in DeliverablesService.LIFECYCLE_PHASES if not p.get('is_optional'))
    }


# ============================================================================
# MEETING TRANSCRIPTS ENDPOINTS
# ============================================================================

@app.get("/api/meeting-transcripts")
async def list_meeting_transcripts(
    project_code: Optional[str] = None,
    limit: int = Query(50, description="Maximum records to return"),
    offset: int = Query(0, description="Records to skip for pagination")
):
    """
    List meeting transcripts, optionally filtered by project.

    Returns voice transcripts from team meetings with summaries,
    key points, and action items extracted by AI.
    """
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT id, audio_filename, transcript, summary, key_points,
                   action_items, detected_project_code, match_confidence,
                   meeting_type, participants, sentiment, duration_seconds,
                   recorded_date, processed_date, created_at
            FROM meeting_transcripts
            WHERE 1=1
        """
        params = []

        if project_code:
            query += " AND (detected_project_code = ? OR detected_project_code LIKE ?)"
            params.extend([project_code, f"%{project_code}%"])

        # Get total count before pagination
        count_query = query.replace(
            "SELECT id, audio_filename, transcript, summary, key_points,\n                   action_items, detected_project_code, match_confidence,\n                   meeting_type, participants, sentiment, duration_seconds,\n                   recorded_date, processed_date, created_at",
            "SELECT COUNT(*)"
        )
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        query += " ORDER BY recorded_date DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        transcripts = []
        for row in rows:
            transcript = dict(row)
            # Parse JSON fields if they exist
            import json
            for json_field in ['key_points', 'action_items', 'participants']:
                if transcript.get(json_field):
                    try:
                        transcript[json_field] = json.loads(transcript[json_field])
                    except (json.JSONDecodeError, TypeError):
                        pass  # Keep as string if not valid JSON
            transcripts.append(transcript)

        conn.close()

        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "transcripts": transcripts
        }

    except Exception as e:
        logger.error(f"Failed to list meeting transcripts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/meeting-transcripts/{transcript_id}")
async def get_meeting_transcript(transcript_id: int):
    """
    Get full details for a single meeting transcript.

    Returns the complete transcript text, AI-generated summary,
    key points, and action items.
    """
    import sqlite3
    import json

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM meeting_transcripts WHERE id = ?
        """, (transcript_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")

        transcript = dict(row)

        # Parse JSON fields
        for json_field in ['key_points', 'action_items', 'participants']:
            if transcript.get(json_field):
                try:
                    transcript[json_field] = json.loads(transcript[json_field])
                except (json.JSONDecodeError, TypeError):
                    pass

        return {
            "success": True,
            "transcript": transcript
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transcript {transcript_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/meeting-transcripts/{transcript_id}/action-items")
async def get_transcript_action_items(transcript_id: int):
    """
    Get just the action items from a meeting transcript.

    Action items are structured as:
    [{"task": "...", "owner": "...", "deadline": "..."}, ...]
    """
    import sqlite3
    import json

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, audio_filename, action_items, detected_project_code, recorded_date
            FROM meeting_transcripts WHERE id = ?
        """, (transcript_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")

        result = dict(row)

        # Parse action items JSON
        action_items = []
        if result.get('action_items'):
            try:
                action_items = json.loads(result['action_items'])
            except (json.JSONDecodeError, TypeError):
                action_items = [{"task": result['action_items'], "owner": "Unknown", "deadline": None}]

        return {
            "success": True,
            "transcript_id": transcript_id,
            "audio_filename": result.get('audio_filename'),
            "project_code": result.get('detected_project_code'),
            "recorded_date": result.get('recorded_date'),
            "action_items": action_items,
            "count": len(action_items)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get action items for transcript {transcript_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UNIFIED TIMELINE ENDPOINT
# ============================================================================

@app.get("/api/projects/{project_code}/unified-timeline")
async def get_unified_timeline(
    project_code: str,
    types: Optional[str] = Query(None, description="Comma-separated event types: email,meeting,rfi,invoice,milestone"),
    limit: int = Query(50, description="Maximum events to return"),
    offset: int = Query(0, description="Events to skip for pagination")
):
    """
    Get ALL communications and events for a project in chronological order.

    Combines data from:
    - emails (via email_project_links)
    - meeting_transcripts
    - rfis
    - invoices
    - project_milestones

    This is THE endpoint for seeing a complete project history.
    """
    import sqlite3
    import json

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Parse types filter
        allowed_types = {'email', 'meeting', 'rfi', 'invoice', 'milestone'}
        if types:
            type_filter = set(t.strip().lower() for t in types.split(','))
            type_filter = type_filter & allowed_types
        else:
            type_filter = allowed_types

        events = []

        # Get emails linked to project
        if 'email' in type_filter:
            cursor.execute("""
                SELECT e.email_id as id, e.date, e.subject as title,
                       COALESCE(e.ai_summary, e.snippet, e.body_preview) as summary,
                       e.sender_name, e.sender_email, e.has_attachments,
                       'email' as event_type
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE epl.project_code = ? OR epl.project_code LIKE ?
            """, (project_code, f"%{project_code}%"))
            for row in cursor.fetchall():
                event = dict(row)
                event['data'] = {
                    'sender_name': event.pop('sender_name', None),
                    'sender_email': event.pop('sender_email', None),
                    'has_attachments': event.pop('has_attachments', False)
                }
                events.append(event)

        # Get meeting transcripts
        if 'meeting' in type_filter:
            cursor.execute("""
                SELECT id, recorded_date as date,
                       COALESCE(audio_filename, 'Meeting') as title,
                       summary, action_items, participants, meeting_type,
                       'meeting' as event_type
                FROM meeting_transcripts
                WHERE detected_project_code = ? OR detected_project_code LIKE ?
            """, (project_code, f"%{project_code}%"))
            for row in cursor.fetchall():
                event = dict(row)
                # Parse JSON fields
                for field in ['action_items', 'participants']:
                    if event.get(field):
                        try:
                            event[field] = json.loads(event[field])
                        except:
                            pass
                event['data'] = {
                    'action_items': event.pop('action_items', []),
                    'participants': event.pop('participants', []),
                    'meeting_type': event.pop('meeting_type', None)
                }
                events.append(event)

        # Get RFIs
        if 'rfi' in type_filter:
            cursor.execute("""
                SELECT rfi_id as id, date_sent as date, subject as title,
                       description as summary, status, priority, date_due,
                       'rfi' as event_type
                FROM rfis
                WHERE project_code = ? OR project_code LIKE ?
            """, (project_code, f"%{project_code}%"))
            for row in cursor.fetchall():
                event = dict(row)
                event['data'] = {
                    'status': event.pop('status', None),
                    'priority': event.pop('priority', None),
                    'date_due': event.pop('date_due', None)
                }
                events.append(event)

        # Get invoices
        if 'invoice' in type_filter:
            cursor.execute("""
                SELECT i.invoice_id as id, i.invoice_date as date,
                       COALESCE(i.invoice_number, 'Invoice') as title,
                       i.description as summary, i.invoice_amount, i.status, i.due_date,
                       'invoice' as event_type
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.project_code = ? OR p.project_code LIKE ?
            """, (project_code, f"%{project_code}%"))
            for row in cursor.fetchall():
                event = dict(row)
                event['data'] = {
                    'amount': event.pop('invoice_amount', None),
                    'status': event.pop('status', None),
                    'due_date': event.pop('due_date', None)
                }
                events.append(event)

        # Get milestones
        if 'milestone' in type_filter:
            cursor.execute("""
                SELECT milestone_id as id,
                       COALESCE(actual_date, planned_date) as date,
                       milestone_name as title, notes as summary,
                       phase, status, planned_date, actual_date,
                       'milestone' as event_type
                FROM project_milestones
                WHERE project_code = ? OR project_code LIKE ?
            """, (project_code, f"%{project_code}%"))
            for row in cursor.fetchall():
                event = dict(row)
                event['data'] = {
                    'phase': event.pop('phase', None),
                    'status': event.pop('status', None),
                    'planned_date': event.pop('planned_date', None),
                    'actual_date': event.pop('actual_date', None)
                }
                events.append(event)

        conn.close()

        # Sort all events by date (most recent first)
        def get_date(event):
            d = event.get('date')
            if d is None:
                return ''
            return str(d)

        events.sort(key=get_date, reverse=True)

        # Apply pagination
        total = len(events)
        events = events[offset:offset + limit]

        return {
            "success": True,
            "project_code": project_code,
            "total_events": total,
            "limit": limit,
            "offset": offset,
            "event_types": list(type_filter),
            "events": events
        }

    except Exception as e:
        logger.error(f"Failed to get unified timeline for {project_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AI SUGGESTIONS ENDPOINTS
# ============================================================================

class BulkApproveRequest(BaseModel):
    min_confidence: float = Field(0.8, description="Minimum confidence threshold")
    field_name: Optional[str] = Field(None, description="Filter by field name (e.g., 'new_contact')")


@app.get("/api/suggestions")
async def list_suggestions(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    field_name: Optional[str] = Query(None, description="Filter by field_name (e.g., 'new_contact', 'project_alias')"),
    data_table: Optional[str] = Query(None, description="Filter by data_table (e.g., 'contacts', 'learned_patterns')"),
    min_confidence: Optional[float] = Query(None, description="Minimum confidence score"),
    limit: int = Query(50, description="Maximum records to return"),
    offset: int = Query(0, description="Records to skip for pagination")
):
    """
    List AI suggestions from the queue.

    Suggestions are AI-detected data like new contacts or project aliases
    that need human review before being applied.
    """
    import sqlite3
    import json

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT suggestion_id, data_table, record_id, field_name,
                   current_value, suggested_value, confidence, reasoning,
                   evidence, status, created_at, reviewed_at, applied_at
            FROM ai_suggestions_queue
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if field_name:
            query += " AND field_name = ?"
            params.append(field_name)

        if data_table:
            query += " AND data_table = ?"
            params.append(data_table)

        if min_confidence is not None:
            query += " AND confidence >= ?"
            params.append(min_confidence)

        # Get total count
        count_query = query.replace(
            "SELECT suggestion_id, data_table, record_id, field_name,\n                   current_value, suggested_value, confidence, reasoning,\n                   evidence, status, created_at, reviewed_at, applied_at",
            "SELECT COUNT(*)"
        )
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        query += " ORDER BY confidence DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        suggestions = []
        for row in rows:
            suggestion = dict(row)
            # Parse suggested_value JSON
            if suggestion.get('suggested_value'):
                try:
                    suggestion['suggested_value'] = json.loads(suggestion['suggested_value'])
                except (json.JSONDecodeError, TypeError):
                    pass
            suggestions.append(suggestion)

        conn.close()

        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "suggestions": suggestions
        }

    except Exception as e:
        logger.error(f"Failed to list suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class ApproveSuggestionWithEdits(BaseModel):
    """Request model for approving suggestions with optional edits"""
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    related_project: Optional[str] = None
    notes: Optional[str] = None


@app.post("/api/suggestions/{suggestion_id}/approve")
async def approve_suggestion(suggestion_id: int, edits: Optional[ApproveSuggestionWithEdits] = None):
    """
    Approve an AI suggestion and apply it to the database.

    Optionally accepts edited contact data in the request body to override
    the original suggestion values.

    For 'new_contact': Inserts into contacts table
    For 'project_alias': Inserts into learned_patterns table
    """
    import sqlite3
    import json
    from datetime import datetime

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion
        cursor.execute("""
            SELECT * FROM ai_suggestions_queue WHERE suggestion_id = ?
        """, (suggestion_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found")

        suggestion = dict(row)

        if suggestion['status'] != 'pending':
            conn.close()
            raise HTTPException(status_code=400, detail=f"Suggestion already {suggestion['status']}")

        # Parse suggested value
        suggested_value = suggestion['suggested_value']
        if isinstance(suggested_value, str):
            try:
                suggested_value = json.loads(suggested_value)
            except:
                pass

        field_name = suggestion['field_name']
        now = datetime.now().isoformat()

        # Apply the suggestion based on field_name
        if field_name == 'new_contact':
            # Use edited values if provided, otherwise fall back to original suggestion
            if edits:
                name = edits.name or suggested_value.get('name', '')
                email = edits.email or suggested_value.get('email', '')
                company = edits.company or suggested_value.get('company', '')
                role = edits.role or suggested_value.get('role', '')
                related_project = edits.related_project or suggested_value.get('related_project', '')
                notes = edits.notes or ''
            else:
                name = suggested_value.get('name', '')
                email = suggested_value.get('email', '')
                company = suggested_value.get('company', '')
                role = suggested_value.get('role', '')
                related_project = suggested_value.get('related_project', '')
                notes = ''

            # Build comprehensive notes
            note_parts = []
            if company:
                note_parts.append(f"Company: {company}")
            if related_project:
                note_parts.append(f"Related project: {related_project}")
            if notes:
                note_parts.append(notes)
            note_parts.append("Added from AI suggestion")
            full_notes = ". ".join(note_parts)

            if email:
                # Check if contact already exists
                cursor.execute("SELECT contact_id FROM contacts WHERE email = ?", (email,))
                existing = cursor.fetchone()
                if not existing:
                    cursor.execute("""
                        INSERT INTO contacts (email, name, role, notes)
                        VALUES (?, ?, ?, ?)
                    """, (email, name, role or '', full_notes))
                    logger.info(f"Created contact: {name} <{email}> (role: {role})")
                else:
                    logger.info(f"Contact already exists: {email}")

        elif field_name == 'project_alias':
            # Insert into learned_patterns table
            alias = suggested_value.get('alias', '')
            project_code = suggested_value.get('project_code', '')

            if alias and project_code:
                cursor.execute("""
                    INSERT INTO learned_patterns
                    (pattern_name, pattern_type, condition, action, confidence_score, is_active)
                    VALUES (?, 'project_alias', ?, ?, ?, 1)
                """, (
                    f"Alias: {alias}",
                    json.dumps({"alias": alias}),
                    json.dumps({"project_code": project_code}),
                    suggestion['confidence']
                ))
                logger.info(f"Created pattern: {alias} -> {project_code}")

        # Mark suggestion as approved
        cursor.execute("""
            UPDATE ai_suggestions_queue
            SET status = 'approved', applied_at = ?, reviewed_at = ?
            WHERE suggestion_id = ?
        """, (now, now, suggestion_id))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Suggestion {suggestion_id} approved and applied",
            "field_name": field_name,
            "suggested_value": suggested_value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve suggestion {suggestion_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/{suggestion_id}/reject")
async def reject_suggestion(suggestion_id: int):
    """
    Reject an AI suggestion.
    """
    import sqlite3
    from datetime import datetime

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if suggestion exists
        cursor.execute("SELECT status FROM ai_suggestions_queue WHERE suggestion_id = ?", (suggestion_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found")

        if row[0] != 'pending':
            conn.close()
            raise HTTPException(status_code=400, detail=f"Suggestion already {row[0]}")

        now = datetime.now().isoformat()

        cursor.execute("""
            UPDATE ai_suggestions_queue
            SET status = 'rejected', reviewed_at = ?
            WHERE suggestion_id = ?
        """, (now, suggestion_id))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Suggestion {suggestion_id} rejected"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject suggestion {suggestion_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/bulk-approve")
async def bulk_approve_suggestions(request: BulkApproveRequest):
    """
    Bulk approve suggestions above a confidence threshold.

    Approves all pending suggestions matching the criteria.
    """
    import sqlite3
    import json
    from datetime import datetime

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query for matching suggestions
        query = """
            SELECT * FROM ai_suggestions_queue
            WHERE status = 'pending' AND confidence >= ?
        """
        params = [request.min_confidence]

        if request.field_name:
            query += " AND field_name = ?"
            params.append(request.field_name)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        approved_count = 0
        skipped_count = 0
        errors = []
        now = datetime.now().isoformat()

        for row in rows:
            suggestion = dict(row)
            suggestion_id = suggestion['suggestion_id']
            field_name = suggestion['field_name']

            try:
                # Parse suggested value
                suggested_value = suggestion['suggested_value']
                if isinstance(suggested_value, str):
                    try:
                        suggested_value = json.loads(suggested_value)
                    except:
                        pass

                # Apply based on field_name
                if field_name == 'new_contact':
                    email = suggested_value.get('email', '')
                    if email:
                        cursor.execute("SELECT contact_id FROM contacts WHERE email = ?", (email,))
                        if not cursor.fetchone():
                            name = suggested_value.get('name', '')
                            company = suggested_value.get('company', '')
                            role = suggested_value.get('role', '')
                            cursor.execute("""
                                INSERT INTO contacts (email, name, role, notes)
                                VALUES (?, ?, ?, ?)
                            """, (email, name, role or company, f"Bulk-added from AI suggestion. Company: {company}"))
                        else:
                            skipped_count += 1

                elif field_name == 'project_alias':
                    alias = suggested_value.get('alias', '')
                    project_code = suggested_value.get('project_code', '')
                    if alias and project_code:
                        cursor.execute("""
                            INSERT INTO learned_patterns
                            (pattern_name, pattern_type, condition, action, confidence_score, is_active)
                            VALUES (?, 'project_alias', ?, ?, ?, 1)
                        """, (
                            f"Alias: {alias}",
                            json.dumps({"alias": alias}),
                            json.dumps({"project_code": project_code}),
                            suggestion['confidence']
                        ))

                # Mark as approved
                cursor.execute("""
                    UPDATE ai_suggestions_queue
                    SET status = 'approved', applied_at = ?, reviewed_at = ?
                    WHERE suggestion_id = ?
                """, (now, now, suggestion_id))

                approved_count += 1

            except Exception as e:
                errors.append({"suggestion_id": suggestion_id, "error": str(e)})

        conn.commit()
        conn.close()

        return {
            "success": True,
            "approved_count": approved_count,
            "skipped_count": skipped_count,
            "error_count": len(errors),
            "errors": errors[:10] if errors else [],  # Limit error details
            "criteria": {
                "min_confidence": request.min_confidence,
                "field_name": request.field_name
            }
        }

    except Exception as e:
        logger.error(f"Failed to bulk approve suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/suggestions/stats")
async def get_suggestion_stats():
    """
    Get statistics about AI suggestions.
    """
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        stats = {}

        # Total counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM ai_suggestions_queue
            GROUP BY status
        """)
        stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Counts by field_name
        cursor.execute("""
            SELECT field_name, COUNT(*) as count
            FROM ai_suggestions_queue
            WHERE status = 'pending'
            GROUP BY field_name
        """)
        stats['pending_by_field'] = {row[0]: row[1] for row in cursor.fetchall()}

        # High confidence pending (>= 0.8)
        cursor.execute("""
            SELECT COUNT(*) FROM ai_suggestions_queue
            WHERE status = 'pending' AND confidence >= 0.8
        """)
        stats['high_confidence_pending'] = cursor.fetchone()[0]

        # Average confidence
        cursor.execute("""
            SELECT AVG(confidence) FROM ai_suggestions_queue
            WHERE status = 'pending'
        """)
        avg = cursor.fetchone()[0]
        stats['avg_pending_confidence'] = round(avg, 3) if avg else 0

        conn.close()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to get suggestion stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
