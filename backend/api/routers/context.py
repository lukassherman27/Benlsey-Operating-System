"""
Context Router - Proposal context, notes, and tasks

Endpoints:
    GET /api/context/by-proposal/{proposal_id} - Get all context
    GET /api/context/by-proposal/{proposal_id}/summary - Get summary
    GET /api/context/by-proposal/{proposal_id}/notes - Get notes
    GET /api/context/by-proposal/{proposal_id}/tasks - Get tasks
    GET /api/context/{context_id} - Get context by ID
    POST /api/context - Create context entry
    PATCH /api/context/{context_id} - Update context
    DELETE /api/context/{context_id} - Delete context
    POST /api/context/{context_id}/complete - Mark task complete
    GET /api/context/tasks/assigned/{assigned_to} - Get tasks by assignee
    GET /api/context/tasks/overdue - Get overdue tasks
    GET /api/context/tasks/upcoming - Get upcoming tasks
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field

from api.services import context_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["context"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateContextRequest(BaseModel):
    """Request to create context entry"""
    proposal_id: int
    context_type: str = Field(..., description="Type: note, task, instruction, reminder")
    content: str
    source: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "normal"
    tags: Optional[str] = None


class UpdateContextRequest(BaseModel):
    """Request to update context"""
    context_type: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[str] = None


class LogAgentActionRequest(BaseModel):
    """Request to log agent action on context"""
    action_taken: str
    result: Optional[str] = None


# ============================================================================
# PROPOSAL CONTEXT
# ============================================================================

@router.get("/context/by-proposal/{proposal_id}")
async def get_context_by_proposal(
    proposal_id: int,
    context_type: Optional[str] = Query(None, description="Filter by type"),
    include_completed: bool = Query(True, description="Include completed items")
):
    """Get all context for a proposal"""
    try:
        context = context_service.get_context_by_proposal(
            proposal_id=proposal_id,
            context_type=context_type,
            include_completed=include_completed
        )
        response = list_response(context, len(context))
        response["proposal_id"] = proposal_id  # Backward compat
        response["context"] = context  # Backward compat
        response["count"] = len(context)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/by-proposal/{proposal_id}/summary")
async def get_context_summary(proposal_id: int):
    """Get context summary for a proposal"""
    try:
        summary = context_service.get_context_summary(proposal_id)
        return item_response(summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/by-proposal/{proposal_id}/notes")
async def get_notes_by_proposal(proposal_id: int):
    """Get all notes for a proposal"""
    try:
        notes = context_service.get_notes_by_proposal(proposal_id)
        response = list_response(notes, len(notes))
        response["proposal_id"] = proposal_id  # Backward compat
        response["notes"] = notes  # Backward compat
        response["count"] = len(notes)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/by-proposal/{proposal_id}/tasks")
async def get_tasks_by_proposal(proposal_id: int):
    """Get all tasks for a proposal"""
    try:
        tasks = context_service.get_tasks_by_proposal(proposal_id)
        response = list_response(tasks, len(tasks))
        response["proposal_id"] = proposal_id  # Backward compat
        response["tasks"] = tasks  # Backward compat
        response["count"] = len(tasks)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CRUD
# ============================================================================

@router.get("/context/{context_id}")
async def get_context(context_id: int):
    """Get a specific context entry"""
    try:
        context = context_service.get_context_by_id(context_id)
        if not context:
            raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
        return item_response(context)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context")
async def create_context(request: CreateContextRequest):
    """Create a new context entry"""
    try:
        context_id = context_service.create_context(request.dict())
        return action_response(True, data={"context_id": context_id}, message="Context created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/context/{context_id}")
async def update_context(context_id: int, request: UpdateContextRequest):
    """Update a context entry"""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        success = context_service.update_context(context_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
        return action_response(True, message="Context updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/context/{context_id}")
async def delete_context(context_id: int):
    """Delete a context entry"""
    try:
        success = context_service.delete_context(context_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
        return action_response(True, message="Context deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context/{context_id}/complete")
async def complete_task(context_id: int):
    """Mark a task as complete"""
    try:
        success = context_service.complete_task(context_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
        return action_response(True, message="Task completed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context/{context_id}/log-action")
async def log_agent_action(context_id: int, request: LogAgentActionRequest):
    """Log an agent action on a context entry"""
    try:
        context_service.log_agent_action(
            context_id=context_id,
            action_taken=request.action_taken,
            result=request.result
        )
        return action_response(True, message="Action logged")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TASK MANAGEMENT
# ============================================================================

@router.get("/context/tasks/assigned/{assigned_to}")
async def get_tasks_by_assigned(
    assigned_to: str,
    status: str = Query("active", description="Filter by status")
):
    """Get tasks assigned to a specific person"""
    try:
        tasks = context_service.get_tasks_by_assigned(assigned_to=assigned_to, status=status)
        response = list_response(tasks, len(tasks))
        response["assigned_to"] = assigned_to  # Backward compat
        response["tasks"] = tasks  # Backward compat
        response["count"] = len(tasks)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/tasks/overdue")
async def get_overdue_tasks():
    """Get all overdue tasks"""
    try:
        tasks = context_service.get_overdue_tasks()
        return list_response(tasks, len(tasks))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/tasks/upcoming")
async def get_upcoming_tasks(days: int = Query(7, ge=1, le=30)):
    """Get tasks due in the next N days"""
    try:
        tasks = context_service.get_upcoming_tasks(days_ahead=days)
        return list_response(tasks, len(tasks))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
