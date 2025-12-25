"""
Activity Extractor Service - AI Story Builder (#141)

Extracts intelligence from emails and transcripts:
- Action items with dates and owners
- Key decisions
- Sentiment analysis
- Important dates mentioned

Stores extracted data in proposal_activities and proposal_action_items tables.
"""

import re
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from .base_service import BaseService

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActivityExtractor(BaseService):
    """Extract activities, action items, and intelligence from content."""

    # Action item patterns
    ACTION_PATTERNS = [
        # Direct requests: "Please send...", "Can you..."
        r'(?:please|kindly|can you|could you|would you)\s+(.+?)(?:\.|$)',
        # Need to: "We need to...", "I need to..."
        r'(?:we|i)\s+need\s+to\s+(.+?)(?:\.|$)',
        # Will do: "I will...", "We will..."
        r'(?:i|we)\s+will\s+(.+?)(?:\.|$)',
        # Action required: "Action required:..."
        r'action\s+required[:\s]+(.+?)(?:\.|$)',
        # Follow up: "Please follow up on..."
        r'follow\s+up\s+(?:on|with|regarding)\s+(.+?)(?:\.|$)',
        # Deadline mentions: "by Friday", "before the meeting"
        r'(?:by|before|deadline[:\s])\s+(.+?)(?:\.|$)',
    ]

    # Date patterns
    DATE_PATTERNS = [
        # Explicit dates: "January 5", "Jan 5th", "12/25"
        (r'\b(\d{1,2})[/-](\d{1,2})[/-]?(\d{2,4})?\b', 'mdy'),
        (r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})?\b', 'month'),
        # Relative dates: "tomorrow", "next week"
        (r'\b(today|tomorrow|next\s+week|this\s+week|end\s+of\s+week|eow|eod)\b', 'relative'),
        # Day names: "Monday", "on Friday"
        (r'\b(?:on\s+)?(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b', 'day'),
    ]

    # Sentiment indicators
    POSITIVE_INDICATORS = [
        'excited', 'pleased', 'happy', 'great', 'wonderful', 'excellent',
        'thank you', 'thanks', 'appreciate', 'looking forward', 'delighted',
        'approved', 'agree', 'confirmed', 'proceeding', 'good news'
    ]

    NEGATIVE_INDICATORS = [
        'concerned', 'worried', 'issue', 'problem', 'unfortunately',
        'delay', 'delayed', 'disappointing', 'frustrated', 'urgent',
        'immediately', 'asap', 'critical', 'declined', 'rejected',
        'cannot proceed', 'on hold', 'stopped'
    ]

    # Decision indicators
    DECISION_PATTERNS = [
        r'(?:we|they|client)\s+(?:have\s+)?decided\s+(?:to\s+)?(.+?)(?:\.|$)',
        r'(?:it\s+was|we)\s+agreed\s+(?:that\s+)?(.+?)(?:\.|$)',
        r'decision[:\s]+(.+?)(?:\.|$)',
        r'(?:will|going\s+to)\s+proceed\s+with\s+(.+?)(?:\.|$)',
        r'approved[:\s]+(.+?)(?:\.|$)',
        r'confirmed[:\s]+(.+?)(?:\.|$)',
    ]

    def extract_from_email(self, email_id: int) -> Dict[str, Any]:
        """
        Extract activities and action items from a linked email.

        Returns dict with extracted data and counts.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get email with link info
            cursor.execute("""
                SELECT
                    e.email_id,
                    e.subject,
                    e.sender_email,
                    e.sender_name,
                    e.sender_category,
                    COALESCE(e.date_normalized, e.date) as email_date,
                    e.body_full,
                    e.snippet,
                    ec.ai_summary,
                    ec.key_points,
                    ec.sentiment as existing_sentiment,
                    epl.proposal_id,
                    p.project_code,
                    p.project_name
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
                LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
                WHERE e.email_id = ?
            """, (email_id,))

            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': 'Email not found'}

            email = dict(row)
            proposal_id = email.get('proposal_id')

            if not proposal_id:
                return {
                    'success': False,
                    'error': 'Email not linked to a proposal',
                    'email_id': email_id
                }

            # Get text to analyze
            text = email.get('body_full') or email.get('snippet') or ''

            # Extract intelligence
            action_items = self._extract_action_items(text)
            dates = self._extract_dates(text)
            decisions = self._extract_decisions(text)
            sentiment = self._analyze_sentiment(text, email.get('existing_sentiment'))

            # Determine actor
            actor = self._determine_actor(
                email.get('sender_email'),
                email.get('sender_category')
            )

            # Determine activity type
            is_sent = actor in ('bill', 'brian', 'lukas', 'mink', 'bensley')
            activity_type = 'email_sent' if is_sent else 'email_received'

            # Check if activity already exists
            cursor.execute("""
                SELECT activity_id FROM proposal_activities
                WHERE source_type = 'email' AND source_id = ?
            """, (str(email_id),))

            existing = cursor.fetchone()

            if existing:
                # Update existing activity
                activity_id = existing[0]
                cursor.execute("""
                    UPDATE proposal_activities SET
                        extracted_dates = ?,
                        extracted_actions = ?,
                        extracted_decisions = ?,
                        sentiment = ?,
                        updated_at = datetime('now')
                    WHERE activity_id = ?
                """, (
                    json.dumps(dates),
                    json.dumps([a['text'] for a in action_items]),
                    json.dumps(decisions),
                    sentiment,
                    activity_id
                ))
            else:
                # Create new activity
                cursor.execute("""
                    INSERT INTO proposal_activities (
                        proposal_id, activity_type, activity_date,
                        source_type, source_id,
                        actor, actor_email,
                        title, summary,
                        extracted_dates, extracted_actions, extracted_decisions,
                        sentiment, is_significant
                    ) VALUES (?, ?, ?, 'email', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal_id,
                    activity_type,
                    email.get('email_date'),
                    str(email_id),
                    actor,
                    email.get('sender_email'),
                    email.get('subject'),
                    email.get('ai_summary') or email.get('snippet'),
                    json.dumps(dates),
                    json.dumps([a['text'] for a in action_items]),
                    json.dumps(decisions),
                    sentiment,
                    1 if len(decisions) > 0 or sentiment == 'concerned' else 0
                ))
                activity_id = cursor.lastrowid

            # Create action items
            action_items_created = 0
            for item in action_items:
                # Check for duplicate
                cursor.execute("""
                    SELECT action_id FROM proposal_action_items
                    WHERE proposal_id = ? AND action_text = ?
                """, (proposal_id, item['text']))

                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO proposal_action_items (
                            proposal_id, source_activity_id,
                            action_text, action_category,
                            due_date, due_date_source,
                            assigned_to, status, priority,
                            extraction_confidence
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    """, (
                        proposal_id,
                        activity_id,
                        item['text'],
                        item.get('category', 'general'),
                        item.get('due_date'),
                        'extracted' if item.get('due_date') else None,
                        item.get('assigned_to'),
                        item.get('priority', 'normal'),
                        item.get('confidence', 0.7)
                    ))
                    action_items_created += 1

            conn.commit()

            return {
                'success': True,
                'email_id': email_id,
                'proposal_id': proposal_id,
                'activity_id': activity_id,
                'extracted': {
                    'action_items': len(action_items),
                    'action_items_created': action_items_created,
                    'dates': dates,
                    'decisions': decisions,
                    'sentiment': sentiment
                }
            }

    def extract_from_transcript(self, transcript_id: int) -> Dict[str, Any]:
        """
        Extract activities and action items from a meeting transcript.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get transcript with link info
            cursor.execute("""
                SELECT
                    t.id as transcript_id,
                    t.meeting_title,
                    COALESCE(t.meeting_date, t.recorded_date) as meeting_date,
                    t.raw_text,
                    t.summary,
                    t.action_items as existing_actions,
                    t.key_decisions as existing_decisions,
                    t.proposal_id,
                    t.detected_project_code,
                    p.proposal_id as derived_proposal_id,
                    p.project_code,
                    p.project_name
                FROM meeting_transcripts t
                LEFT JOIN proposals p ON t.detected_project_code = p.project_code
                WHERE t.id = ?
            """, (transcript_id,))

            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': 'Transcript not found'}

            transcript = dict(row)
            proposal_id = transcript.get('proposal_id') or transcript.get('derived_proposal_id')

            if not proposal_id:
                return {
                    'success': False,
                    'error': 'Transcript not linked to a proposal',
                    'transcript_id': transcript_id
                }

            # Get text to analyze
            text = transcript.get('raw_text') or transcript.get('summary') or ''

            # Use existing extracted data if available
            existing_actions = transcript.get('existing_actions')
            existing_decisions = transcript.get('existing_decisions')

            if existing_actions:
                try:
                    action_items = json.loads(existing_actions) if isinstance(existing_actions, str) else existing_actions
                    action_items = [{'text': a, 'category': 'meeting'} for a in action_items]
                except:
                    action_items = self._extract_action_items(text)
            else:
                action_items = self._extract_action_items(text)

            if existing_decisions:
                try:
                    decisions = json.loads(existing_decisions) if isinstance(existing_decisions, str) else existing_decisions
                except:
                    decisions = self._extract_decisions(text)
            else:
                decisions = self._extract_decisions(text)

            dates = self._extract_dates(text)
            sentiment = self._analyze_sentiment(text)

            # Check if activity already exists
            cursor.execute("""
                SELECT activity_id FROM proposal_activities
                WHERE source_type = 'transcript' AND source_id = ?
            """, (str(transcript_id),))

            existing = cursor.fetchone()

            if existing:
                activity_id = existing[0]
                cursor.execute("""
                    UPDATE proposal_activities SET
                        extracted_dates = ?,
                        extracted_actions = ?,
                        extracted_decisions = ?,
                        sentiment = ?,
                        updated_at = datetime('now')
                    WHERE activity_id = ?
                """, (
                    json.dumps(dates),
                    json.dumps([a['text'] if isinstance(a, dict) else a for a in action_items]),
                    json.dumps(decisions),
                    sentiment,
                    activity_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO proposal_activities (
                        proposal_id, activity_type, activity_date,
                        source_type, source_id,
                        actor,
                        title, summary,
                        extracted_dates, extracted_actions, extracted_decisions,
                        sentiment, is_significant
                    ) VALUES (?, 'meeting', ?, 'transcript', ?, 'team', ?, ?, ?, ?, ?, ?, 1)
                """, (
                    proposal_id,
                    transcript.get('meeting_date'),
                    str(transcript_id),
                    transcript.get('meeting_title'),
                    transcript.get('summary'),
                    json.dumps(dates),
                    json.dumps([a['text'] if isinstance(a, dict) else a for a in action_items]),
                    json.dumps(decisions),
                    sentiment
                ))
                activity_id = cursor.lastrowid

            # Create action items
            action_items_created = 0
            for item in action_items:
                item_text = item['text'] if isinstance(item, dict) else item
                cursor.execute("""
                    SELECT action_id FROM proposal_action_items
                    WHERE proposal_id = ? AND action_text = ?
                """, (proposal_id, item_text))

                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO proposal_action_items (
                            proposal_id, source_activity_id,
                            action_text, action_category,
                            status, priority,
                            extraction_confidence
                        ) VALUES (?, ?, ?, 'meeting', 'pending', 'normal', 0.8)
                    """, (
                        proposal_id,
                        activity_id,
                        item_text
                    ))
                    action_items_created += 1

            conn.commit()

            return {
                'success': True,
                'transcript_id': transcript_id,
                'proposal_id': proposal_id,
                'activity_id': activity_id,
                'extracted': {
                    'action_items': len(action_items),
                    'action_items_created': action_items_created,
                    'dates': dates,
                    'decisions': decisions,
                    'sentiment': sentiment
                }
            }

    def _extract_action_items(self, text: str) -> List[Dict]:
        """Extract action items from text."""
        if not text:
            return []

        action_items = []
        text_lower = text.lower()

        for pattern in self.ACTION_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match) > 10:  # Skip very short matches
                    # Clean up the action text
                    action_text = match.strip()
                    if action_text and action_text not in [a['text'] for a in action_items]:
                        action_items.append({
                            'text': action_text[:200],  # Limit length
                            'category': 'general',
                            'confidence': 0.7
                        })

        return action_items[:10]  # Limit to 10 action items per email

    def _extract_dates(self, text: str) -> List[Dict]:
        """Extract dates mentioned in text."""
        if not text:
            return []

        dates = []
        today = datetime.now()

        for pattern, date_type in self.DATE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    date_str = None
                    context = text[max(0, match.start()-30):match.end()+30]

                    if date_type == 'relative':
                        word = match.group(1).lower()
                        if word == 'today':
                            date_str = today.strftime('%Y-%m-%d')
                        elif word == 'tomorrow':
                            date_str = (today + timedelta(days=1)).strftime('%Y-%m-%d')
                        elif 'next week' in word:
                            date_str = (today + timedelta(days=7)).strftime('%Y-%m-%d')
                        elif word in ('eow', 'end of week', 'this week'):
                            days_until_friday = (4 - today.weekday()) % 7
                            date_str = (today + timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
                        elif word == 'eod':
                            date_str = today.strftime('%Y-%m-%d')

                    elif date_type == 'day':
                        day_name = match.group(1)
                        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                        day_idx = days.index(day_name.lower())
                        days_ahead = day_idx - today.weekday()
                        if days_ahead <= 0:
                            days_ahead += 7
                        date_str = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

                    elif date_type == 'month':
                        month_name = match.group(1)
                        day = int(match.group(2))
                        year = int(match.group(3)) if match.group(3) else today.year
                        months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                  'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
                        month = months.get(month_name[:3].lower(), 1)
                        date_str = f"{year}-{month:02d}-{day:02d}"

                    if date_str and date_str not in [d.get('date') for d in dates]:
                        dates.append({
                            'date': date_str,
                            'context': context.strip(),
                            'type': date_type
                        })
                except:
                    continue

        return dates[:5]  # Limit to 5 dates

    def _extract_decisions(self, text: str) -> List[str]:
        """Extract key decisions from text."""
        if not text:
            return []

        decisions = []
        text_lower = text.lower()

        for pattern in self.DECISION_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match) > 10:
                    decision = match.strip()
                    if decision and decision not in decisions:
                        decisions.append(decision[:200])

        return decisions[:5]

    def _analyze_sentiment(self, text: str, existing_sentiment: str = None) -> str:
        """Analyze sentiment of text."""
        if existing_sentiment:
            return existing_sentiment

        if not text:
            return 'neutral'

        text_lower = text.lower()
        positive_count = sum(1 for ind in self.POSITIVE_INDICATORS if ind in text_lower)
        negative_count = sum(1 for ind in self.NEGATIVE_INDICATORS if ind in text_lower)

        if negative_count > positive_count and negative_count >= 2:
            return 'concerned'
        elif positive_count > negative_count and positive_count >= 2:
            return 'positive'
        return 'neutral'

    def _determine_actor(self, sender_email: str, sender_category: str) -> str:
        """Determine actor from email sender."""
        if sender_category:
            if sender_category in ('bill', 'brian', 'lukas', 'mink'):
                return sender_category
            if sender_category == 'bensley_other':
                return 'bensley'
        return 'client'

    def process_unprocessed_emails(self, limit: int = 100) -> Dict[str, Any]:
        """
        Process linked emails that haven't had activities extracted.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Find linked emails without activities
            cursor.execute("""
                SELECT epl.email_id
                FROM email_proposal_links epl
                LEFT JOIN proposal_activities pa
                    ON pa.source_type = 'email' AND pa.source_id = CAST(epl.email_id AS TEXT)
                WHERE pa.activity_id IS NULL
                ORDER BY epl.created_at DESC
                LIMIT ?
            """, (limit,))

            email_ids = [row[0] for row in cursor.fetchall()]

        results = {
            'processed': 0,
            'action_items_created': 0,
            'errors': []
        }

        for email_id in email_ids:
            try:
                result = self.extract_from_email(email_id)
                if result.get('success'):
                    results['processed'] += 1
                    results['action_items_created'] += result.get('extracted', {}).get('action_items_created', 0)
                else:
                    results['errors'].append({
                        'email_id': email_id,
                        'error': result.get('error')
                    })
            except Exception as e:
                results['errors'].append({
                    'email_id': email_id,
                    'error': str(e)
                })

        return results

    def process_unprocessed_transcripts(self, limit: int = 50) -> Dict[str, Any]:
        """
        Process transcripts that haven't had activities extracted.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Find transcripts linked to proposals without activities
            cursor.execute("""
                SELECT t.id
                FROM meeting_transcripts t
                LEFT JOIN proposals p ON t.detected_project_code = p.project_code
                LEFT JOIN proposal_activities pa
                    ON pa.source_type = 'transcript' AND pa.source_id = CAST(t.id AS TEXT)
                WHERE (t.proposal_id IS NOT NULL OR p.proposal_id IS NOT NULL)
                AND pa.activity_id IS NULL
                ORDER BY t.recorded_date DESC
                LIMIT ?
            """, (limit,))

            transcript_ids = [row[0] for row in cursor.fetchall()]

        results = {
            'processed': 0,
            'action_items_created': 0,
            'errors': []
        }

        for transcript_id in transcript_ids:
            try:
                result = self.extract_from_transcript(transcript_id)
                if result.get('success'):
                    results['processed'] += 1
                    results['action_items_created'] += result.get('extracted', {}).get('action_items_created', 0)
                else:
                    results['errors'].append({
                        'transcript_id': transcript_id,
                        'error': result.get('error')
                    })
            except Exception as e:
                results['errors'].append({
                    'transcript_id': transcript_id,
                    'error': str(e)
                })

        return results


def main():
    """CLI entry point for testing."""
    import sys

    extractor = ActivityExtractor()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--emails':
            result = extractor.process_unprocessed_emails(limit=50)
        elif sys.argv[1] == '--transcripts':
            result = extractor.process_unprocessed_transcripts(limit=20)
        elif sys.argv[1] == '--email' and len(sys.argv) > 2:
            result = extractor.extract_from_email(int(sys.argv[2]))
        elif sys.argv[1] == '--transcript' and len(sys.argv) > 2:
            result = extractor.extract_from_transcript(int(sys.argv[2]))
        else:
            print("Usage:")
            print("  python activity_extractor.py --emails       # Process unprocessed emails")
            print("  python activity_extractor.py --transcripts  # Process unprocessed transcripts")
            print("  python activity_extractor.py --email <id>   # Process specific email")
            print("  python activity_extractor.py --transcript <id>  # Process specific transcript")
            return

        print(json.dumps(result, indent=2, default=str))
    else:
        # Process both
        print("Processing emails...")
        email_result = extractor.process_unprocessed_emails(limit=50)
        print(json.dumps(email_result, indent=2))

        print("\nProcessing transcripts...")
        transcript_result = extractor.process_unprocessed_transcripts(limit=20)
        print(json.dumps(transcript_result, indent=2))


if __name__ == "__main__":
    main()
