"""
Transcript Consolidation Service

Consolidates chunked meeting transcripts into single records and generates smart titles.

Problem: Long meetings are split into 20-minute chunks for Whisper transcription limits.
Each chunk gets stored as a SEPARATE row in meeting_transcripts table with duplicates.

Solution:
1. Group chunks by base filename (strip _chunk1, _chunk2 suffix)
2. Deduplicate rows (keep best content from each chunk)
3. Merge transcripts into one consolidated record per meeting
4. Generate smart title using GPT: "{Project Name} - {Meeting Topic}"
5. Enrich with proposal context when matched
6. Match participant names against contacts database

Created: 2025-12-02
Updated: 2025-12-02 - Added participant matching from contacts
"""

import sqlite3
import re
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from collections import defaultdict

# Default database path
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


class TranscriptConsolidationService:
    """Consolidates chunked transcripts and generates smart titles"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.client = OpenAI()
        self.stats = {
            'meetings_identified': 0,
            'chunks_processed': 0,
            'duplicates_removed': 0,
            'titles_generated': 0,
            'proposals_matched': 0,
            'participants_matched': 0,
            'errors': []
        }
        # Cache contacts for fuzzy matching
        self._contacts_cache = None

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def _extract_base_filename(self, filename: str) -> str:
        """
        Extract base meeting name from chunked filename.

        Examples:
            meeting_20251127_122841_chunk1.m4a -> meeting_20251127_122841
            meeting_20251127_122841_chunk2.m4a -> meeting_20251127_122841
            meeting_20251127_122841.wav -> meeting_20251127_122841
            meeting_20251127_122841_chunk1_part1.m4a -> meeting_20251127_122841
        """
        # Remove extension
        name = re.sub(r'\.(m4a|wav|mp3|mp4|webm|ogg)$', '', filename, flags=re.IGNORECASE)

        # Remove chunk and part suffixes
        name = re.sub(r'_chunk\d+(_part\d+)?$', '', name)

        return name

    def _get_chunk_order(self, filename: str) -> Tuple[int, int]:
        """
        Extract chunk and part number for ordering.

        Returns (chunk_num, part_num) tuple for sorting.
        Base files return (0, 0).
        """
        # Look for _chunk{N} pattern
        chunk_match = re.search(r'_chunk(\d+)', filename, re.IGNORECASE)
        chunk_num = int(chunk_match.group(1)) if chunk_match else 0

        # Look for _part{N} pattern (for sub-chunks)
        part_match = re.search(r'_part(\d+)', filename, re.IGNORECASE)
        part_num = int(part_match.group(1)) if part_match else 0

        return (chunk_num, part_num)

    def _load_contacts(self) -> List[Dict]:
        """Load all contacts from database for fuzzy matching."""
        if self._contacts_cache is not None:
            return self._contacts_cache

        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    contact_id,
                    name,
                    email,
                    role,
                    company
                FROM contacts
                WHERE name IS NOT NULL AND name != ''
            """)
            self._contacts_cache = [dict(row) for row in cursor.fetchall()]

        return self._contacts_cache

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison (lowercase, remove extra spaces)."""
        if not name:
            return ""
        return ' '.join(name.lower().strip().split())

    def _fuzzy_match_name(self, transcript_name: str, contact_name: str) -> float:
        """
        Calculate fuzzy match score between two names.
        Returns 0.0 to 1.0 (1.0 = perfect match).
        """
        t_name = self._normalize_name(transcript_name)
        c_name = self._normalize_name(contact_name)

        if not t_name or not c_name:
            return 0.0

        # Exact match
        if t_name == c_name:
            return 1.0

        # Check if transcript name is part of contact name or vice versa
        t_parts = t_name.split()
        c_parts = c_name.split()

        # First name match (common transcription issue: "Caragh" -> "Kara")
        if len(t_parts) >= 1 and len(c_parts) >= 1:
            # Check first name similarity
            t_first = t_parts[0]
            c_first = c_parts[0]

            # Phonetic similarity check (simplified)
            # Remove common variations and normalize sounds
            def simplify(s):
                s = s.lower()
                # Remove silent letters and normalize sounds
                s = s.replace('gh', '')  # Caragh -> Cara
                s = s.replace('ph', 'f')
                s = s.replace('ck', 'k')
                s = s.replace('ee', 'i')
                s = s.replace('ea', 'i')
                s = s.replace('ou', 'u')
                # Normalize vowel sounds
                s = s.replace('aa', 'a')
                # Normalize hard sounds (K and C often sound same)
                s = s.replace('c', 'k')  # Cara -> Kara
                s = s.replace('qu', 'k')
                return s

            t_simplified = simplify(t_first)
            c_simplified = simplify(c_first)

            if t_simplified == c_simplified:
                return 0.85

            # Check if one contains the other (for phonetic matches like Kara/Cara)
            if t_simplified in c_simplified or c_simplified in t_simplified:
                return 0.8

            # Check if one is a prefix of the other (common for nicknames)
            if c_simplified.startswith(t_simplified) or t_simplified.startswith(c_simplified):
                return 0.75

            # Levenshtein-style: if only 1 char different in short names
            if len(t_simplified) >= 3 and len(c_simplified) >= 3:
                if abs(len(t_simplified) - len(c_simplified)) <= 1:
                    # Count matching chars
                    shorter = min(t_simplified, c_simplified, key=len)
                    longer = max(t_simplified, c_simplified, key=len)
                    matches = sum(1 for i, c in enumerate(shorter) if i < len(longer) and c == longer[i])
                    if matches >= len(shorter) - 1:
                        return 0.75

        # Last name exact match (if both have last names)
        if len(t_parts) >= 2 and len(c_parts) >= 2:
            if t_parts[-1] == c_parts[-1]:
                return 0.9

        # Check if all words in transcript name appear in contact name
        if all(part in c_name for part in t_parts):
            return 0.85

        # Check if contact's first or last name matches transcript name exactly
        if t_name in c_parts:
            return 0.8

        return 0.0

    def _get_proposal_contacts(self, proposal_id: int) -> List[Dict]:
        """Get contacts associated with a proposal via email links."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get contacts from emails linked to this proposal
            cursor.execute("""
                SELECT DISTINCT
                    c.contact_id,
                    c.name,
                    c.email,
                    c.role,
                    c.company
                FROM contacts c
                JOIN emails e ON c.email = e.sender_email
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                WHERE epl.proposal_id = ?
                AND c.name IS NOT NULL
            """, (proposal_id,))

            return [dict(row) for row in cursor.fetchall()]

    def match_participants(self, transcript_id: int) -> Dict:
        """
        Match participant names mentioned in transcript against contacts database.

        Strategy:
        1. Extract names from transcript text using GPT
        2. Fuzzy match against contacts table
        3. Use proposal context to prioritize likely matches
        4. Update participants field with matched contacts

        Returns:
            Result dict with matched participants
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get transcript
            cursor.execute("""
                SELECT
                    id,
                    transcript,
                    summary,
                    participants,
                    proposal_id,
                    meeting_title
                FROM meeting_transcripts
                WHERE id = ?
            """, (transcript_id,))

            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': f'Transcript {transcript_id} not found'}

            transcript = dict(row)
            transcript_text = transcript['transcript'] or ''
            proposal_id = transcript.get('proposal_id')

            # Load all contacts
            all_contacts = self._load_contacts()

            # Get proposal-specific contacts if linked
            proposal_contacts = []
            if proposal_id:
                proposal_contacts = self._get_proposal_contacts(proposal_id)

            # Use GPT to extract names mentioned in the transcript
            excerpt = transcript_text[:4000]  # First 4000 chars
            summary = transcript.get('summary') or ''

            # Build contacts context for GPT
            contacts_for_gpt = all_contacts[:100]  # Limit to 100 contacts
            contacts_list = "\n".join([
                f"- {c['name']} ({c.get('email', 'no email')}) - {c.get('role', 'unknown role')}"
                for c in contacts_for_gpt
            ])

            prompt = f"""Analyze this meeting transcript and identify participants mentioned.

