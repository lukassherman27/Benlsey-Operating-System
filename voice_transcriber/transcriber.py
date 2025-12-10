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
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS, SMTP_SERVER, SMTP_PORT, SMTP_USE_SSL,
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
# FEEDBACK & LEARNING SYSTEM
# =============================================================================

FEEDBACK_FILE = Path(__file__).parent / "feedback.json"

def load_feedback() -> Dict:
    """Load user feedback/corrections to improve future summaries."""
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE) as f:
            return json.load(f)
    return {"rules": [], "corrections": [], "participant_clarifications": {}}

def format_feedback_for_prompt(feedback: Dict) -> str:
    """Format feedback into instructions for the AI prompt."""
    sections = []

    if feedback.get("rules"):
        sections.append("## IMPORTANT RULES (learned from past corrections):")
        for rule in feedback["rules"]:
            sections.append(f"- {rule}")

    if feedback.get("formatting_rules"):
        sections.append("\n## FORMATTING RULES:")
        for rule in feedback["formatting_rules"]:
            sections.append(f"- {rule}")

    if feedback.get("corrections"):
        sections.append("\n## PAST MISTAKES TO AVOID:")
        for c in feedback["corrections"][-5:]:  # Last 5 corrections
            sections.append(f"- Error: {c['original_error']}")
            sections.append(f"  Correct: {c['correction']}")
            sections.append(f"  Lesson: {c['lesson']}\n")

    if feedback.get("participant_clarifications"):
        sections.append("\n## KNOWN PARTICIPANT CLARIFICATIONS:")
        for name, info in feedback["participant_clarifications"].items():
            sections.append(f"- {name}: {info}")

    if feedback.get("name_corrections"):
        sections.append("\n## NAME CORRECTIONS (fix these transcription errors):")
        for wrong, correct in feedback["name_corrections"].items():
            sections.append(f"- '{wrong}' should be '{correct}'")

    return "\n".join(sections)

def add_feedback(meeting_name: str, original_error: str, correction: str, lesson: str):
    """Add a new correction to the feedback file."""
    feedback = load_feedback()
    feedback["corrections"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "meeting": meeting_name,
        "original_error": original_error,
        "correction": correction,
        "lesson": lesson
    })
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback, f, indent=2)
    logger.info(f"Added feedback: {lesson}")

# =============================================================================
# AUDIO COMPRESSION & CHUNKING (for large/long files)
# =============================================================================

MAX_FILE_SIZE_MB = 24  # Whisper API limit is 25MB, leave buffer
CHUNK_DURATION_MINUTES = 20  # Split long files into chunks

def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    import subprocess
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)
        ], capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 0

def split_audio_into_chunks(audio_path: Path, chunk_minutes: int = CHUNK_DURATION_MINUTES) -> List[Path]:
    """
    Split audio file into chunks of specified duration.
    Returns list of chunk file paths.
    """
    import subprocess

    duration = get_audio_duration(audio_path)
    chunk_seconds = chunk_minutes * 60

    if duration <= chunk_seconds:
        return [audio_path]  # No splitting needed

    num_chunks = int(duration / chunk_seconds) + 1
    logger.info(f"Splitting {duration/60:.1f} min audio into {num_chunks} chunks...")

    chunks = []
    for i in range(num_chunks):
        start_time = i * chunk_seconds
        chunk_path = audio_path.parent / f"{audio_path.stem}_chunk{i+1}.m4a"

        try:
            result = subprocess.run([
                'ffmpeg', '-y', '-i', str(audio_path),
                '-ss', str(start_time), '-t', str(chunk_seconds),
                '-c:a', 'aac', '-b:a', '64k', '-ar', '16000',
                str(chunk_path)
            ], capture_output=True, text=True)

            if result.returncode == 0 and chunk_path.exists():
                chunks.append(chunk_path)
                logger.info(f"  Created chunk {i+1}/{num_chunks}")
            else:
                logger.error(f"Failed to create chunk {i+1}: {result.stderr}")
        except Exception as e:
            logger.error(f"Chunk creation error: {e}")

    return chunks if chunks else [audio_path]

