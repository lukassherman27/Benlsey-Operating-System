"""
Transcript Linker - Creates suggestions to link meeting transcripts to proposals

IMPORTANT: This script creates AI suggestions for human review.
It NEVER auto-links transcripts - all links must be approved.

Strategies:
1. Code Extraction: Extract BK project codes from transcript text
2. Name Matching: Match project/client names mentioned in transcript
3. AI Analysis: Use OpenAI to identify which proposal the transcript relates to

Created: 2025-12-01
"""

import sqlite3
import re
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI

# Default database path
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


class TranscriptLinker:
    """Creates suggestions to link unlinked transcripts to proposals"""

    def __init__(self, db_path: str = DB_PATH, use_ai: bool = True):
        self.db_path = db_path
        self.use_ai = use_ai
        self.client = OpenAI() if use_ai else None
        self.stats = {
            'code_matched': 0,
            'name_matched': 0,
            'ai_matched': 0,
            'already_linked': 0,
            'no_match': 0,
            'suggestions_created': 0,
            'errors': 0
        }

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_unlinked_transcripts(self) -> List[Dict]:
        """Get all transcripts not linked to any proposal"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    audio_filename,
                    transcript,
                    summary,
                    key_points,
                    detected_project_code,
                    match_confidence,
                    meeting_title,
                    meeting_date,
                    recorded_date
                FROM meeting_transcripts
                WHERE proposal_id IS NULL
                  AND project_id IS NULL
                  AND transcript IS NOT NULL
                  AND transcript != ''
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_proposals(self) -> Dict[str, Dict]:
        """Get mapping of project_code -> proposal info"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    proposal_id,
                    project_code,
                    project_name,
                    client_company,
                    country,
                    status
                FROM proposals
                WHERE project_code IS NOT NULL
            """)
            return {
                row['project_code']: dict(row)
                for row in cursor.fetchall()
            }

    def get_proposal_tracker(self) -> Dict[str, Dict]:
        """Get mapping from proposal_tracker table"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    project_code,
                    project_name,
                    country,
                    current_status
                FROM proposal_tracker
                WHERE project_code IS NOT NULL
            """)
            return {
                row['project_code']: dict(row)
                for row in cursor.fetchall()
            }

    # =========================================================================
    # STRATEGY 1: Code Extraction from Transcript
    # =========================================================================

    def extract_project_codes(self, text: str) -> List[str]:
        """Extract BK project codes from text"""
        if not text:
            return []

        codes = []
        patterns = [
            r'(\d{2}\s*BK[-\s]?\d{3})',  # Year prefix: 25 BK-087
            r'BK[-\s]?0?(\d{2,3})',       # BK-070 or BK070
            r'code\s+BK[-\s]?0?(\d{2,3})', # "code BK070"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Normalize code format
                code = match.upper().replace(' ', '').replace('-', '')
                if code.startswith('BK'):
                    # Try to find full format like "25 BK-070"
                    if len(code) >= 5:
                        codes.append(code)
                else:
                    # Just digits - format as BK-XXX
                    codes.append(f"BK-{code.zfill(3)}")

        return list(set(codes))

    def normalize_code(self, code: str) -> str:
        """Normalize project code to match database format"""
        code = code.upper().replace(' ', '').replace('-', '')
        # Try different formats
        if code.startswith('BK'):
            digits = code[2:].zfill(3)
            return f"BK-{digits}"
        return code

    def match_by_code(self, transcript: Dict, proposals: Dict) -> Optional[Dict]:
        """Try to match transcript to proposal by extracted codes"""
        # First check if there's a detected_project_code
        detected = transcript.get('detected_project_code')
        if detected:
            normalized = self.normalize_code(detected)
            # Try to find match with various year prefixes
            for year in ['25', '24', '23', '22', '21']:
                full_code = f"{year} {normalized}"
                if full_code in proposals:
                    return {
                        'proposal': proposals[full_code],
                        'confidence': transcript.get('match_confidence', 0.8),
                        'method': 'detected_code',
                        'match_reason': f"Detected project code: {detected}"
                    }

        # Extract codes from transcript text
        text = transcript.get('transcript', '')
        codes = self.extract_project_codes(text)

        for code in codes:
            normalized = self.normalize_code(code)
            for year in ['25', '24', '23', '22', '21']:
                full_code = f"{year} {normalized}"
                if full_code in proposals:
                    return {
                        'proposal': proposals[full_code],
                        'confidence': 0.85,
                        'method': 'extracted_code',
                        'match_reason': f"Found project code in transcript: {code}"
                    }

        return None

    # =========================================================================
    # STRATEGY 2: Name Matching
    # =========================================================================

    def match_by_name(self, transcript: Dict, proposals: Dict) -> Optional[Dict]:
        """Try to match transcript to proposal by project/client names"""
        text = (transcript.get('transcript', '') + ' ' +
                (transcript.get('summary') or '') + ' ' +
                (transcript.get('meeting_title') or '')).lower()

        best_match = None
        best_score = 0

        for code, proposal in proposals.items():
            score = 0
            reasons = []

            # Check project name
            project_name = (proposal.get('project_name') or '').lower()
            if project_name and len(project_name) > 5:
                # Check for significant words
                words = [w for w in project_name.split() if len(w) > 3]
                matches = sum(1 for w in words if w in text)
                if matches >= 2 or (matches == 1 and len(words) == 1):
                    score += matches * 0.3
                    reasons.append(f"Project name match: {project_name}")

            # Check client name
            client = (proposal.get('client_company') or '').lower()
            if client and len(client) > 3 and client in text:
                score += 0.4
                reasons.append(f"Client match: {client}")

            # Check country
            country = (proposal.get('country') or '').lower()
            if country and len(country) > 3 and country in text:
                score += 0.2
                reasons.append(f"Country match: {country}")

            if score > best_score and score >= 0.5:
                best_score = score
                best_match = {
                    'proposal': proposal,
                    'confidence': min(score, 0.75),  # Cap at 0.75 for name matching
                    'method': 'name_matching',
                    'match_reason': '; '.join(reasons)
                }

        return best_match

    # =========================================================================
    # STRATEGY 3: AI Analysis (OpenAI)
    # =========================================================================

    def match_by_ai(self, transcript: Dict, proposals: Dict) -> Optional[Dict]:
        """Use OpenAI to analyze transcript and find matching proposal"""
        if not self.use_ai or not self.client:
            return None

        # Prepare proposal list for AI
        proposal_list = "\n".join([
            f"- {code}: {p.get('project_name', 'Unknown')} ({p.get('client_company', 'Unknown')} - {p.get('country', 'Unknown')})"
            for code, p in list(proposals.items())[:50]  # Limit to 50 proposals
        ])

        # Get transcript excerpt
        transcript_text = transcript.get('transcript', '')[:2000]
        summary = transcript.get('summary', '')

        prompt = f"""Analyze this meeting transcript and identify which project it relates to.