TRANSCRIPT EXCERPT:
{excerpt}

SUMMARY:
{summary}

KNOWN CONTACTS (match names to these when possible):
{contacts_list}

Instructions:
1. Extract all person names mentioned in the transcript
2. For each name, try to match it to one of the KNOWN CONTACTS above
3. Common transcription errors: "Kara" might be "Caragh", phonetic spellings vary
4. Determine if each person is: team (Bensley employee), client, consultant, or unknown

Return a JSON array of participants:
```json
[
  {{"name": "Full Name", "matched_contact_id": 123 or null, "role": "their role", "type": "team|client|consultant|unknown"}}
]
```

Only return the JSON array, nothing else."""

            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You extract participant information from meeting transcripts and match them to known contacts. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.2
                )

                response_text = response.choices[0].message.content.strip()

                # Parse JSON from response
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0]
                else:
                    json_str = response_text

                gpt_participants = json.loads(json_str.strip())

            except Exception as e:
                self.stats['errors'].append(f"GPT participant extraction error: {str(e)}")
                gpt_participants = []

            # Now do our own fuzzy matching to verify/improve GPT matches
            matched_participants = []
            contacts_by_id = {c['contact_id']: c for c in all_contacts}

            for p in gpt_participants:
                name = p.get('name', '')
                gpt_contact_id = p.get('matched_contact_id')
                role = p.get('role', 'Unknown')
                p_type = p.get('type', 'unknown')

                best_match = None
                best_score = 0.0

                # First check GPT's suggested match
                if gpt_contact_id and gpt_contact_id in contacts_by_id:
                    contact = contacts_by_id[gpt_contact_id]
                    score = self._fuzzy_match_name(name, contact['name'])
                    if score >= 0.7:
                        best_match = contact
                        best_score = score

                # Try our own fuzzy matching
                if best_score < 0.9:
                    # Prioritize proposal contacts
                    for contact in proposal_contacts:
                        score = self._fuzzy_match_name(name, contact['name'])
                        if score > best_score:
                            best_score = score
                            best_match = contact

                    # Then try all contacts
                    if best_score < 0.85:
                        for contact in all_contacts:
                            score = self._fuzzy_match_name(name, contact['name'])
                            if score > best_score:
                                best_score = score
                                best_match = contact

                # Build participant entry
                participant = {
                    'name': best_match['name'] if best_match and best_score >= 0.7 else name,
                    'role': best_match.get('role') or role if best_match else role,
                    'type': p_type
                }

                if best_match and best_score >= 0.7:
                    participant['contact_id'] = best_match['contact_id']
                    participant['email'] = best_match.get('email')
                    participant['match_confidence'] = best_score
                    self.stats['participants_matched'] += 1

                matched_participants.append(participant)

            # Update transcript with matched participants
            cursor.execute("""
                UPDATE meeting_transcripts
                SET participants = ?
                WHERE id = ?
            """, (json.dumps(matched_participants), transcript_id))
            conn.commit()

            return {
                'success': True,
                'transcript_id': transcript_id,
                'participants_found': len(matched_participants),
                'participants_matched': sum(1 for p in matched_participants if p.get('contact_id')),
                'participants': matched_participants
            }

    def match_all_participants(self) -> Dict:
        """Match participants for all transcripts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM meeting_transcripts WHERE transcript IS NOT NULL")
            transcript_ids = [row[0] for row in cursor.fetchall()]

        results = []
        for tid in transcript_ids:
            result = self.match_participants(tid)
            results.append(result)

        return {
            'transcripts_processed': len(results),
            'total_participants_matched': self.stats['participants_matched'],
            'results': results
        }

    def analyze_transcripts(self) -> Dict:
        """
        Analyze the meeting_transcripts table to understand chunk patterns.

        Returns detailed analysis of what needs consolidation.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all transcripts
            cursor.execute("""
                SELECT
                    id,
                    audio_filename,
                    length(transcript) as transcript_len,
                    proposal_id,
                    meeting_title,
                    summary
                FROM meeting_transcripts
                WHERE transcript IS NOT NULL
                ORDER BY audio_filename, id
            """)

            rows = cursor.fetchall()

            # Group by base filename
            meetings = defaultdict(list)
            for row in rows:
                base_name = self._extract_base_filename(row['audio_filename'])
                meetings[base_name].append(dict(row))

            analysis = {
                'total_rows': len(rows),
                'unique_meetings': len(meetings),
                'meetings_with_chunks': 0,
                'meetings_with_duplicates': 0,
                'total_duplicates': 0,
                'meetings': []
            }

            for base_name, transcripts in meetings.items():
                # Count unique filenames within this meeting
                unique_files = set(t['audio_filename'] for t in transcripts)
                row_count = len(transcripts)

                meeting_info = {
                    'base_filename': base_name,
                    'total_rows': row_count,
                    'unique_files': len(unique_files),
                    'file_names': list(unique_files),
                    'ids': [t['id'] for t in transcripts],
                    'has_title': any(t['meeting_title'] for t in transcripts),
                    'has_proposal': any(t['proposal_id'] for t in transcripts)
                }

                # Check for chunks
                if any('_chunk' in f for f in unique_files):
                    analysis['meetings_with_chunks'] += 1
                    meeting_info['has_chunks'] = True
                else:
                    meeting_info['has_chunks'] = False

                # Check for duplicates (same filename, multiple rows)
                file_counts = defaultdict(int)
                for t in transcripts:
                    file_counts[t['audio_filename']] += 1

                duplicates = sum(c - 1 for c in file_counts.values() if c > 1)
                if duplicates > 0:
                    analysis['meetings_with_duplicates'] += 1
                    analysis['total_duplicates'] += duplicates
                    meeting_info['duplicates'] = duplicates

                analysis['meetings'].append(meeting_info)

            return analysis

    def consolidate_meeting(self, base_filename: str, dry_run: bool = False) -> Dict:
        """
        Consolidate all chunks and duplicates for a single meeting.

        Args:
            base_filename: The base meeting name (without chunk suffixes)
            dry_run: If True, report what would happen without making changes

        Returns:
            Result dict with consolidation details
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Find all rows for this meeting
            cursor.execute("""
                SELECT
                    id,
                    audio_filename,
                    audio_path,
                    transcript,
                    summary,
                    key_points,
                    action_items,
                    detected_project_id,
                    detected_project_code,
                    match_confidence,
                    meeting_type,
                    participants,
                    sentiment,
                    duration_seconds,
                    recorded_date,
                    processed_date,
                    project_id,
                    proposal_id,
                    meeting_title,
                    meeting_date
                FROM meeting_transcripts
                WHERE transcript IS NOT NULL
            """)

            all_rows = cursor.fetchall()

            # Filter to matching base filename
            matching_rows = []
            for row in all_rows:
                row_base = self._extract_base_filename(row['audio_filename'])
                if row_base == base_filename:
                    matching_rows.append(dict(row))

            if not matching_rows:
                return {'success': False, 'error': f'No transcripts found for {base_filename}'}

            # Group by actual filename to handle duplicates within chunks
            by_filename = defaultdict(list)
            for row in matching_rows:
                by_filename[row['audio_filename']].append(row)

            # For each unique filename, keep the best row (longest transcript)
            best_per_chunk = []
            duplicates_to_remove = []

            for filename, rows in by_filename.items():
                # Sort by transcript length (descending), keep best
                rows.sort(key=lambda x: len(x['transcript'] or ''), reverse=True)
                best_per_chunk.append(rows[0])
                duplicates_to_remove.extend(r['id'] for r in rows[1:])

            # Sort chunks by order for proper concatenation
            best_per_chunk.sort(key=lambda x: self._get_chunk_order(x['audio_filename']))

            # Merge transcripts in order
            merged_transcript = '\n\n'.join(
                row['transcript'] for row in best_per_chunk
                if row['transcript']
            )

            # Merge summaries
            summaries = [row['summary'] for row in best_per_chunk if row['summary']]

            # Get best metadata from chunks
            primary_row = best_per_chunk[0]  # Use first chunk as base
            proposal_id = next((r['proposal_id'] for r in best_per_chunk if r['proposal_id']), None)
            project_id = next((r['project_id'] for r in best_per_chunk if r['project_id']), None)
            meeting_title = next((r['meeting_title'] for r in best_per_chunk if r['meeting_title']), None)
            detected_code = next((r['detected_project_code'] for r in best_per_chunk if r['detected_project_code']), None)

            # Collect all participants
            all_participants = []
            for row in best_per_chunk:
                if row['participants']:
                    try:
                        participants = json.loads(row['participants']) if isinstance(row['participants'], str) else row['participants']
                        all_participants.extend(participants)
                    except (json.JSONDecodeError, TypeError):
                        pass

            # Dedupe participants by name
            seen_names = set()
            unique_participants = []
            for p in all_participants:
                name = p.get('name') if isinstance(p, dict) else str(p)
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_participants.append(p)

            # Sum durations
            total_duration = sum(r['duration_seconds'] or 0 for r in best_per_chunk)

            result = {
                'base_filename': base_filename,
                'chunks_found': len(best_per_chunk),
                'duplicates_found': len(duplicates_to_remove),
                'chunk_files': [r['audio_filename'] for r in best_per_chunk],
                'merged_transcript_length': len(merged_transcript),
                'summaries_merged': len(summaries),
                'proposal_id': proposal_id,
                'project_id': project_id,
                'detected_code': detected_code,
                'existing_title': meeting_title,
                'participants': unique_participants,
                'total_duration_seconds': total_duration,
                'rows_to_keep': [primary_row['id']],
                'rows_to_remove': [r['id'] for r in best_per_chunk[1:]] + duplicates_to_remove
            }

            if dry_run:
                result['dry_run'] = True
                return result

            # Perform consolidation
            # 1. Update primary row with merged content
            cursor.execute("""
                UPDATE meeting_transcripts
                SET
                    audio_filename = ?,
                    transcript = ?,
                    participants = ?,
                    duration_seconds = ?,
                    proposal_id = COALESCE(proposal_id, ?),
                    project_id = COALESCE(project_id, ?),
                    detected_project_code = COALESCE(detected_project_code, ?)
                WHERE id = ?
            """, (
                base_filename + '.m4a',  # Normalize filename
                merged_transcript,
                json.dumps(unique_participants),
                total_duration if total_duration > 0 else None,
                proposal_id,
                project_id,
                detected_code,
                primary_row['id']
            ))

            # 2. Delete all other rows
            if result['rows_to_remove']:
                placeholders = ','.join('?' * len(result['rows_to_remove']))
                cursor.execute(
                    f"DELETE FROM meeting_transcripts WHERE id IN ({placeholders})",
                    result['rows_to_remove']
                )

            conn.commit()

            result['consolidated'] = True
            result['primary_id'] = primary_row['id']
            result['rows_removed'] = len(result['rows_to_remove'])

            self.stats['chunks_processed'] += len(best_per_chunk)
            self.stats['duplicates_removed'] += len(duplicates_to_remove) + len(best_per_chunk) - 1

            return result

    def generate_smart_title(self, transcript_id: int) -> Dict:
        """
        Generate a smart title for a transcript using GPT.

        Format: "{Project Name} - {Meeting Topic}" (max 60 chars)

        Also enriches with proposal context if matched.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get transcript
            cursor.execute("""
                SELECT
                    t.id,
                    t.audio_filename,
                    t.transcript,
                    t.summary,
                    t.proposal_id,
                    t.project_id,
                    t.detected_project_code,
                    t.meeting_title,
                    t.meeting_type,
                    t.participants,
                    p.project_code,
                    p.project_name,
                    p.client_company,
                    p.country,
                    p.status as proposal_status
                FROM meeting_transcripts t
                LEFT JOIN proposals p ON t.proposal_id = p.proposal_id
                WHERE t.id = ?
            """, (transcript_id,))

            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': f'Transcript {transcript_id} not found'}

            transcript = dict(row)

            # Check if already has a good title
            if transcript['meeting_title'] and len(transcript['meeting_title']) > 10:
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'Already has title',
                    'existing_title': transcript['meeting_title']
                }

            # Get project name if linked
            project_name = transcript.get('project_name')
            project_code = transcript.get('project_code') or transcript.get('detected_project_code')

            # If no proposal link, try to find from proposals/projects tables
            if not project_name and project_code:
                cursor.execute("""
                    SELECT project_name, client_company
                    FROM proposals
                    WHERE project_code = ?
                    LIMIT 1
                """, (project_code,))
                prop_row = cursor.fetchone()
                if prop_row:
                    project_name = prop_row[0]

            # Build context for GPT
            transcript_excerpt = (transcript['transcript'] or '')[:3000]
            summary = transcript['summary'] or ''

            # Get recent proposals for context
            cursor.execute("""
                SELECT project_code, project_name, client_company, country
                FROM proposals
                WHERE status IN ('active', 'proposal', 'pending')
                ORDER BY proposal_id DESC
                LIMIT 30
            """)
            proposals_context = "\n".join([
                f"- {r[0]}: {r[1]} ({r[2]}, {r[3]})"
                for r in cursor.fetchall()
            ])

            prompt = f"""Generate a concise meeting title for this transcript.