def compress_audio_if_needed(audio_path: Path) -> Path:
    """
    Compress audio file if it exceeds Whisper's 25MB limit.
    Converts WAV to M4A using ffmpeg (if available).
    Returns path to compressed file, or original if no compression needed.
    """
    import subprocess

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)

    if file_size_mb <= MAX_FILE_SIZE_MB:
        logger.info(f"File size: {file_size_mb:.1f}MB (within limit)")
        return audio_path

    logger.info(f"File size: {file_size_mb:.1f}MB - compressing for Whisper API...")

    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("ffmpeg not installed - cannot compress. Try: brew install ffmpeg")
        logger.warning("Proceeding with original file (may fail if >25MB)")
        return audio_path

    # Create compressed version
    compressed_path = audio_path.with_suffix('.m4a')

    try:
        # Convert to M4A with good compression
        result = subprocess.run([
            'ffmpeg', '-y', '-i', str(audio_path),
            '-c:a', 'aac', '-b:a', '64k',  # Low bitrate for speech
            '-ar', '16000',  # 16kHz is fine for speech
            str(compressed_path)
        ], capture_output=True, text=True)

        if result.returncode == 0 and compressed_path.exists():
            new_size_mb = compressed_path.stat().st_size / (1024 * 1024)
            logger.info(f"Compressed: {file_size_mb:.1f}MB → {new_size_mb:.1f}MB")
            return compressed_path
        else:
            logger.error(f"Compression failed: {result.stderr}")
            return audio_path

    except Exception as e:
        logger.error(f"Compression error: {e}")
        return audio_path

# =============================================================================
# TRANSCRIPTION (OpenAI Whisper)
# =============================================================================

def transcribe_audio(audio_path: Path) -> str:
    """
    Transcribe audio file using OpenAI Whisper API.
    Automatically handles long recordings by chunking.
    Automatically compresses large files before sending.

    Args:
        audio_path: Path to audio file (m4a, mp3, wav, etc.)

    Returns:
        Transcribed text
    """
    logger.info(f"Transcribing: {audio_path.name}")

    # Check duration and split into chunks if needed (for long meetings)
    duration = get_audio_duration(audio_path)
    duration_minutes = duration / 60 if duration > 0 else 0

    if duration_minutes > CHUNK_DURATION_MINUTES:
        logger.info(f"Long recording detected: {duration_minutes:.1f} minutes")
        return transcribe_long_audio(audio_path)

    # For shorter files, compress if needed and transcribe directly
    file_to_transcribe = compress_audio_if_needed(audio_path)

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    with open(file_to_transcribe, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=audio_file,
            response_format="text"
        )

    # Clean up compressed file if we created one
    if file_to_transcribe != audio_path and file_to_transcribe.exists():
        file_to_transcribe.unlink()
        logger.info("Cleaned up compressed file")

    logger.info(f"Transcription complete: {len(transcript)} characters")
    return transcript


def transcribe_long_audio(audio_path: Path) -> str:
    """
    Transcribe long audio files by splitting into chunks.
    Handles recordings of any length.
    """
    # Split into chunks
    chunks = split_audio_into_chunks(audio_path)

    if len(chunks) == 1 and chunks[0] == audio_path:
        # Splitting failed or wasn't needed, try direct transcription
        return transcribe_audio(audio_path)

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    transcripts = []
    cleanup_files = []

    for i, chunk_path in enumerate(chunks):
        logger.info(f"Transcribing chunk {i+1}/{len(chunks)}...")

        try:
            with open(chunk_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=WHISPER_MODEL,
                    file=audio_file,
                    response_format="text"
                )
            transcripts.append(transcript)
            logger.info(f"  Chunk {i+1}: {len(transcript)} characters")

            # Mark for cleanup if it's a generated chunk file
            if chunk_path != audio_path:
                cleanup_files.append(chunk_path)

        except Exception as e:
            logger.error(f"Failed to transcribe chunk {i+1}: {e}")

    # Clean up chunk files
    for chunk_file in cleanup_files:
        try:
            chunk_file.unlink()
        except:
            pass
    logger.info(f"Cleaned up {len(cleanup_files)} chunk files")

    # Combine transcripts
    full_transcript = "\n\n".join(transcripts)
    logger.info(f"Combined transcript: {len(full_transcript)} characters from {len(chunks)} chunks")

    return full_transcript

