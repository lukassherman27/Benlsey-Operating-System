"""
Recordings Router - Audio recording upload and processing endpoints
Issue: #194

Endpoints:
    POST /api/recordings/upload - Upload and process audio recording
    GET /api/recordings/projects - Get projects for dropdown
    GET /api/recordings/{id}/status - Check processing status
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import json

from api.dependencies import DB_PATH

router = APIRouter(prefix="/api/recordings", tags=["recordings"])

_processor = None

def get_processor():
    global _processor
    if _processor is None:
        from services.audio_processor import get_audio_processor
        _processor = get_audio_processor(DB_PATH)
    return _processor


@router.post("/upload")
async def upload_recording(
    audio: UploadFile = File(...),
    project_code: Optional[str] = Form(None),
    meeting_title: Optional[str] = Form(None),
    attendees: Optional[str] = Form(None),
):
    """Upload and process an audio recording."""
    allowed_types = ['audio/mpeg', 'audio/mp4', 'audio/wav', 'audio/webm', 'audio/ogg', 'audio/m4a', 'video/webm', 'video/mp4']
    content_type = audio.content_type or ''
    filename = audio.filename or 'recording.webm'
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    allowed_extensions = ['mp3', 'm4a', 'wav', 'webm', 'ogg', 'mp4']

    if content_type not in allowed_types and ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: {content_type}")

    content = await audio.read()
    max_size = 25 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"File too large: {len(content) / (1024*1024):.1f}MB. Max: 25MB")
    if len(content) < 1000:
        raise HTTPException(status_code=400, detail="Recording too short or empty")

    attendee_list = None
    if attendees:
        try:
            attendee_list = json.loads(attendees)
        except json.JSONDecodeError:
            attendee_list = [a.strip() for a in attendees.split(',') if a.strip()]

    try:
        processor = get_processor()
        result = await processor.process_recording(
            audio_content=content,
            filename=filename,
            project_code=project_code,
            attendees=attendee_list,
            meeting_title=meeting_title
        )
        return {
            "success": True,
            "message": "Recording processed successfully",
            "transcript_id": result['transcript_id'],
            "audio_path": result['audio_path'],
            "word_count": result['word_count'],
            "summary": result.get('summary'),
            "key_points": result.get('key_points', []),
            "action_items": result.get('action_items', []),
            "task_ids": result.get('task_ids', []),
            "tasks_created": len(result.get('task_ids', []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects")
async def get_projects():
    """Get list of projects for the recorder dropdown."""
    try:
        processor = get_processor()
        projects = processor.get_projects_for_dropdown()
        return {"success": True, "projects": projects, "count": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{transcript_id}/status")
async def get_recording_status(transcript_id: int):
    """Check processing status of a recording."""
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, transcript, summary, key_points, action_items, processed_date
            FROM meeting_transcripts WHERE id = ?
        """, (transcript_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Recording not found")

        transcript = dict(row)
        cursor.execute("SELECT task_id, title, status, priority, due_date FROM tasks WHERE source_transcript_id = ?", (transcript_id,))
        tasks = [dict(r) for r in cursor.fetchall()]
        conn.close()

        key_points = transcript.get('key_points')
        if key_points and isinstance(key_points, str):
            try:
                key_points = json.loads(key_points)
            except:
                key_points = []

        action_items = transcript.get('action_items')
        if action_items and isinstance(action_items, str):
            try:
                action_items = json.loads(action_items)
            except:
                action_items = []

        status = 'completed' if transcript.get('processed_date') else 'processing'
        if not transcript.get('transcript'):
            status = 'failed'

        return {
            "success": True,
            "transcript_id": transcript_id,
            "status": status,
            "transcript": transcript.get('transcript'),
            "summary": transcript.get('summary'),
            "key_points": key_points,
            "action_items": action_items,
            "tasks": tasks,
            "task_count": len(tasks)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")
