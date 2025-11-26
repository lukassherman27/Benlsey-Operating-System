#!/usr/bin/env python3
"""
Voice Memo Transcriber - Automatic Meeting Transcription Service

Watches for new voice memos, transcribes them, generates AI summaries,
and emails results while saving to the BDS database.

Usage:
    python transcriber.py          # Run in foreground
    python transcriber.py --once   # Process once and exit
    python transcriber.py --test   # Test with a specific file
"""

import os
import sys
import json
import time
import sqlite3
import smtplib
import logging
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, List, Tuple

# Third-party imports
try:
    import openai
except ImportError:
    print("Missing required packages. Run: pip install openai")
    sys.exit(1)

# Optional: Anthropic for Claude summaries (falls back to OpenAI if not available)
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Local imports
from config import (
    OPENAI_API_KEY, ANTHROPIC_API_KEY,
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS, SMTP_SERVER, SMTP_PORT,
    VOICE_MEMOS_FOLDER, OUTPUT_FOLDER, BDS_DATABASE,
    CHECK_INTERVAL, MIN_FILE_AGE, WHISPER_MODEL, CLAUDE_MODEL,
    AUTO_DETECT_PROJECT, PROJECT_MATCH_CONFIDENCE
)

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / 'transcriber.log')
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# PROCESSED FILES TRACKING
# =============================================================================

PROCESSED_FILE = Path(__file__).parent / "processed_files.json"

def load_processed_files() -> set:
    """Load set of already processed file hashes."""
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE) as f:
            return set(json.load(f))
    return set()

def save_processed_file(file_hash: str):
    """Mark a file as processed."""
    processed = load_processed_files()
    processed.add(file_hash)
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(list(processed), f)

def get_file_hash(filepath: Path) -> str:
    """Generate unique hash for a file based on path and modification time."""
    stat = filepath.stat()
    return hashlib.md5(f"{filepath}:{stat.st_mtime}:{stat.st_size}".encode()).hexdigest()

# =============================================================================
# TRANSCRIPTION (OpenAI Whisper)
# =============================================================================

def transcribe_audio(audio_path: Path) -> str:
    """
    Transcribe audio file using OpenAI Whisper API.

    Args:
        audio_path: Path to audio file (m4a, mp3, wav, etc.)

    Returns:
        Transcribed text
    """
    logger.info(f"Transcribing: {audio_path.name}")

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=audio_file,
            response_format="text"
        )

    logger.info(f"Transcription complete: {len(transcript)} characters")
    return transcript

# =============================================================================
# SUMMARIZATION (Claude)
# =============================================================================

