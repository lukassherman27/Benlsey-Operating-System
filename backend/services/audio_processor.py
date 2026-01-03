"""
Audio Processor Service - Whisper transcription and processing
Issue: #194

Handles:
1. Audio upload and storage
2. Whisper API transcription
3. Claude/GPT summarization
4. Action item extraction
5. Task creation from action items
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

from openai import OpenAI

DB_PATH = os.getenv('BENSLEY_DB_PATH', 'database/bensley_master.db')
AUDIO_STORAGE_PATH = Path(os.getenv('AUDIO_STORAGE_PATH', 'uploads/audio'))


class AudioProcessor:
    """Processes audio recordings: transcription, summarization, task extraction"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.client = OpenAI()
        AUDIO_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    async def process_recording(
        self,
        audio_content: bytes,
        filename: str,
        project_code: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        meeting_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Full pipeline: save audio -> transcribe -> summarize -> extract tasks"""
        audio_path = await self.save_audio(audio_content, filename)
        transcript_text = await self.transcribe_audio(audio_path)

        transcript_id = self.create_transcript_record(
            audio_filename=filename,
            audio_path=str(audio_path),
            transcript=transcript_text,
            project_code=project_code,
            meeting_title=meeting_title,
            participants=attendees
        )

        analysis = await self.analyze_transcript(
            transcript_text,
            project_code=project_code,
            attendees=attendees
        )

        self.update_transcript(
            transcript_id,
            summary=analysis.get('summary'),
            key_points=analysis.get('key_points'),
            action_items=analysis.get('action_items')
        )

        task_ids = []
        if analysis.get('action_items'):
            task_ids = self.create_tasks_from_action_items(
                transcript_id=transcript_id,
                action_items=analysis['action_items'],
                project_code=project_code
            )

        return {
            'transcript_id': transcript_id,
            'audio_path': str(audio_path),
            'transcript': transcript_text,
            'summary': analysis.get('summary'),
            'key_points': analysis.get('key_points'),
            'action_items': analysis.get('action_items'),
            'task_ids': task_ids,
            'word_count': len(transcript_text.split()) if transcript_text else 0
        }

    async def save_audio(self, audio_content: bytes, filename: str) -> Path:
        """Save audio file to storage"""
        date_folder = datetime.now().strftime('%Y-%m')
        folder = AUDIO_STORAGE_PATH / date_folder
        folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = "".join(c for c in filename if c.isalnum() or c in '._-')
        final_filename = f"{timestamp}_{safe_name}"
        file_path = folder / final_filename

        with open(file_path, 'wb') as f:
            f.write(audio_content)
        return file_path

    async def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        with open(audio_path, 'rb') as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                language="en"
            )
        return response

    async def analyze_transcript(
        self,
        transcript: str,
        project_code: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Use GPT to summarize transcript and extract action items"""
        if not transcript or len(transcript.strip()) < 50:
            return {'summary': 'Recording too short for analysis', 'key_points': [], 'action_items': []}

        attendee_context = f"Attendees: {', '.join(attendees)}" if attendees else ""
        project_context = f"Project: {project_code}" if project_code else ""

        prompt = f"""Analyze this meeting transcript and extract:
1. A concise summary (2-3 paragraphs)
2. Key points discussed (bullet points)
3. Action items with assignees and due dates if mentioned

{project_context}
{attendee_context}

TRANSCRIPT:
{transcript[:8000]}

Respond in JSON format:
{{
    "summary": "...",
    "key_points": ["point 1", "point 2", ...],
    "action_items": [
        {{"task": "description", "assignee": "name or null", "due_date": "YYYY-MM-DD or null", "priority": "low/normal/high"}}
    ]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a meeting analyst. Extract actionable insights from meeting transcripts. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return {
                'summary': result.get('summary', ''),
                'key_points': result.get('key_points', []),
                'action_items': result.get('action_items', [])
            }
        except Exception as e:
            return {'summary': f'Analysis failed: {str(e)}', 'key_points': [], 'action_items': []}

    def create_transcript_record(
        self,
        audio_filename: str,
        audio_path: str,
        transcript: str,
        project_code: Optional[str] = None,
        meeting_title: Optional[str] = None,
        participants: Optional[List[str]] = None
    ) -> int:
        """Create initial transcript record in database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            project_id = proposal_id = None
            if project_code:
                cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
                row = cursor.fetchone()
                if row:
                    project_id = row[0]
                cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (project_code,))
                row = cursor.fetchone()
                if row:
                    proposal_id = row[0]

            cursor.execute("""
                INSERT INTO meeting_transcripts (
                    audio_filename, audio_path, transcript, detected_project_code,
                    detected_project_id, project_id, proposal_id, meeting_title,
                    participants, recorded_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'), datetime('now'))
            """, (
                audio_filename, audio_path, transcript, project_code,
                project_id, project_id, proposal_id,
                meeting_title or f"Recording {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                json.dumps(participants) if participants else None
            ))
            conn.commit()
            return cursor.lastrowid

    def update_transcript(self, transcript_id: int, summary=None, key_points=None, action_items=None):
        """Update transcript with analysis results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE meeting_transcripts SET
                    summary = ?, key_points = ?, action_items = ?, processed_date = datetime('now')
                WHERE id = ?
            """, (
                summary,
                json.dumps(key_points) if key_points else None,
                json.dumps(action_items) if action_items else None,
                transcript_id
            ))
            conn.commit()

    def create_tasks_from_action_items(self, transcript_id: int, action_items: List[Dict], project_code: Optional[str] = None) -> List[int]:
        """Create tasks from extracted action items"""
        task_ids = []
        with self.get_connection() as conn:
            cursor = conn.cursor()

            proposal_id = None
            if project_code:
                cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (project_code,))
                row = cursor.fetchone()
                if row:
                    proposal_id = row[0]

            priority_map = {'low': 'low', 'normal': 'medium', 'medium': 'medium', 'high': 'high', 'critical': 'critical'}

            for item in action_items:
                priority = priority_map.get(item.get('priority', 'normal').lower(), 'medium')
                cursor.execute("""
                    INSERT INTO tasks (
                        title, description, task_type, priority, status, due_date,
                        proposal_id, project_code, source_transcript_id, assignee, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    item.get('task', 'Untitled task'),
                    f"Extracted from meeting transcript #{transcript_id}",
                    'action_item', priority, 'pending', item.get('due_date'),
                    proposal_id, project_code, transcript_id, item.get('assignee', 'us')
                ))
                task_ids.append(cursor.lastrowid)
            conn.commit()
        return task_ids

    def get_projects_for_dropdown(self) -> List[Dict]:
        """Get list of active projects for recorder dropdown"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT
                    COALESCE(pr.project_id, p.proposal_id) as id,
                    COALESCE(pr.project_code, p.project_code) as project_code,
                    COALESCE(pr.project_name, p.project_name) as project_name,
                    CASE WHEN pr.project_id IS NOT NULL THEN 'active_project' ELSE 'proposal' END as type
                FROM proposals p
                LEFT JOIN projects pr ON p.project_code = pr.project_code
                WHERE p.project_code IS NOT NULL
                ORDER BY CASE WHEN pr.project_id IS NOT NULL THEN 0 ELSE 1 END, p.project_code DESC
                LIMIT 100
            """)
            return [dict(row) for row in cursor.fetchall()]


_processor = None

def get_audio_processor(db_path: str = DB_PATH) -> AudioProcessor:
    global _processor
    if _processor is None:
        _processor = AudioProcessor(db_path)
    return _processor