# =============================================================================
# SUMMARIZATION (Claude)
# =============================================================================

def get_project_context_from_database(project_code: str) -> Optional[Dict]:
    """
    Fetch detailed project/proposal context from BDS database for email formatting.
    Returns None if project not found.

    This is used AFTER AI has identified a project to enrich the email with:
    - Project name, location, country
    - Client name and contact info
    - First contact date
    - Proposal date
    - Fee breakdown (if available)
    - Scope summary
    """
    if not BDS_DATABASE.exists() or not project_code:
        return None

    try:
        conn = sqlite3.connect(BDS_DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        context = {
            'project_code': project_code,
            'project_name': None,
            'client_name': None,
            'client_contact': None,
            'client_email': None,
            'location': None,
            'country': None,
            'first_contact_date': None,
            'proposal_date': None,
            'status': None,
            'fee_total': None,
            'fee_breakdown': None,
            'scope_summary': None,
        }

        # Try proposals table first
        cursor.execute("""
            SELECT
                project_name, client_company, contact_person, contact_email,
                location, country, first_contact_date, created_at, status
            FROM proposals
            WHERE project_code = ?
        """, (project_code,))

        row = cursor.fetchone()
        if row:
            context['project_name'] = row['project_name']
            context['client_name'] = row['client_company']
            context['client_contact'] = row['contact_person']
            context['client_email'] = row['contact_email']
            context['location'] = row['location']
            context['country'] = row['country']
            context['first_contact_date'] = row['first_contact_date']
            context['proposal_date'] = row['created_at'][:10] if row['created_at'] else None
            context['status'] = row['status']

        # Try projects table if not found in proposals
        if not context['project_name']:
            cursor.execute("""
                SELECT
                    p.project_title, p.city, p.country, p.status,
                    c.company_name
                FROM projects p
                LEFT JOIN clients c ON p.client_id = c.client_id
                WHERE p.project_code = ?
            """, (project_code,))

            row = cursor.fetchone()
            if row:
                context['project_name'] = row['project_title']
                context['client_name'] = row['company_name']
                context['location'] = row['city']
                context['country'] = row['country']
                context['status'] = row['status']

        # Try to get fee breakdown if available
        try:
            cursor.execute("""
                SELECT discipline, phase, phase_fee_usd
                FROM project_fee_breakdown
                WHERE project_code = ?
                ORDER BY discipline, phase
            """, (project_code,))

            fees = cursor.fetchall()
            if fees:
                fee_breakdown = {}
                total = 0
                for fee in fees:
                    disc = fee['discipline'] or 'Other'
                    if disc not in fee_breakdown:
                        fee_breakdown[disc] = 0
                    fee_breakdown[disc] += fee['phase_fee_usd'] or 0
                    total += fee['phase_fee_usd'] or 0
                if total > 0:
                    context['fee_breakdown'] = fee_breakdown
                    context['fee_total'] = total
        except Exception:
            # Fee breakdown table might not have data for this project
            pass

        conn.close()

        # Only return if we found something useful
        if context['project_name']:
            return context
        return None

    except Exception as e:
        logger.error(f"Error fetching project context: {e}")
        return None


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

    # Load user feedback/corrections for improved summaries
    feedback = load_feedback()
    feedback_context = format_feedback_for_prompt(feedback)
    if feedback_context:
        logger.info(f"Loaded {len(feedback.get('rules', []))} rules and {len(feedback.get('corrections', []))} corrections from feedback")

    prompt = f"""Analyze this meeting transcript and provide a structured summary.

## Recording Info:
- Filename: {audio_filename}
- Recorded: {datetime.now().strftime('%Y-%m-%d')}

## Transcript:
{transcript}

## DATABASE CONTEXT (use this to match projects, clients, and contacts mentioned)
{database_context}

{feedback_context}

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
    "detailed_summary": "A detailed, conversational summary of the meeting (3-6 paragraphs). Write it like you're explaining to a colleague who wasn't on the call what was discussed. Include: what the client's current situation is, what they need from us, what we explained about our process, any unique aspects of the project, synergies or rapport discussed, and what was agreed for next steps. Use natural language, not bullet points.",
    "action_items": [
        {{"task": "Description", "owner": "Person name", "deadline": "If mentioned or null", "owner_role": "Their role if known"}}
    ],
    "new_project_candidate": {{
        "is_new_project": true or false,
        "client_name": "Client/company or family name if new, null if unknown",
        "project_name": "If a name was given, else null",
        "location": "City, Country if mentioned",
        "scope": "Short freeform scope (e.g., 'interiors + facade + landscape for 10-story residence')",
        "approximate_size_sqft": "Number if mentioned, else null",
        "notes": "Any other pertinent details about the new opportunity"
    }},
    "detected_project": {{
        "code": "Project code if detected (e.g. BK-070), null if not",
        "name": "Project name",
        "confidence": 0.0 to 1.0,
        "reasoning": "Why this project was matched"
    }},
    "participants": [
        {{"name": "Person name", "role": "Their role/title and company", "type": "client/team/vendor/unknown"}}
    ],
    "meeting_type": "One of: Client Call, Internal Meeting, Site Visit, Vendor Call, Design Review, Other",
    "sentiment": "Positive, Neutral, or Negative overall tone",
    "follow_up_required": true or false,
    "follow_up_date": "Date/timeframe if mentioned (e.g., 'mid-January', 'next week'), null if not"
}}
```

**IMPORTANT GUIDELINES:**
- Match names to known contacts when possible
- For participants, include their role AND company (e.g., "Founder, Marcheval Advisory Group" not just "Founder")
- For Bensley team members, you can leave role empty unless they have a specific title
- The detailed_summary should read like a natural narrative, not a list of bullet points
- If no existing project is clearly mentioned but the conversation is about a new potential project/client, set new_project_candidate.is_new_project to true
- If no project is clearly mentioned, set detected_project.code to null
- Only include action items that were explicitly discussed
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
        # Ensure new_project_candidate exists for downstream consumers
        result.setdefault('new_project_candidate', {
            "is_new_project": False,
            "client_name": None,
            "project_name": None,
            "location": None,
            "scope": None,
            "approximate_size_sqft": None,
            "notes": None
        })
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
            "new_project_candidate": {
                "is_new_project": False,
                "client_name": None,
                "project_name": None,
                "location": None,
                "scope": None,
                "approximate_size_sqft": None,
                "notes": None
            },
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

        # Send (use SSL or STARTTLS based on config)
        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
        else:
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
    duration_seconds: float = None,
    include_full_transcript: bool = False,
    project_context: Dict = None
) -> str:
    """
    Format transcript and summary as HTML email.

    Args:
        transcript: Full transcript text
        summary: AI-generated summary dict
        audio_filename: Original audio filename
        duration_seconds: Recording duration
        include_full_transcript: If False, omit full transcript from email body (it's in attachment)
        project_context: Optional dict with project details from database (for background box)
    """

    # Project Background Box (shown if we have project context from database)
    project_background = ""
    if project_context and project_context.get('project_name'):
        ctx = project_context

        # Build fee info if available
        fee_info = ""
        if ctx.get('fee_total'):
            fee_info = f"<p style='margin-bottom: 0;'><strong>Fee:</strong> ${ctx['fee_total']:,.0f}"
            if ctx.get('fee_breakdown'):
                breakdown_parts = [f"{disc} (${amt:,.0f})" for disc, amt in ctx['fee_breakdown'].items()]
                fee_info += f" — {' + '.join(breakdown_parts)}"
            fee_info += "</p>"

        # Build timeline info
        timeline_info = ""
        if ctx.get('first_contact_date') or ctx.get('proposal_date'):
            timeline_parts = []
            if ctx.get('first_contact_date'):
                timeline_parts.append(f"First contact: {ctx['first_contact_date']}")
            if ctx.get('proposal_date'):
                timeline_parts.append(f"Proposal sent: {ctx['proposal_date']}")
            timeline_info = f"<p style='margin-bottom: 10px;'><strong>Timeline:</strong> {'. '.join(timeline_parts)}</p>"

        # Build location info
        location_parts = [p for p in [ctx.get('location'), ctx.get('country')] if p]
        location_str = ', '.join(location_parts) if location_parts else 'TBD'

        project_background = f"""
        <div style="background: #f0f7ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #1a73e8;">
            <h3 style="margin-top: 0; color: #1a73e8;">Project Background</h3>
            <p style="margin-bottom: 10px;"><strong>Project:</strong> {ctx.get('project_code')} — {ctx.get('project_name')}</p>
            <p style="margin-bottom: 10px;"><strong>Client:</strong> {ctx.get('client_name') or 'TBD'}{f" ({ctx.get('client_contact')})" if ctx.get('client_contact') and ctx.get('client_contact') != ctx.get('client_name') else ''}</p>
            <p style="margin-bottom: 10px;"><strong>Location:</strong> {location_str}</p>
            {timeline_info}
            {fee_info}
        </div>
        """

    # Simple project tag (fallback if no full context but AI detected a project)
    project_info = ""
    if not project_background and summary.get('detected_project', {}).get('code'):
        proj = summary['detected_project']
        project_info = f"""
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #4caf50;">
            <strong>🎯 Project:</strong> {proj['code']} - {proj.get('name', '')}<br>
            <small style="color: #666;">{proj.get('reasoning', '')}</small>
        </div>
        """

    action_items_html = ""
    if summary.get('action_items'):
        items = "".join([
            f"<li><strong>{item.get('task', 'Task')}</strong>"
            f"<br><span style='color: #666; font-size: 13px;'>→ {item.get('owner', 'TBD')}"
            f"{' (by ' + item.get('deadline') + ')' if item.get('deadline') else ''}</span></li>"
            for item in summary['action_items']
        ])
        action_items_html = f"""
        <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ff9800;">
            <h3 style="margin-top: 0; color: #e65100;">📋 Action Items</h3>
            <ul style="margin-bottom: 0;">{items}</ul>
        </div>
        """

    new_project_html = ""
    new_proj = summary.get('new_project_candidate', {})
    if new_proj and new_proj.get('is_new_project'):
        new_project_html = f"""
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #2196f3;">
            <h3 style="margin-top: 0; color: #1565c0;">🆕 New Project Opportunity</h3>
            <p style="margin-bottom: 0;">
                <strong>Client:</strong> {new_proj.get('client_name') or 'Unknown'}<br>
                <strong>Project:</strong> {new_proj.get('project_name') or 'Not named yet'}<br>
                <strong>Location:</strong> {new_proj.get('location') or 'TBD'}<br>
                <strong>Scope:</strong> {new_proj.get('scope') or 'TBD'}<br>
                {f"<strong>Notes:</strong> {new_proj.get('notes')}" if new_proj.get('notes') else ''}
            </p>
        </div>
        """

    key_points_html = ""
    if summary.get('key_points'):
        points = "".join([f"<li>{point}</li>" for point in summary['key_points']])
        key_points_html = f"""
        <h3 style="color: #1a73e8;">💡 Key Points</h3>
        <ul>{points}</ul>
        """

    duration_str = ""
    if duration_seconds:
        mins = int(duration_seconds // 60)
        secs = int(duration_seconds % 60)
        duration_str = f" ({mins}:{secs:02d})"

    # Participants list
    participants = summary.get('participants', [])
    participants_str = ', '.join([
        f"{p.get('name', p)} ({p.get('role', 'Unknown')})" if isinstance(p, dict) else str(p)
        for p in participants
    ]) if participants else 'Unknown'

    # Full transcript section (optional)
    transcript_section = ""
    if include_full_transcript:
        transcript_section = f"""
        <h3 style="color: #1a73e8;">📝 Full Transcript</h3>
        <div style="background: #fafafa; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-size: 13px; max-height: 500px; overflow-y: auto; border: 1px solid #e0e0e0;">
{transcript}
        </div>
        """
    else:
        transcript_section = """
        <p style="color: #666; font-style: italic; font-size: 13px;">
            📎 Full transcript attached as text file.
        </p>
        """

    # Get summary text - support both old 'summary' and new 'detailed_summary' fields
    summary_text = summary.get('detailed_summary') or summary.get('summary', 'No summary generated.')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; font-size: 22px; }}
            h2 {{ color: #333; font-size: 18px; }}
            h3 {{ color: #1a73e8; margin-top: 25px; font-size: 16px; }}
            .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .summary p {{ margin-bottom: 12px; }}
            .summary p:last-child {{ margin-bottom: 0; }}
            .meta {{ color: #5f6368; font-size: 13px; margin-bottom: 15px; }}
            ul {{ padding-left: 20px; }}
            li {{ margin: 8px 0; }}
        </style>
    </head>
    <body>
        <h1>🎤 Meeting Summary</h1>

        <div class="meta">
            <strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}{duration_str}<br>
            <strong>Type:</strong> {summary.get('meeting_type', 'Unknown')}<br>
            <strong>Participants:</strong> {participants_str}
        </div>

        {project_background}
        {project_info}
        {new_project_html}

        <div class="summary">
            <h2>Meeting Summary</h2>
            {summary_text}
        </div>

        {key_points_html}
        {action_items_html}
        {transcript_section}

        <hr style="margin-top: 30px; border: none; border-top: 1px solid #e0e0e0;">
        <p style="color: #9e9e9e; font-size: 11px;">
            Automatically generated by BDS Voice Transcriber
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
    new_project = summary.get('new_project_candidate', {})

    if new_project.get('is_new_project'):
        title = "New Project Lead"
        subtitle = new_project.get('client_name') or audio_filename
    elif project_code:
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
            summary.get('detailed_summary') or summary.get('summary', ''),
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
        # Fetch project context from database if a project was detected
        project_context = None
        detected_code = summary.get('detected_project', {}).get('code')
        if detected_code:
            project_context = get_project_context_from_database(detected_code)
            if project_context:
                logger.info(f"Loaded project context for {detected_code}: {project_context.get('project_name')}")

        email_html = format_email_html(
            transcript,
            summary,
            audio_path.name,
            include_full_transcript=False,
            project_context=project_context
        )

        # Create transcript attachment
        transcript_bytes = transcript.encode('utf-8')
        attachments = [
            (f"{audio_path.stem}_transcript.txt", transcript_bytes)
        ]

        # Build subject line
        subject = "Meeting Summary"
        if summary.get('new_project_candidate', {}).get('is_new_project'):
            new_proj = summary['new_project_candidate']
            subject = f"[New Project] {new_proj.get('client_name') or 'Unknown Client'}"
        elif detected_code:
            project_name = (project_context or {}).get('project_name') or summary.get('detected_project', {}).get('name', '')
            subject = f"[{detected_code}] Meeting Summary: {project_name}"

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