def get_all_context_from_database() -> Dict:
    """
    Fetch ALL relevant context from BDS database for AI matching.
    This is dynamic - pulls everything currently in the database.

    Returns dict with: projects, proposals, contacts, team_members, clients
    """
    context = {
        'projects': [],
        'proposals': [],
        'contacts': [],
        'team_members': [],
        'clients': []
    }

    if not BDS_DATABASE.exists():
        logger.warning(f"BDS database not found at {BDS_DATABASE}")
        return context

    try:
        conn = sqlite3.connect(BDS_DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # ===========================================
        # 1. ALL PROJECTS (active and recent)
        # ===========================================
        cursor.execute("""
            SELECT
                p.project_id,
                p.project_code,
                p.project_title,
                COALESCE(c.company_name, '') as client_name,
                p.status,
                p.country,
                p.city,
                p.project_type
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.client_id
            ORDER BY p.project_code DESC
        """)

        for row in cursor.fetchall():
            context['projects'].append({
                'id': row['project_id'],
                'code': row['project_code'],
                'name': row['project_title'],
                'client': row['client_name'],
                'status': row['status'],
                'country': row['country'],
                'city': row['city'],
                'type': row['project_type']
            })

        logger.info(f"Loaded {len(context['projects'])} projects")

        # ===========================================
        # 2. ALL PROPOSALS
        # ===========================================
        cursor.execute("""
            SELECT
                proposal_id,
                project_code,
                project_name,
                client_company,
                status,
                country,
                location
            FROM proposals
            ORDER BY project_code DESC
        """)

        for row in cursor.fetchall():
            context['proposals'].append({
                'id': row['proposal_id'],
                'code': row['project_code'],
                'name': row['project_name'],
                'client': row['client_company'],
                'status': row['status'],
                'country': row['country'],
                'location': row['location']
            })

        logger.info(f"Loaded {len(context['proposals'])} proposals")

        # ===========================================
        # 3. ALL CONTACTS
        # ===========================================
        cursor.execute("""
            SELECT DISTINCT
                co.contact_id,
                co.name,
                co.email,
                co.role,
                COALESCE(cl.company_name, '') as company
            FROM contacts co
            LEFT JOIN clients cl ON co.client_id = cl.client_id
            WHERE co.name IS NOT NULL AND co.name != ''
            ORDER BY co.name
        """)

        for row in cursor.fetchall():
            context['contacts'].append({
                'id': row['contact_id'],
                'name': row['name'],
                'email': row['email'],
                'company': row['company'],
                'role': row['role']
            })

        logger.info(f"Loaded {len(context['contacts'])} contacts")

        # ===========================================
        # 4. ALL CLIENTS/COMPANIES
        # ===========================================
        cursor.execute("""
            SELECT
                client_id,
                company_name,
                country,
                industry
            FROM clients
            WHERE company_name IS NOT NULL
            ORDER BY company_name
        """)

        for row in cursor.fetchall():
            context['clients'].append({
                'id': row['client_id'],
                'name': row['company_name'],
                'country': row['country'],
                'industry': row['industry']
            })

        logger.info(f"Loaded {len(context['clients'])} clients/companies")

        # ===========================================
        # 5. TEAM MEMBERS (if table exists)
        # ===========================================
        try:
            cursor.execute("""
                SELECT DISTINCT name, role, email
                FROM team_members
                WHERE name IS NOT NULL
                ORDER BY name
            """)

            for row in cursor.fetchall():
                context['team_members'].append({
                    'name': row['name'],
                    'role': row['role'],
                    'email': row['email']
                })

            logger.info(f"Loaded {len(context['team_members'])} team members")
        except:
            # Table might not exist
            pass

        conn.close()

    except Exception as e:
        logger.error(f"Error loading database context: {e}")

    return context


def format_context_for_prompt(context: Dict, max_items_per_category: int = 200) -> str:
    """
    Format database context for AI prompt.
    Intelligently truncates if needed while keeping most relevant items.
    """
    sections = []

    # Projects (prioritize active/recent)
    if context['projects']:
        projects = context['projects'][:max_items_per_category]
        project_lines = [
            f"- {p['code']}: {p['name']} | Client: {p['client']} | {p.get('city', '')}, {p.get('country', '')} | Status: {p['status']}"
            for p in projects
        ]
        sections.append(f"## Active Projects ({len(context['projects'])} total)\n" + "\n".join(project_lines))

    # Proposals
    if context['proposals']:
        proposals = context['proposals'][:max_items_per_category]
        proposal_lines = [
            f"- {p['code']}: {p['name']} | Client: {p['client']} | {p.get('location', '')}, {p.get('country', '')} | Status: {p['status']}"
            for p in proposals
        ]
        sections.append(f"## Proposals ({len(context['proposals'])} total)\n" + "\n".join(proposal_lines))

    # Clients/Companies (important for matching)
    if context['clients']:
        clients = context['clients'][:max_items_per_category]
        client_lines = [
            f"- {c['name']} ({c.get('country', 'Unknown')})"
            for c in clients
        ]
        sections.append(f"## Clients/Companies ({len(context['clients'])} total)\n" + "\n".join(client_lines))

    # Contacts
    if context['contacts']:
        contacts = context['contacts'][:max_items_per_category]
        contact_lines = [
            f"- {c['name']}: {c.get('role', 'Unknown role')} at {c.get('company', 'Unknown')}"
            for c in contacts
        ]
        sections.append(f"## Known Contacts ({len(context['contacts'])} total)\n" + "\n".join(contact_lines))

    # Team members
    if context['team_members']:
        team = context['team_members'][:50]  # Team is usually smaller
        team_lines = [
            f"- {t['name']}: {t.get('role', 'Team Member')}"
            for t in team
        ]
        sections.append(f"## Bensley Team Members ({len(context['team_members'])} total)\n" + "\n".join(team_lines))

    return "\n\n".join(sections)

def summarize_transcript(transcript: str, audio_filename: str) -> Dict:
    """
    Generate AI summary of transcript using OpenAI GPT-4 or Claude.

    Returns dict with:
        - summary: Brief executive summary
        - key_points: Bullet points of main topics
        - action_items: Any action items mentioned
        - detected_project: Best matching project (if found)
        - participants: Detected participants
    """
    logger.info("Generating AI summary...")

    # Get ALL context from database (dynamic - grows as database grows)
    context = get_all_context_from_database()

    # Format context for AI prompt
    database_context = format_context_for_prompt(context, max_items_per_category=200)

    # Log what we loaded
    total_items = sum([
        len(context['projects']),
        len(context['proposals']),
        len(context['contacts']),
        len(context['clients']),
        len(context['team_members'])
    ])
    logger.info(f"Total context items loaded: {total_items} (projects: {len(context['projects'])}, proposals: {len(context['proposals'])}, contacts: {len(context['contacts'])}, clients: {len(context['clients'])})")

    prompt = f"""Analyze this meeting transcript and provide a structured summary.

## Recording Info:
- Filename: {audio_filename}
- Recorded: {datetime.now().strftime('%Y-%m-%d')}

## Transcript:
{transcript}

## DATABASE CONTEXT (use this to match projects, clients, and contacts mentioned)
{database_context}

## Instructions:
Analyze the transcript carefully. Match any mentioned names to the Known Contacts or Team Members lists.

**PROJECT MATCHING PRIORITY (CRITICAL):**
1. **Location/Country is the STRONGEST signal** - If someone says "Turkey" or "Bodrum", match to a Turkey project
2. Project code (BK-XXX) if explicitly mentioned
3. Exact project name match
4. Client company name
5. Brand name (e.g., "Cheval Blanc") is WEAK - many brands have multiple locations

**IMPORTANT:** A Turkey project mentioned = match to a project in Turkey, NOT a similar-sounding project elsewhere.
Search BOTH Active Projects AND Proposals lists for matches.

Provide your analysis in the following JSON format:

```json
{{
    "summary": "2-3 sentence executive summary of the meeting",
    "key_points": [
        "Key point 1",
        "Key point 2",
        "Key point 3"
    ],
    "action_items": [
        {{"task": "Description", "owner": "Person name", "deadline": "If mentioned", "owner_role": "Their role if known"}}
    ],
    "detected_project": {{
        "code": "Project code if detected (e.g. BK-070), null if not",
        "name": "Project name",
        "confidence": 0.0 to 1.0,
        "reasoning": "Why this project was matched"
    }},
    "participants": [
        {{"name": "Person name", "role": "Their role", "type": "client/team/vendor/unknown"}}
    ],
    "meeting_type": "One of: Client Call, Internal Meeting, Site Visit, Vendor Call, Design Review, Other",
    "sentiment": "Positive, Neutral, or Negative overall tone",
    "follow_up_required": true or false,
    "next_meeting_mentioned": "Date/time if mentioned, null if not"
}}
```

Be accurate and concise. Match names to known contacts when possible.
If no project is clearly mentioned, set detected_project.code to null.
Only include action items that were explicitly discussed.
"""

    # Use Claude if available and configured, otherwise use OpenAI
    use_claude = HAS_ANTHROPIC and ANTHROPIC_API_KEY

    if use_claude:
        logger.info("Using Claude for summarization...")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text
        model_used = CLAUDE_MODEL
    else:
        logger.info("Using OpenAI GPT-4 for summarization...")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        response_text = response.choices[0].message.content
        model_used = "gpt-4o"

    # Extract JSON from response (handle markdown code blocks)
    if "```json" in response_text:
        json_str = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        json_str = response_text.split("```")[1].split("```")[0]
    else:
        json_str = response_text

    try:
        result = json.loads(json_str.strip())
        result['model_used'] = model_used
        logger.info(f"Summary generated with {model_used}. Project detected: {result.get('detected_project', {}).get('code', 'None')}")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        # Return basic structure
        return {
            "summary": response_text[:500],
            "key_points": [],
            "action_items": [],
            "detected_project": {"code": None, "confidence": 0, "reasoning": "Parse error"},
            "participants": [],
            "meeting_type": "Unknown",
            "sentiment": "Neutral",
            "model_used": model_used
        }

# =============================================================================
# EMAIL SENDING
# =============================================================================

def send_email(
    subject: str,
    body_html: str,
    attachments: List[Tuple[str, bytes]] = None
) -> bool:
    """
    Send email with transcript and summary.

    Args:
        subject: Email subject
        body_html: HTML body content
        attachments: List of (filename, content) tuples

    Returns:
        True if sent successfully
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        logger.warning("Email not configured. Skipping email send.")
        return False

    logger.info(f"Sending email to {EMAIL_RECIPIENTS}")

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = ", ".join(EMAIL_RECIPIENTS)

        # HTML body
        msg.attach(MIMEText(body_html, 'html'))

        # Attachments
        if attachments:
            for filename, content in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)

        # Send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info("Email sent successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def format_email_html(
    transcript: str,
    summary: Dict,
    audio_filename: str,
    duration_seconds: float = None
) -> str:
    """Format transcript and summary as HTML email."""

    project_info = ""
    if summary.get('detected_project', {}).get('code'):
        proj = summary['detected_project']
        confidence_pct = int(proj.get('confidence', 0) * 100)
        project_info = f"""
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <strong>Detected Project:</strong> {proj['code']}<br>
            <strong>Confidence:</strong> {confidence_pct}%<br>
            <small>{proj.get('reasoning', '')}</small>
        </div>
        """

    action_items_html = ""
    if summary.get('action_items'):
        items = "".join([
            f"<li><strong>{item.get('task', 'Task')}</strong>"
            f"{' - ' + item.get('owner', '') if item.get('owner') else ''}"
            f"{' (Due: ' + item.get('deadline') + ')' if item.get('deadline') else ''}</li>"
            for item in summary['action_items']
        ])
        action_items_html = f"""
        <h3>Action Items</h3>
        <ul>{items}</ul>
        """

    key_points_html = ""
    if summary.get('key_points'):
        points = "".join([f"<li>{point}</li>" for point in summary['key_points']])
        key_points_html = f"""
        <h3>Key Points</h3>
        <ul>{points}</ul>
        """

    duration_str = ""
    if duration_seconds:
        mins = int(duration_seconds // 60)
        secs = int(duration_seconds % 60)
        duration_str = f"<br><strong>Duration:</strong> {mins}:{secs:02d}"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
            h2 {{ color: #5f6368; }}
            h3 {{ color: #1a73e8; margin-top: 25px; }}
            .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #1a73e8; }}
            .transcript {{ background: #fafafa; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-size: 14px; max-height: 500px; overflow-y: auto; }}
            .meta {{ color: #5f6368; font-size: 14px; }}
            ul {{ padding-left: 20px; }}
            li {{ margin: 8px 0; }}
        </style>
    </head>
    <body>
        <h1>Meeting Transcript</h1>

        <div class="meta">
            <strong>Recording:</strong> {audio_filename}<br>
            <strong>Processed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}
            {duration_str}<br>
            <strong>Type:</strong> {summary.get('meeting_type', 'Unknown')}<br>
            <strong>Participants:</strong> {', '.join([p.get('name', p) if isinstance(p, dict) else str(p) for p in summary.get('participants', ['Unknown'])])}
        </div>

        {project_info}

        <div class="summary">
            <h2>Summary</h2>
            <p>{summary.get('summary', 'No summary generated.')}</p>
        </div>

        {key_points_html}
        {action_items_html}

        <h3>Full Transcript</h3>
        <div class="transcript">{transcript}</div>

        <hr style="margin-top: 30px; border: none; border-top: 1px solid #e0e0e0;">
        <p style="color: #9e9e9e; font-size: 12px;">
            Automatically generated by BDS Voice Transcriber<br>
            Powered by OpenAI Whisper + Claude AI
        </p>
    </body>
    </html>
    """

# =============================================================================
# MACOS NOTIFICATION
# =============================================================================

def send_macos_notification(audio_filename: str, summary: Dict):
    """Send macOS notification when transcription is complete."""
    import subprocess

    project_code = summary.get('detected_project', {}).get('code', '')
    project_name = summary.get('detected_project', {}).get('name', '')
    meeting_summary = summary.get('summary', 'Transcription complete')[:100]

    if project_code:
        title = f"Transcribed: {project_code}"
        subtitle = project_name
    else:
        title = "Meeting Transcribed"
        subtitle = audio_filename

    # Use osascript to show notification
    script = f'''
    display notification "{meeting_summary}..." with title "{title}" subtitle "{subtitle}" sound name "Glass"
    '''

    try:
        subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
        logger.info("macOS notification sent")
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")

# =============================================================================
# DATABASE STORAGE
# =============================================================================

def save_to_database(
    audio_path: Path,
    transcript: str,
    summary: Dict,
    project_id: Optional[int] = None
) -> Optional[int]:
    """
    Save transcript to BDS database.

    Returns the ID of the inserted record, or None if failed.
    """
    if not BDS_DATABASE.exists():
        logger.warning("BDS database not found. Skipping database save.")
        return None

    try:
        conn = sqlite3.connect(BDS_DATABASE)
        cursor = conn.cursor()

        # Check if meeting_transcripts table exists, create if not
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meeting_transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_filename TEXT,
                audio_path TEXT,
                transcript TEXT,
                summary TEXT,
                key_points TEXT,
                action_items TEXT,
                detected_project_id INTEGER,
                detected_project_code TEXT,
                match_confidence REAL,
                meeting_type TEXT,
                participants TEXT,
                sentiment TEXT,
                duration_seconds REAL,
                recorded_date TEXT,
                processed_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (detected_project_id) REFERENCES projects(id)
            )
        """)

        # Insert record
        cursor.execute("""
            INSERT INTO meeting_transcripts (
                audio_filename, audio_path, transcript, summary,
                key_points, action_items, detected_project_id, detected_project_code,
                match_confidence, meeting_type, participants, sentiment,
                processed_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audio_path.name,
            str(audio_path),
            transcript,
            summary.get('summary', ''),
            json.dumps(summary.get('key_points', [])),
            json.dumps(summary.get('action_items', [])),
            project_id,
            summary.get('detected_project', {}).get('code'),
            summary.get('detected_project', {}).get('confidence', 0),
            summary.get('meeting_type', 'Unknown'),
            json.dumps(summary.get('participants', [])),
            summary.get('sentiment', 'Neutral'),
            datetime.now().isoformat()
        ))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Saved to database with ID: {record_id}")
        return record_id

    except Exception as e:
        logger.error(f"Failed to save to database: {e}")
        return None

