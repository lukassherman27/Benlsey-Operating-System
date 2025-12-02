"""
API Models - Shared Pydantic models for all routers

This file centralizes all request/response models used across API endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any


# ============================================================================
# DASHBOARD MODELS
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
    proposals: Dict[str, int]
    revenue: Dict[str, float]


# ============================================================================
# PROPOSAL MODELS
# ============================================================================

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


# ============================================================================
# CONTRACT MODELS
# ============================================================================

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
# EMAIL MODELS
# ============================================================================

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


class EmailCategoryRequest(BaseModel):
    """Request to update email category"""
    category: str = Field(..., description="Category name")
    subcategory: Optional[str] = Field(None, description="Subcategory name")
    project_code: Optional[str] = Field(None, description="Associated project code")


class BulkCategoryRequest(BaseModel):
    """Request for bulk email categorization"""
    email_ids: List[int] = Field(..., description="List of email IDs to categorize")
    category: str = Field(..., description="Category to apply")
    subcategory: Optional[str] = Field(None, description="Subcategory to apply")
    project_code: Optional[str] = Field(None, description="Associated project code")


class EmailLinkRequest(BaseModel):
    """Request to link email to project"""
    project_code: str = Field(..., description="Project code to link to")
    link_type: str = Field(default="manual", description="Type of link (manual, auto, ai)")


# ============================================================================
# SUGGESTION MODELS
# ============================================================================

class SuggestionApproveRequest(BaseModel):
    """Request to approve a suggestion with optional edits"""
    edits: Optional[Dict[str, Any]] = Field(None, description="Optional edits to apply before approving")


class SuggestionRejectRequest(BaseModel):
    """Request to reject a suggestion"""
    reason: Optional[str] = Field(None, description="Reason for rejection")


class BulkApproveRequest(BaseModel):
    """Request for bulk approval of suggestions"""
    min_confidence: float = Field(default=0.8, ge=0, le=1, description="Minimum confidence threshold")


class BulkRejectRequest(BaseModel):
    """Request for bulk rejection of suggestions by ID"""
    suggestion_ids: List[int] = Field(..., description="List of suggestion IDs to reject")
    reason: Optional[str] = Field(default="batch_rejected", description="Reason for rejection")


class BulkApproveByIdsRequest(BaseModel):
    """Request for bulk approval of suggestions by ID"""
    suggestion_ids: List[int] = Field(..., description="List of suggestion IDs to approve")


class LinkedItem(BaseModel):
    """An item to link (project, proposal, or category)"""
    type: str = Field(..., description="Type: 'project', 'proposal', or 'category'")
    code: str = Field(..., description="Project/proposal code or category ID")
    name: Optional[str] = Field(None, description="Display name")
    subcategory: Optional[str] = Field(None, description="Subcategory for category type")


class SuggestionRejectWithCorrectionRequest(BaseModel):
    """Request to reject a suggestion with correction (specifies correct data)"""
    rejection_reason: str = Field(..., description="Why this suggestion is wrong")
    # For email_link corrections
    correct_project_code: Optional[str] = Field(None, description="Correct project code to link to (backward compat)")
    correct_proposal_id: Optional[int] = Field(None, description="Correct proposal ID to link to")
    # For contact corrections
    correct_contact_id: Optional[int] = Field(None, description="Correct contact to link")
    # Multi-linking support
    linked_items: Optional[List[LinkedItem]] = Field(None, description="List of items to link (multi-link support)")
    # Email categorization
    category: Optional[str] = Field(None, description="Email category (internal, external, spam, etc.)")
    subcategory: Optional[str] = Field(None, description="Email subcategory (hr, it, admin, etc.)")
    # Pattern learning
    create_pattern: bool = Field(default=False, description="Create a pattern from this correction")
    pattern_notes: Optional[str] = Field(None, description="Notes about the pattern")


class SuggestionApproveWithContextRequest(BaseModel):
    """Request to approve a suggestion with additional context for learning"""
    # Pattern learning options
    create_sender_pattern: bool = Field(default=False, description="Always link emails from this sender")
    create_domain_pattern: bool = Field(default=False, description="Always link emails from this domain")
    contact_role: Optional[str] = Field(None, description="Role of the contact (client, contractor, etc.)")
    pattern_notes: Optional[str] = Field(None, description="Notes about the pattern")
    # Contact edits (for new_contact suggestions)
    contact_edits: Optional[Dict[str, Any]] = Field(None, description="Edits to contact data")


class PatternCreateRequest(BaseModel):
    """Request to manually create a pattern"""
    pattern_type: str = Field(..., description="Type: sender_to_project, domain_to_project, etc.")
    pattern_key: str = Field(..., description="The key to match (email, domain, keyword)")
    target_type: str = Field(..., description="Target type: project or proposal")
    target_code: str = Field(..., description="Project/proposal code")
    notes: Optional[str] = Field(None, description="Notes about this pattern")


class PatternUpdateRequest(BaseModel):
    """Request to update a pattern"""
    is_active: Optional[bool] = Field(None, description="Enable/disable pattern")
    notes: Optional[str] = Field(None, description="Notes about this pattern")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")


# ============================================================================
# RFI MODELS
# ============================================================================

class RFIRequest(BaseModel):
    """Request to create an RFI"""
    project_code: str = Field(..., description="Project code")
    rfi_number: str = Field(..., description="RFI number")
    subject: str = Field(..., description="RFI subject")
    description: Optional[str] = Field(None, description="RFI description")
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    priority: str = Field(default="normal", description="Priority (low, normal, high, urgent)")
    assigned_to: Optional[str] = Field(None, description="Assigned to")


class RFIResponseRequest(BaseModel):
    """Request to respond to an RFI"""
    response: str = Field(..., description="Response text")
    responded_by: str = Field(..., description="Who responded")


# ============================================================================
# MEETING MODELS
# ============================================================================

class MeetingRequest(BaseModel):
    """Request to create a meeting"""
    title: str = Field(..., description="Meeting title")
    start_time: str = Field(..., description="Start time (ISO format)")
    end_time: Optional[str] = Field(None, description="End time (ISO format)")
    project_code: Optional[str] = Field(None, description="Associated project code")
    location: Optional[str] = Field(None, description="Meeting location")
    attendees: Optional[List[str]] = Field(None, description="List of attendees")
    notes: Optional[str] = Field(None, description="Meeting notes")


# ============================================================================
# CONTACT MODELS
# ============================================================================

class ContactRequest(BaseModel):
    """Request to create or update a contact"""
    name: str = Field(..., description="Contact name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    company: Optional[str] = Field(None, description="Company name")
    role: Optional[str] = Field(None, description="Role/title")
    notes: Optional[str] = Field(None, description="Additional notes")


# ============================================================================
# TRAINING/FEEDBACK MODELS
# ============================================================================

class FeedbackRequest(BaseModel):
    """Request to submit training feedback"""
    feature_type: str = Field(..., description="Feature type (email, proposal, etc.)")
    feature_id: str = Field(..., description="Feature ID")
    feedback_type: str = Field(..., description="Feedback type (correct, incorrect, missing)")
    current_value: Optional[str] = Field(None, description="Current value")
    correct_value: Optional[str] = Field(None, description="Correct value")
    notes: Optional[str] = Field(None, description="Additional notes")


class ValidationReviewRequest(BaseModel):
    """Request to approve/deny a validation suggestion"""
    reviewed_by: str = Field(..., description="Reviewer name")
    review_notes: Optional[str] = Field(None, description="Review notes")


# ============================================================================
# QUERY MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Request for natural language query"""
    query: str = Field(..., description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context")


class QueryFeedbackRequest(BaseModel):
    """Request to provide feedback on query results"""
    query: str = Field(..., description="Original query")
    response: str = Field(..., description="System response")
    helpful: bool = Field(..., description="Was the response helpful?")
    feedback: Optional[str] = Field(None, description="Additional feedback")


# ============================================================================
# DELIVERABLE MODELS
# ============================================================================

class DeliverableRequest(BaseModel):
    """Request to create a deliverable"""
    project_code: str = Field(..., description="Project code")
    title: str = Field(..., description="Deliverable title")
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    status: str = Field(default="pending", description="Status")
    description: Optional[str] = Field(None, description="Description")


class DeliverableStatusRequest(BaseModel):
    """Request to update deliverable status"""
    status: str = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Status notes")


# ============================================================================
# PROJECT MODELS
# ============================================================================

class ProjectCreateRequest(BaseModel):
    """Request to create a full project"""
    project_code: str = Field(..., description="Project code")
    project_title: str = Field(..., description="Project title")
    client_name: Optional[str] = Field(None, description="Client name")
    total_fee_usd: Optional[float] = Field(None, description="Total fee")
    status: str = Field(default="active", description="Project status")
    start_date: Optional[str] = Field(None, description="Start date")
    description: Optional[str] = Field(None, description="Description")


# ============================================================================
# INVOICE MODELS
# ============================================================================

class InvoiceCreateRequest(BaseModel):
    """Request to create an invoice"""
    project_code: str = Field(..., description="Project code")
    invoice_number: str = Field(..., description="Invoice number")
    amount_usd: float = Field(..., description="Invoice amount in USD")
    invoice_date: Optional[str] = Field(None, description="Invoice date (YYYY-MM-DD)")
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    description: Optional[str] = Field(None, description="Description")
    status: str = Field(default="pending", description="Invoice status")


class InvoiceUpdateRequest(BaseModel):
    """Request to update an invoice"""
    amount_usd: Optional[float] = Field(None, description="Invoice amount")
    status: Optional[str] = Field(None, description="Invoice status")
    paid_date: Optional[str] = Field(None, description="Payment date")
    notes: Optional[str] = Field(None, description="Notes")