TRANSCRIPT:
{transcript_text}

{f'SUMMARY: {summary}' if summary else ''}

AVAILABLE PROPOSALS:
{proposal_list}

If you can identify which proposal this transcript relates to, respond with ONLY the project code (e.g., "25 BK-070").
If you're not confident, respond with "UNSURE".
Do not explain - just provide the code or UNSURE."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are analyzing meeting transcripts to identify which project they relate to. Only respond with a project code or UNSURE."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0
            )

            result = response.choices[0].message.content.strip()

            if result and result != "UNSURE" and result in proposals:
                return {
                    'proposal': proposals[result],
                    'confidence': 0.7,  # AI matches need human verification
                    'method': 'ai_analysis',
                    'match_reason': f"AI identified project code: {result}"
                }
        except Exception as e:
            print(f"AI analysis error: {e}")
            self.stats['errors'] += 1

        return None

    # =========================================================================
    # SUGGESTION CREATION
    # =========================================================================

    def suggestion_exists(self, transcript_id: int, proposal_id: int) -> bool:
        """Check if a suggestion already exists for this transcript-proposal pair"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM ai_suggestions
                WHERE suggestion_type = 'transcript_link'
                  AND source_type = 'transcript'
                  AND source_id = ?
                  AND proposal_id = ?
                  AND status IN ('pending', 'approved')
            """, (transcript_id, proposal_id))
            return cursor.fetchone() is not None

    def create_suggestion(self, transcript: Dict, match: Dict) -> bool:
        """Create an AI suggestion for linking transcript to proposal"""
        proposal = match['proposal']
        transcript_id = transcript['id']
        proposal_id = proposal['proposal_id']

        # Check for existing suggestion
        if self.suggestion_exists(transcript_id, proposal_id):
            return False

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Build source reference
                meeting_date = transcript.get('meeting_date') or transcript.get('recorded_date') or 'Unknown date'
                audio_file = transcript.get('audio_filename') or 'Unknown'
                source_ref = f"Transcript: {audio_file} ({meeting_date})"

                # Build suggested data
                suggested_data = json.dumps({
                    'transcript_id': transcript_id,
                    'proposal_id': proposal_id,
                    'project_code': proposal['project_code'],
                    'match_method': match['method'],
                    'match_confidence': match['confidence']
                })

                # Determine priority based on confidence
                confidence = match['confidence']
                if confidence >= 0.9:
                    priority = 'high'
                elif confidence >= 0.7:
                    priority = 'medium'
                else:
                    priority = 'low'

                cursor.execute("""
                    INSERT INTO ai_suggestions (
                        suggestion_type,
                        priority,
                        confidence_score,
                        source_type,
                        source_id,
                        source_reference,
                        title,
                        description,
                        suggested_action,
                        suggested_data,
                        target_table,
                        target_id,
                        project_code,
                        proposal_id,
                        status,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
                """, (
                    'transcript_link',
                    priority,
                    confidence,
                    'transcript',
                    transcript_id,
                    source_ref,
                    f"Link transcript to {proposal['project_code']}",
                    f"Transcript appears to be about {proposal.get('project_name', proposal['project_code'])}. {match['match_reason']}",
                    f"Set meeting_transcripts.proposal_id = {proposal_id}",
                    suggested_data,
                    'meeting_transcripts',
                    transcript_id,
                    proposal['project_code'],
                    proposal_id
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating suggestion: {e}")
            self.stats['errors'] += 1
            return False

    # =========================================================================
    # MAIN LOGIC
    # =========================================================================

    def run(self, dry_run: bool = False, limit: int = None) -> Dict:
        """
        Run all matching strategies on unlinked transcripts

        Args:
            dry_run: If True, don't create suggestions, just report matches
            limit: Max transcripts to process

        Returns:
            Statistics dict
        """
        print(f"{'[DRY RUN] ' if dry_run else ''}Starting transcript linking...")

        # Load proposals from both tables
        print("Loading proposals...")
        proposals = self.get_proposals()
        print(f"  Found {len(proposals)} proposals")

        # Also get proposal_tracker entries
        tracker = self.get_proposal_tracker()
        print(f"  Found {len(tracker)} proposal tracker entries")

        # Merge (proposals table takes priority)
        for code, entry in tracker.items():
            if code not in proposals:
                # Convert tracker format to match proposals
                proposals[code] = {
                    'proposal_id': entry['id'],
                    'project_code': code,
                    'project_name': entry.get('project_name'),
                    'client_company': None,
                    'country': entry.get('country'),
                    'status': entry.get('current_status')
                }

        print(f"  Total unique proposals: {len(proposals)}")

        # Get unlinked transcripts
        print("Loading unlinked transcripts...")
        transcripts = self.get_unlinked_transcripts()
        print(f"  Found {len(transcripts)} unlinked transcripts")

        if limit:
            transcripts = transcripts[:limit]
            print(f"  Processing first {limit} transcripts")

        # Process each transcript
        for i, transcript in enumerate(transcripts):
            if (i + 1) % 10 == 0:
                print(f"  Processed {i+1}/{len(transcripts)}...")

            match = None

            # Strategy 1: Code matching (highest confidence)
            match = self.match_by_code(transcript, proposals)
            if match:
                self.stats['code_matched'] += 1

            # Strategy 2: Name matching
            if not match:
                match = self.match_by_name(transcript, proposals)
                if match:
                    self.stats['name_matched'] += 1

            # Strategy 3: AI analysis (lowest confidence, only if enabled)
            if not match and self.use_ai:
                match = self.match_by_ai(transcript, proposals)
                if match:
                    self.stats['ai_matched'] += 1

            # Create suggestion if match found
            if match:
                if dry_run:
                    print(f"  Would suggest: Transcript {transcript['id']} -> {match['proposal']['project_code']} "
                          f"(confidence: {match['confidence']:.2f}, method: {match['method']})")
                else:
                    if self.create_suggestion(transcript, match):
                        self.stats['suggestions_created'] += 1
                    else:
                        self.stats['already_linked'] += 1
            else:
                self.stats['no_match'] += 1

        # Print summary
        print("\n" + "="*50)
        print("TRANSCRIPT LINKING SUMMARY")
        print("="*50)
        print(f"Code matched:         {self.stats['code_matched']}")
        print(f"Name matched:         {self.stats['name_matched']}")
        print(f"AI matched:           {self.stats['ai_matched']}")
        print(f"Already has suggestion: {self.stats['already_linked']}")
        print(f"No match found:       {self.stats['no_match']}")
        print(f"Errors:               {self.stats['errors']}")
        print(f"\nSuggestions created:  {self.stats['suggestions_created']}")

        return self.stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create suggestions to link transcripts to proposals')
    parser.add_argument('--dry-run', action='store_true', help='Show matches without creating suggestions')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI analysis (faster, less accurate)')
    parser.add_argument('--limit', type=int, help='Max transcripts to process')
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    args = parser.parse_args()

    linker = TranscriptLinker(args.db, use_ai=not args.no_ai)
    stats = linker.run(dry_run=args.dry_run, limit=args.limit)

    return stats


if __name__ == '__main__':
    main()
