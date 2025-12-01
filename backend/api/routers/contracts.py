"""
Contracts Router - Contract management, terms, and fee breakdowns

Endpoints:
    GET /api/contracts - List all contracts
    GET /api/contracts/stats - Contract statistics
    GET /api/contracts/expiring-soon - Contracts expiring soon
    GET /api/contracts/monthly-summary - Monthly fee summary
    GET /api/contracts/by-project/{project_code} - Get project contracts
    GET /api/contracts/by-project/{project_code}/latest - Get latest contract
    GET /api/contracts/by-project/{project_code}/terms - Get contract terms
    GET /api/contracts/by-project/{project_code}/fee-breakdown - Get fee breakdown
    GET /api/contracts/by-project/{project_code}/versions - Get contract versions
    POST /api/contracts/by-project/{project_code}/terms - Create contract terms
    POST /api/contracts/by-project/{project_code}/fee-breakdown - Create fee breakdown
    GET /api/contracts/families - Get project families
    POST /api/contracts/families/link - Link projects
    GET /api/contracts/imports/pending - Pending contract imports
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field

from api.services import contract_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["contracts"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateContractTermsRequest(BaseModel):
    """Request to create contract terms"""
    contract_type: Optional[str] = None
    payment_terms: Optional[str] = None
    payment_due_days: Optional[int] = None
    retention_percent: Optional[float] = None
    currency: str = "USD"
    total_value: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None


class CreateFeeBreakdownRequest(BaseModel):
    """Request to create fee breakdown"""
    total_fee: float
    phases: Optional[List[str]] = None
    percentages: Optional[List[float]] = None


class LinkProjectsRequest(BaseModel):
    """Request to link projects as family"""
    parent_code: str
    child_code: str
    relationship: str = "phase"


# ============================================================================
# LIST ENDPOINTS
# ============================================================================

@router.get("/contracts")
async def get_all_contracts(
    contract_type: Optional[str] = Query(None, description="Filter by contract type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("DESC", description="Sort order: ASC or DESC")
):
    """Get all contracts with optional filtering"""
    try:
        result = contract_service.get_all_contracts(
            contract_type=contract_type,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        # paginate() returns 'items', not 'contracts'
        contracts = result.get("items", [])
        return list_response(contracts, result.get("total", len(contracts)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/stats")
async def get_contract_stats():
    """Get contract statistics"""
    try:
        stats = contract_service.get_contract_stats()
        return item_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/expiring-soon")
async def get_contracts_expiring_soon(days: int = Query(90, ge=1, le=365)):
    """Get contracts expiring within N days"""
    try:
        contracts = contract_service.get_contracts_expiring_soon(days=days)
        return list_response(contracts, len(contracts))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/monthly-summary")
async def get_monthly_fee_summary():
    """Get monthly fee summary across all contracts"""
    try:
        summary = contract_service.get_monthly_fee_summary()
        return item_response(summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT-SPECIFIC CONTRACTS
# ============================================================================

@router.get("/contracts/by-project/{project_code}")
async def get_contracts_by_project(project_code: str):
    """Get all contracts for a project"""
    try:
        contracts = contract_service.get_all_contracts_for_project(project_code)
        response = list_response(contracts, len(contracts))
        response["project_code"] = project_code  # Backward compat
        response["contracts"] = contracts  # Backward compat
        response["count"] = len(contracts)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/by-project/{project_code}/latest")
async def get_latest_contract(project_code: str):
    """Get the latest/current contract for a project"""
    try:
        contract = contract_service.get_latest_contract_for_project(project_code)
        if not contract:
            raise HTTPException(status_code=404, detail=f"No contract found for {project_code}")
        return item_response(contract)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/by-project/{project_code}/terms")
async def get_contract_terms(project_code: str):
    """Get contract terms for a project"""
    try:
        terms = contract_service.get_contract_terms(project_code)
        if not terms:
            raise HTTPException(status_code=404, detail=f"No contract terms for {project_code}")
        return item_response(terms)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts/by-project/{project_code}/terms")
async def create_contract_terms(project_code: str, request: CreateContractTermsRequest):
    """Create or update contract terms for a project"""
    try:
        result = contract_service.create_contract_terms(project_code, request.dict())
        return action_response(True, data=result, message="Contract terms created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/by-project/{project_code}/fee-breakdown")
async def get_fee_breakdown(project_code: str):
    """Get fee breakdown for a project"""
    try:
        breakdown = contract_service.get_fee_breakdown(project_code)
        response = list_response(breakdown, len(breakdown))
        response["project_code"] = project_code  # Backward compat
        response["breakdown"] = breakdown  # Backward compat
        response["count"] = len(breakdown)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts/by-project/{project_code}/fee-breakdown")
async def create_fee_breakdown(project_code: str, request: CreateFeeBreakdownRequest):
    """Create standard fee breakdown for a project"""
    try:
        result = contract_service.create_standard_fee_breakdown(
            project_code=project_code,
            total_fee=request.total_fee,
            phases=request.phases,
            percentages=request.percentages
        )
        return action_response(True, data=result, message="Fee breakdown created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/by-project/{project_code}/versions")
async def get_contract_versions(project_code: str):
    """Get all versions of contracts for a project"""
    try:
        versions = contract_service.get_contract_versions(project_code)
        response = list_response(versions, len(versions))
        response["project_code"] = project_code  # Backward compat
        response["versions"] = versions  # Backward compat
        response["count"] = len(versions)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT FAMILIES
# ============================================================================

@router.get("/contracts/families")
async def get_all_project_families():
    """Get all project family relationships"""
    try:
        families = contract_service.get_all_project_families()
        response = list_response(families, len(families))
        response["families"] = families  # Backward compat
        response["count"] = len(families)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/families/{project_code}")
async def get_project_family(project_code: str):
    """Get family tree for a project"""
    try:
        family = contract_service.get_project_family(project_code)
        return item_response(family)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts/families/link")
async def link_projects(request: LinkProjectsRequest):
    """Link two projects as parent/child"""
    try:
        result = contract_service.link_projects(
            parent_code=request.parent_code,
            child_code=request.child_code,
            relationship=request.relationship
        )
        return action_response(True, data=result, message="Projects linked")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# IMPORT MANAGEMENT
# ============================================================================

@router.get("/contracts/imports/pending")
async def get_pending_imports(limit: int = Query(50, ge=1, le=200)):
    """Get pending contract imports"""
    try:
        pending = contract_service.list_pending_imports(limit=limit)
        return list_response(pending, len(pending))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