FORMAT: "[Project Name] - [Meeting Topic]" (max 60 characters)

If the meeting is about a specific project, start with the project name.
If it's a general meeting, describe the main topic.

Examples:
- "Shinta Mani Wild - Pool Design Discussion"
- "Cheval Blanc Bodrum - Road Network Review"
- "Team Meeting - Q4 Project Pipeline"
- "Client Call - Calcutta Residence Interior"

TRANSCRIPT EXCERPT:
{transcript_excerpt}

SUMMARY:
{summary}

{f"DETECTED PROJECT: {project_code} - {project_name}" if project_name else ""}

ACTIVE PROPOSALS (for matching):
{proposals_context}

Return ONLY the title, nothing else. Keep it under 60 characters."""

            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You generate concise, descriptive meeting titles. Return only the title, no explanation."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=50,
                    temperature=0.3
                )

                title = response.choices[0].message.content.strip()

                # Clean up title (remove quotes if present)
                title = title.strip('"\'')

                # Ensure max length
                if len(title) > 60:
                    title = title[:57] + '...'

                # Update transcript
                cursor.execute("""
                    UPDATE meeting_transcripts
                    SET meeting_title = ?
                    WHERE id = ?
                """, (title, transcript_id))
                conn.commit()

                self.stats['titles_generated'] += 1

                return {
                    'success': True,
                    'transcript_id': transcript_id,
                    'title': title,
                    'project_code': project_code,
                    'project_name': project_name
                }

            except Exception as e:
                self.stats['errors'].append(f"Title generation error for {transcript_id}: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'transcript_id': transcript_id
                }

    def consolidate_all(self, dry_run: bool = False) -> Dict:
        """
        Consolidate all chunked and duplicated transcripts.

        Args:
            dry_run: If True, report what would happen without making changes

        Returns:
            Consolidation results including statistics
        """
        # First analyze
        analysis = self.analyze_transcripts()

        results = {
            'analysis': analysis,
            'consolidations': [],
            'titles_generated': [],
            'dry_run': dry_run
        }

        # Process each meeting that needs consolidation
        for meeting in analysis['meetings']:
            if meeting['total_rows'] > 1 or meeting.get('has_chunks'):
                consolidation = self.consolidate_meeting(
                    meeting['base_filename'],
                    dry_run=dry_run
                )
                results['consolidations'].append(consolidation)
                self.stats['meetings_identified'] += 1

        # Generate titles for all transcripts
        if not dry_run:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM meeting_transcripts
                    WHERE (meeting_title IS NULL OR meeting_title = '')
                      AND transcript IS NOT NULL
                      AND length(transcript) > 100
                """)
                ids_needing_titles = [row[0] for row in cursor.fetchall()]

            for transcript_id in ids_needing_titles:
                title_result = self.generate_smart_title(transcript_id)
                results['titles_generated'].append(title_result)

        results['stats'] = self.stats
        results['final_analysis'] = self.analyze_transcripts() if not dry_run else None

        return results