# =============================================================================
# LOCAL FILE STORAGE
# =============================================================================

def save_transcript_locally(
    audio_path: Path,
    transcript: str,
    summary: Dict
) -> Path:
    """Save transcript and summary to local files."""

    # Ensure output folder exists
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    # Create filename from audio filename
    base_name = audio_path.stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    # Save transcript
    transcript_path = OUTPUT_FOLDER / f"{base_name}_{timestamp}_transcript.txt"
    with open(transcript_path, 'w') as f:
        f.write(f"MEETING TRANSCRIPT\n")
        f.write(f"==================\n")
        f.write(f"Source: {audio_path.name}\n")
        f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"\n")
        f.write(transcript)

    # Save summary
    summary_path = OUTPUT_FOLDER / f"{base_name}_{timestamp}_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Saved locally to: {OUTPUT_FOLDER}")
    return transcript_path

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_audio_file(audio_path: Path) -> bool:
    """
    Process a single audio file: transcribe, summarize, email, save.

    Returns True if successful.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {audio_path.name}")
    logger.info(f"{'='*60}")

    try:
        # 1. Transcribe
        transcript = transcribe_audio(audio_path)

        if not transcript or len(transcript.strip()) < 10:
            logger.warning("Transcript too short or empty. Skipping.")
            return False

        # 2. Generate summary
        summary = summarize_transcript(transcript, audio_path.name)

        # 3. Save locally
        save_transcript_locally(audio_path, transcript, summary)

        # 4. Save to database
        project_id = None
        if AUTO_DETECT_PROJECT and summary.get('detected_project', {}).get('code'):
            # Look up project ID
            if BDS_DATABASE.exists():
                try:
                    conn = sqlite3.connect(BDS_DATABASE)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id FROM projects WHERE project_code = ?",
                        (summary['detected_project']['code'],)
                    )
                    row = cursor.fetchone()
                    if row:
                        project_id = row[0]
                    conn.close()
                except Exception:
                    pass

        save_to_database(audio_path, transcript, summary, project_id)

        # 5. Send email
        email_html = format_email_html(transcript, summary, audio_path.name)

        # Create transcript attachment
        transcript_bytes = transcript.encode('utf-8')
        attachments = [
            (f"{audio_path.stem}_transcript.txt", transcript_bytes)
        ]

        subject = f"Meeting Transcript: {audio_path.stem}"
        if summary.get('detected_project', {}).get('code'):
            subject = f"[{summary['detected_project']['code']}] {subject}"

        send_email(subject, email_html, attachments)

        # 5b. Send macOS notification
        send_macos_notification(audio_path.name, summary)

        # 6. Mark as processed
        save_processed_file(get_file_hash(audio_path))

        logger.info(f"Successfully processed: {audio_path.name}")
        return True

    except Exception as e:
        logger.error(f"Error processing {audio_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_new_recordings() -> List[Path]:
    """Find new, unprocessed voice memos."""

    if not VOICE_MEMOS_FOLDER.exists():
        logger.warning(f"Voice Memos folder not found: {VOICE_MEMOS_FOLDER}")
        return []

    processed = load_processed_files()
    new_files = []

    # Look for audio files
    audio_extensions = {'.m4a', '.mp3', '.wav', '.mp4', '.webm', '.ogg'}

    for audio_file in VOICE_MEMOS_FOLDER.iterdir():
        if audio_file.suffix.lower() not in audio_extensions:
            continue

        # Check if already processed
        file_hash = get_file_hash(audio_file)
        if file_hash in processed:
            continue

        # Check file age (avoid files still being synced)
        file_age = time.time() - audio_file.stat().st_mtime
        if file_age < MIN_FILE_AGE:
            logger.debug(f"File too new, waiting: {audio_file.name}")
            continue

        new_files.append(audio_file)

    return new_files

def run_watcher():
    """Run continuous watcher for new voice memos."""
    logger.info("Starting Voice Memo Transcriber...")
    logger.info(f"Watching: {VOICE_MEMOS_FOLDER}")
    logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
    logger.info(f"Output folder: {OUTPUT_FOLDER}")
    logger.info("-" * 60)

    # Validate configuration
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set! Set it in config.py or environment.")
        sys.exit(1)

    if not ANTHROPIC_API_KEY:
        logger.info("ANTHROPIC_API_KEY not set - will use OpenAI GPT-4 for summaries")

    while True:
        try:
            new_recordings = find_new_recordings()

            if new_recordings:
                logger.info(f"Found {len(new_recordings)} new recording(s)")
                for audio_path in new_recordings:
                    process_audio_file(audio_path)

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\nStopping watcher...")
            break
        except Exception as e:
            logger.error(f"Watcher error: {e}")
            time.sleep(CHECK_INTERVAL)

def run_once():
    """Process any pending recordings once and exit."""
    logger.info("Running single check for new recordings...")

    new_recordings = find_new_recordings()

    if not new_recordings:
        logger.info("No new recordings found.")
        return

    logger.info(f"Found {len(new_recordings)} new recording(s)")
    for audio_path in new_recordings:
        process_audio_file(audio_path)

def test_file(filepath: str):
    """Test transcription with a specific file."""
    audio_path = Path(filepath)

    if not audio_path.exists():
        logger.error(f"File not found: {filepath}")
        sys.exit(1)

    logger.info(f"Testing with file: {audio_path}")
    process_audio_file(audio_path)

# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Voice Memo Transcriber - Automatic meeting transcription"
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help="Process pending recordings once and exit"
    )
    parser.add_argument(
        '--test',
        type=str,
        metavar='FILE',
        help="Test with a specific audio file"
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help="Show current status and configuration"
    )

    args = parser.parse_args()

    if args.status:
        print("\n=== Voice Memo Transcriber Status ===\n")
        print(f"Voice Memos Folder: {VOICE_MEMOS_FOLDER}")
        print(f"  Exists: {VOICE_MEMOS_FOLDER.exists()}")
        print(f"\nOutput Folder: {OUTPUT_FOLDER}")
        print(f"  Exists: {OUTPUT_FOLDER.exists()}")
        print(f"\nBDS Database: {BDS_DATABASE}")
        print(f"  Exists: {BDS_DATABASE.exists()}")
        print(f"\nOpenAI API Key: {'Set' if OPENAI_API_KEY else 'NOT SET'}")
        print(f"Anthropic API Key: {'Set' if ANTHROPIC_API_KEY else 'NOT SET'}")
        print(f"\nEmail Configured: {'Yes' if EMAIL_SENDER and EMAIL_PASSWORD else 'No'}")
        print(f"  Sender: {EMAIL_SENDER or 'Not set'}")
        print(f"  Recipients: {EMAIL_RECIPIENTS}")

        processed = load_processed_files()
        print(f"\nProcessed Files: {len(processed)}")

        if VOICE_MEMOS_FOLDER.exists():
            recordings = list(VOICE_MEMOS_FOLDER.glob('*.m4a'))
            print(f"Voice Memos Found: {len(recordings)}")

        return

    if args.test:
        test_file(args.test)
    elif args.once:
        run_once()
    else:
        run_watcher()

if __name__ == "__main__":
    main()
