"""
Meetings Router - Meeting and calendar management endpoints

Endpoints:
    GET /api/meetings - List meetings
    POST /api/meetings - Create meeting
    POST /api/calendar/add-meeting - Add meeting from natural language
    GET /api/calendar/today - Today's meetings
    GET /api/calendar/upcoming - Upcoming meetings
    GET /api/calendar/date/{date} - Meetings for specific date
    GET /api/calendar/project/{project_code} - Project meetings
    GET /api/meetings/{meeting_id}/briefing - Meeting briefing
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field

from api.services import meeting_service, calendar_service, meeting_briefing_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["meetings"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class ChatMeetingRequest(BaseModel):
    """Request model for creating meetings via natural language"""
    text: str = Field(..., description="Natural language meeting request")


class CreateMeetingRequest(BaseModel):
    """Request model for creating meetings via JSON"""
    title: str = Field(..., description="Meeting title")
    meeting_type: str = Field(default="client_call", description="Type of meeting")
    meeting_date: str = Field(..., description="Meeting date (YYYY-MM-DD)")
    start_time: Optional[str] = Field(default=None, description="Start time (HH:MM)")
    end_time: Optional[str] = Field(default=None, description="End time (HH:MM)")
    location: Optional[str] = Field(default=None, description="Location or video call URL")
    meeting_link: Optional[str] = Field(default=None, description="Video call URL")
    project_code: Optional[str] = Field(default=None, description="Project code to link")
    description: Optional[str] = Field(default=None, description="Meeting description")


# ============================================================================
# MEETING ENDPOINTS
# ============================================================================

@router.get("/meetings")
async def list_meetings(
    proposal_id: Optional[int] = None,
    upcoming: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    meeting_type: Optional[str] = None
):
    """List meetings with optional filters"""
    try:
        if upcoming:
            meetings = meeting_service.get_upcoming_meetings(days_ahead=30)
        elif proposal_id:
            meetings = meeting_service.get_meetings_by_proposal(proposal_id)
        else:
            # Get all meetings with optional date filtering
            meetings = meeting_service.get_all_meetings(
                start_date=start_date,
                end_date=end_date,
                meeting_type=meeting_type
            )

        # Format meetings for frontend compatibility
        formatted = []
        for m in meetings:
            # Combine meeting_date and start_time into start_time datetime
            start_time = m.get('meeting_date', '') or ''
            if m.get('start_time'):
                start_time = f"{m['meeting_date']}T{m['start_time']}"

            end_time = None
            if m.get('end_time') and m.get('meeting_date'):
                end_time = f"{m['meeting_date']}T{m['end_time']}"

            formatted.append({
                'id': m.get('id'),
                'title': m.get('title', 'Untitled Meeting'),
                'description': m.get('description'),
                'start_time': start_time,
                'end_time': end_time,
                'location': m.get('location'),
                'meeting_type': m.get('meeting_type'),
                'project_code': m.get('project_code'),
                'attendees': [],  # Would parse participants JSON
                'status': m.get('status'),
                'is_virtual': bool(m.get('meeting_link')),
                'meeting_link': m.get('meeting_link'),
                # Transcript data
                'has_transcript': bool(m.get('transcript_id')),
                'transcript_id': m.get('transcript_id'),
                'transcript_summary': m.get('transcript_summary'),
                'transcript_key_points': m.get('transcript_key_points'),
                'transcript_action_items': m.get('transcript_action_items'),
            })

        response = list_response(formatted, len(formatted))
        response["meetings"] = formatted  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get meetings: {str(e)}")


@router.post("/meetings")
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
        return action_response(True, data={"meeting_id": meeting_id}, message="Meeting created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")


@router.post("/meetings/create")
async def create_meeting_json(request: CreateMeetingRequest):
    """Create a new meeting from JSON body"""
    try:
        from database.connection import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO meetings (
                title, description, meeting_type, meeting_date, start_time, end_time,
                location, meeting_link, project_code, status, source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', 'manual', datetime('now'))
        """, (
            request.title,
            request.description,
            request.meeting_type,
            request.meeting_date,
            request.start_time,
            request.end_time,
            request.location,
            request.meeting_link,
            request.project_code
        ))

        meeting_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return action_response(True, data={"meeting_id": meeting_id}, message="Meeting created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")


@router.get("/meetings/{meeting_id}/briefing")
async def get_meeting_briefing(meeting_id: int):
    """Get AI-generated briefing for a meeting"""
    try:
        briefing = meeting_briefing_service.generate_briefing(meeting_id)
        if not briefing:
            raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
        return item_response(briefing)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate briefing: {str(e)}")


# ============================================================================
# CALENDAR ENDPOINTS
# ============================================================================

@router.post("/calendar/add-meeting")
async def add_meeting_from_chat(request: ChatMeetingRequest):
    """Create a meeting from natural language input"""
    try:
        result = calendar_service.add_meeting_from_chat(request.text)
        if result.get('success'):
            return action_response(True, data=result.get('meeting'), message=result.get('message', 'Meeting created'))
        else:
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to create meeting'))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process meeting request: {str(e)}")


@router.get("/calendar/today")
async def get_today_meetings():
    """Get all meetings scheduled for today"""
    try:
        meetings = calendar_service.get_today_meetings()
        response = list_response(meetings, len(meetings))
        response["meetings"] = meetings  # Backward compat
        response["count"] = len(meetings)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get today's meetings: {str(e)}")


@router.get("/calendar/upcoming")
async def get_upcoming_meetings(days: int = Query(default=7, ge=1, le=30)):
    """Get meetings in the next N days"""
    try:
        meetings = calendar_service.get_upcoming_meetings(days)
        response = list_response(meetings, len(meetings))
        response["meetings"] = meetings  # Backward compat
        response["count"] = len(meetings)  # Backward compat
        response["days"] = days  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get upcoming meetings: {str(e)}")


@router.get("/calendar/date/{date}")
async def get_meetings_for_date(date: str):
    """Get all meetings for a specific date (YYYY-MM-DD format)"""
    try:
        meetings = calendar_service.get_meetings_for_date(date)
        response = list_response(meetings, len(meetings))
        response["meetings"] = meetings  # Backward compat
        response["count"] = len(meetings)  # Backward compat
        response["date"] = date  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get meetings for {date}: {str(e)}")


@router.get("/calendar/project/{project_code}")
async def get_project_meetings(project_code: str):
    """Get all meetings for a specific project"""
    try:
        meetings = calendar_service.get_meetings_for_project(project_code)
        response = list_response(meetings, len(meetings))
        response["meetings"] = meetings  # Backward compat
        response["count"] = len(meetings)  # Backward compat
        response["project_code"] = project_code  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get meetings for {project_code}: {str(e)}")