def get_consolidation_service(db_path: str = None) -> TranscriptConsolidationService:
    """Get a configured consolidation service instance."""
    return TranscriptConsolidationService(db_path or DB_PATH)


def main():
    """Command-line interface for transcript consolidation."""
    import argparse
    parser = argparse.ArgumentParser(description='Consolidate chunked meeting transcripts')
    parser.add_argument('--dry-run', action='store_true', help='Report without making changes')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze, no consolidation')
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    parser.add_argument('--meeting', type=str, help='Process single meeting by base filename')
    parser.add_argument('--title', type=int, help='Generate title for single transcript ID')
    args = parser.parse_args()

    service = TranscriptConsolidationService(args.db)

    if args.analyze_only:
        analysis = service.analyze_transcripts()
        print("\n" + "="*60)
        print("TRANSCRIPT ANALYSIS")
        print("="*60)
        print(f"Total rows: {analysis['total_rows']}")
        print(f"Unique meetings: {analysis['unique_meetings']}")
        print(f"Meetings with chunks: {analysis['meetings_with_chunks']}")
        print(f"Meetings with duplicates: {analysis['meetings_with_duplicates']}")
        print(f"Total duplicate rows: {analysis['total_duplicates']}")
        print("\nMeetings breakdown:")
        for m in analysis['meetings']:
            status = []
            if m.get('has_chunks'):
                status.append('has chunks')
            if m.get('duplicates'):
                status.append(f"{m['duplicates']} duplicates")
            if m.get('has_title'):
                status.append('has title')
            if m.get('has_proposal'):
                status.append('has proposal')
            status_str = f" ({', '.join(status)})" if status else ""
            print(f"  - {m['base_filename']}: {m['total_rows']} rows{status_str}")
        return

    if args.title:
        result = service.generate_smart_title(args.title)
        print(json.dumps(result, indent=2))
        return

    if args.meeting:
        result = service.consolidate_meeting(args.meeting, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
        return

    # Full consolidation
    results = service.consolidate_all(dry_run=args.dry_run)

    print("\n" + "="*60)
    print("TRANSCRIPT CONSOLIDATION RESULTS")
    print("="*60)
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Meetings processed: {len(results['consolidations'])}")
    print(f"Titles generated: {len(results['titles_generated'])}")
    print(f"\nStats:")
    for key, value in results['stats'].items():
        if key != 'errors':
            print(f"  {key}: {value}")
    if results['stats']['errors']:
        print(f"\nErrors ({len(results['stats']['errors'])}):")
        for error in results['stats']['errors'][:5]:
            print(f"  - {error}")

    if results.get('final_analysis'):
        print(f"\nAfter consolidation:")
        print(f"  Total rows: {results['final_analysis']['total_rows']}")
        print(f"  Unique meetings: {results['final_analysis']['unique_meetings']}")


if __name__ == '__main__':
    main()
