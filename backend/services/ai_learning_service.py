"""
AI Learning Service - Human Feedback Loop for Continuous Learning

This service:
1. Generates suggestions from processed emails
2. Allows human review (approve/reject/modify)
3. Stores feedback for training
4. Applies learned patterns to future processing
"""

import os
import json
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .base_service import BaseService
from .suggestion_handlers import HandlerRegistry
from .learning_service import LearningService

logger = logging.getLogger(__name__)


class AILearningService(BaseService):
    """Service for AI learning with human feedback loop"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)
        # Initialize learning service for email pattern learning
        self.pattern_learner = LearningService(str(self.db_path))

    # =========================================================================
    # SUGGESTION GENERATION
    # =========================================================================

    def generate_suggestions_from_email(self, email_id: int) -> List[Dict]:
        """
        Analyze a processed email and generate suggestions.
        Called after email is processed by smart_email_brain.
        """
        suggestions = []

        # Get email and its content
        email_data = self.execute_query("""
            SELECT
                e.email_id, e.subject, e.sender_email, e.recipient_emails,
                e.body_full, e.date, e.folder,
                ec.category, ec.ai_summary, ec.entities, ec.linked_project_code,
                ec.urgency_level, ec.action_required
            FROM emails e
            JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.email_id = ?
        """, [email_id])

        if not email_data:
            return []

        email = dict(email_data[0])
        entities = json.loads(email.get('entities') or '{}')

        # 1. Check for new contacts
        contact_suggestions = self._detect_new_contacts(email, entities)
        suggestions.extend(contact_suggestions)

        # 2. Check for fee/payment mentions
        if email.get('category') in ['invoice', 'contract', 'financial']:
            fee_suggestions = self._detect_fee_changes(email, entities)
            suggestions.extend(fee_suggestions)

        # 3. Check for follow-up needs
        if email.get('action_required') or email.get('urgency_level') in ['high', 'critical']:
            followup_suggestions = self._detect_followup_needed(email)
            suggestions.extend(followup_suggestions)

        # 4. Check for deadlines
        deadline_suggestions = self._detect_deadlines(email, entities)
        suggestions.extend(deadline_suggestions)

        # 5. Check for email links (project/proposal associations)
        email_link_suggestions = self._detect_email_links(email, entities)
        suggestions.extend(email_link_suggestions)

        # Save suggestions to database
        for suggestion in suggestions:
            self._save_suggestion(suggestion)

        return suggestions

    def _detect_new_contacts(self, email: Dict, entities: Dict) -> List[Dict]:
        """Detect new contacts mentioned in email"""
        suggestions = []

        # Extract email addresses
        sender = email.get('sender_email', '')
        if not sender:
            return []

        # Check if sender exists in contacts
        existing = self.execute_query("""
            SELECT contact_id, email FROM contacts WHERE email = ?
        """, [sender])

        if not existing:
            # Extract name from email format "Name <email@domain.com>"
            name_match = re.match(r'^([^<]+)<', sender)
            name = name_match.group(1).strip() if name_match else sender.split('@')[0]

            # Clean email
            email_match = re.search(r'<([^>]+)>', sender)
            clean_email = email_match.group(1) if email_match else sender

            suggestions.append({
                'suggestion_type': 'new_contact',
                'priority': 'medium',
                'confidence_score': 0.8,
                'source_type': 'email',
                'source_id': email['email_id'],
                'source_reference': f"Email: {email['subject'][:50]}",
                'title': f"New contact: {name}",
                'description': f"Found new contact in email from {email['date'][:10]}",
                'suggested_action': 'Add to contacts table',
                'suggested_data': json.dumps({
                    'name': name,
                    'email': clean_email,
                    'first_seen': email['date'],
                    'source': 'email_import'
                }),
                'target_table': 'contacts',
                'project_code': email.get('linked_project_code')
            })

        return suggestions

    def _detect_fee_changes(self, email: Dict, entities: Dict) -> List[Dict]:
        """Detect fee or payment amounts mentioned"""
        suggestions = []

        amounts = entities.get('amounts', [])
        if not amounts:
            return []

        project_code = email.get('linked_project_code')
        if not project_code:
            return []

        # Get current project value
        current = self.execute_query("""
            SELECT project_value FROM proposals WHERE project_code = ?
        """, [project_code])

        if current and amounts:
            current_value = current[0]['project_value']

            for amount in amounts:
                # Parse amount (handle "$50,000" format)
                try:
                    clean_amount = float(re.sub(r'[,$]', '', str(amount)))
                    if clean_amount > 10000 and clean_amount != current_value:
                        suggestions.append({
                            'suggestion_type': 'fee_change',
                            'priority': 'high',
                            'confidence_score': 0.6,
                            'source_type': 'email',
                            'source_id': email['email_id'],
                            'source_reference': f"Email: {email['subject'][:50]}",
                            'title': f"Fee change detected: ${clean_amount:,.0f}",
                            'description': f"Current: ${current_value:,.0f}, Found: ${clean_amount:,.0f} in email",
                            'suggested_action': 'Update project_value in proposals',
                            'suggested_data': json.dumps({
                                'old_value': current_value,
                                'new_value': clean_amount,
                                'source_email': email['email_id']
                            }),
                            'target_table': 'proposals',
                            'project_code': project_code
                        })
                except (ValueError, TypeError):
                    pass

        return suggestions

    def _detect_followup_needed(self, email: Dict) -> List[Dict]:
        """Detect if follow-up is needed"""
        suggestions = []

        project_code = email.get('linked_project_code')
        if not project_code:
            return []

        # Check days since last outbound email
        last_sent = self.execute_query("""
            SELECT MAX(e.date) as last_sent
            FROM emails e
            WHERE e.folder IN ('Sent', 'SENT')
            AND EXISTS (
                SELECT 1 FROM email_content ec
                WHERE ec.email_id = e.email_id
                AND ec.linked_project_code = ?
            )
        """, [project_code])

        if last_sent and last_sent[0]['last_sent']:
            # Parse various date formats
            from email.utils import parsedate_to_datetime
            try:
                last_date = parsedate_to_datetime(last_sent[0]['last_sent'])
            except:
                try:
                    last_date = datetime.fromisoformat(last_sent[0]['last_sent'].replace('Z', '+00:00'))
                except:
                    return []  # Can't parse date
            days_since = (datetime.now(last_date.tzinfo) - last_date).days

            if days_since > 7:
                suggestions.append({
                    'suggestion_type': 'follow_up_needed',
                    'priority': 'high' if days_since > 14 else 'medium',
                    'confidence_score': 0.9,
                    'source_type': 'pattern',
                    'source_id': email['email_id'],
                    'source_reference': f"No response for {days_since} days",
                    'title': f"Follow up on {project_code}",
                    'description': f"Client email received but no response sent in {days_since} days",
                    'suggested_action': 'Draft follow-up email',
                    'suggested_data': json.dumps({
                        'days_since_response': days_since,
                        'last_email_id': email['email_id']
                    }),
                    'target_table': None,
                    'project_code': project_code
                })

        return suggestions

    def _detect_deadlines(self, email: Dict, entities: Dict) -> List[Dict]:
        """Detect deadlines mentioned in email"""
        suggestions = []

        dates = entities.get('dates', [])
        project_code = email.get('linked_project_code')

        for date_str in dates:
            try:
                # Try to parse date
                deadline = datetime.strptime(date_str, '%Y-%m-%d')
                if deadline > datetime.now():
                    suggestions.append({
                        'suggestion_type': 'deadline_detected',
                        'priority': 'medium',
                        'confidence_score': 0.7,
                        'source_type': 'email',
                        'source_id': email['email_id'],
                        'source_reference': f"Email: {email['subject'][:50]}",
                        'title': f"Deadline: {date_str}",
                        'description': f"Deadline mentioned in email about {project_code or 'unknown project'}",
                        'suggested_action': 'Add to project milestones',
                        'suggested_data': json.dumps({
                            'deadline_date': date_str,
                            'context': email.get('ai_summary', '')[:200]
                        }),
                        'target_table': 'milestones',
                        'project_code': project_code
                    })
            except ValueError:
                pass

        return suggestions

    def _detect_email_links(self, email: Dict, entities: Dict) -> List[Dict]:
        """Detect potential project/proposal links for email"""
        suggestions = []

        # Skip if already linked
        if email.get('linked_project_code'):
            return []

        # NEW: Check learned patterns first (highest confidence)
        try:
            pattern_suggestion = self.pattern_learner.suggest_link_from_patterns(email)
            if pattern_suggestion:
                logger.info(
                    f"Pattern match found for email {email['email_id']}: "
                    f"{pattern_suggestion.get('project_code')}"
                )
                suggestions.append(pattern_suggestion)
                # If we have a high-confidence pattern match, we can return early
                if pattern_suggestion.get('confidence_score', 0) >= 0.8:
                    return suggestions
        except Exception as e:
            logger.warning(f"Pattern matching failed for email {email['email_id']}: {e}")

        subject = email.get('subject', '') or ''
        body = email.get('body_full', '') or ''
        text = f"{subject} {body}".lower()

        # Pattern 1: Look for project codes (BK-XXX pattern)
        project_code_pattern = r'\b(\d{2}\s*BK[-\s]?\d{3})\b'
        matches = re.findall(project_code_pattern, text, re.IGNORECASE)

        for match in matches:
            # Normalize the project code
            normalized = re.sub(r'[\s-]+', ' ', match.upper()).strip()
            normalized = re.sub(r'(\d{2})\s*BK\s*(\d{3})', r'\1 BK-\2', normalized)

            # Check if project exists
            existing = self.execute_query("""
                SELECT proposal_id, project_code, project_name
                FROM proposals WHERE project_code = ?
            """, [normalized])

            if existing:
                proposal = dict(existing[0])
                suggestions.append({
                    'suggestion_type': 'email_link',
                    'priority': 'medium',
                    'confidence_score': 0.85,
                    'source_type': 'email',
                    'source_id': email['email_id'],
                    'source_reference': f"Email: {subject[:50]}",
                    'title': f"Link email to {normalized}",
                    'description': f"Project code {normalized} found in email",
                    'suggested_action': 'Create email_proposal_link',
                    'suggested_data': json.dumps({
                        'email_id': email['email_id'],
                        'proposal_id': proposal['proposal_id'],
                        'project_code': normalized,
                        'project_name': proposal['project_name'],
                        'match_type': 'project_code'
                    }),
                    'target_table': 'email_proposal_links',
                    'project_code': normalized
                })

        # Pattern 2: Look for client/project name mentions if no code found
        if not suggestions:
            # Get active proposals to match against
            proposals = self.execute_query("""
                SELECT proposal_id, project_code, project_name, client_company
                FROM proposals
                WHERE status NOT IN ('lost', 'cancelled', 'completed')
                ORDER BY created_at DESC
                LIMIT 50
            """, [])

            for proposal in proposals:
                proposal = dict(proposal)
                # Check if project title or client name is mentioned
                title = (proposal.get('project_name') or '').lower()
                client = (proposal.get('client_company') or '').lower()

                if (title and len(title) > 4 and title in text) or \
                   (client and len(client) > 4 and client in text):
                    suggestions.append({
                        'suggestion_type': 'email_link',
                        'priority': 'low',
                        'confidence_score': 0.6,
                        'source_type': 'email',
                        'source_id': email['email_id'],
                        'source_reference': f"Email: {subject[:50]}",
                        'title': f"Link email to {proposal['project_code']}",
                        'description': f"Project/client name mentioned: {proposal['project_name']}",
                        'suggested_action': 'Create email_proposal_link',
                        'suggested_data': json.dumps({
                            'email_id': email['email_id'],
                            'proposal_id': proposal['proposal_id'],
                            'project_code': proposal['project_code'],
                            'project_name': proposal['project_name'],
                            'match_type': 'name_mention'
                        }),
                        'target_table': 'email_proposal_links',
                        'project_code': proposal['project_code']
                    })
                    break  # Only one suggestion per email

        return suggestions

    def _detect_transcript_links(self, transcript: Dict) -> List[Dict]:
        """Detect potential proposal links for meeting transcripts"""
        suggestions = []

        # Skip if already linked
        if transcript.get('proposal_id'):
            return []

        title = transcript.get('title', '') or ''
        summary = transcript.get('summary', '') or ''
        text = f"{title} {summary}".lower()

        # Pattern 1: Look for project codes
        project_code_pattern = r'\b(\d{2}\s*BK[-\s]?\d{3})\b'
        matches = re.findall(project_code_pattern, text, re.IGNORECASE)

        for match in matches:
            normalized = re.sub(r'[\s-]+', ' ', match.upper()).strip()
            normalized = re.sub(r'(\d{2})\s*BK\s*(\d{3})', r'\1 BK-\2', normalized)

            existing = self.execute_query("""
                SELECT proposal_id, project_code, project_name
                FROM proposals WHERE project_code = ?
            """, [normalized])

            if existing:
                proposal = dict(existing[0])
                suggestions.append({
                    'suggestion_type': 'transcript_link',
                    'priority': 'medium',
                    'confidence_score': 0.85,
                    'source_type': 'transcript',
                    'source_id': transcript['id'],
                    'source_reference': f"Transcript: {title[:50]}",
                    'title': f"Link transcript to {normalized}",
                    'description': f"Project code {normalized} mentioned in transcript",
                    'suggested_action': 'Update meeting_transcripts.proposal_id',
                    'suggested_data': json.dumps({
                        'transcript_id': transcript['id'],
                        'proposal_id': proposal['proposal_id'],
                        'project_code': normalized,
                        'project_name': proposal['project_name'],
                        'match_type': 'project_code'
                    }),
                    'target_table': 'meeting_transcripts',
                    'project_code': normalized
                })

        # Pattern 2: Match by project/client name
        if not suggestions:
            proposals = self.execute_query("""
                SELECT proposal_id, project_code, project_name, client_company
                FROM proposals
                WHERE status NOT IN ('lost', 'cancelled', 'completed')
                ORDER BY created_at DESC
                LIMIT 50
            """, [])

            for proposal in proposals:
                proposal = dict(proposal)
                proj_title = (proposal.get('project_name') or '').lower()
                client = (proposal.get('client_company') or '').lower()

                if (proj_title and len(proj_title) > 4 and proj_title in text) or \
                   (client and len(client) > 4 and client in text):
                    suggestions.append({
                        'suggestion_type': 'transcript_link',
                        'priority': 'low',
                        'confidence_score': 0.6,
                        'source_type': 'transcript',
                        'source_id': transcript['id'],
                        'source_reference': f"Transcript: {title[:50]}",
                        'title': f"Link transcript to {proposal['project_code']}",
                        'description': f"Project/client name mentioned: {proposal['project_name']}",
                        'suggested_action': 'Update meeting_transcripts.proposal_id',
                        'suggested_data': json.dumps({
                            'transcript_id': transcript['id'],
                            'proposal_id': proposal['proposal_id'],
                            'project_code': proposal['project_code'],
                            'project_name': proposal['project_name'],
                            'match_type': 'name_mention'
                        }),
                        'target_table': 'meeting_transcripts',
                        'project_code': proposal['project_code']
                    })
                    break

        return suggestions

    def _create_info_suggestion(
        self,
        email: Dict,
        info_type: str,
        title: str,
        content: str,
        priority: str = 'low'
    ) -> Dict:
        """Create informational suggestion (no DB change, just visibility)"""
        return {
            'suggestion_type': 'info',
            'priority': priority,
            'confidence_score': 1.0,
            'source_type': 'email',
            'source_id': email['email_id'],
            'source_reference': f"Email: {email.get('subject', '')[:50]}",
            'title': title,
            'description': content,
            'suggested_action': 'Review information',
            'suggested_data': json.dumps({
                'info_type': info_type,
                'content': content
            }),
            'target_table': None,
            'project_code': email.get('linked_project_code')
        }

    def generate_suggestions_from_transcript(self, transcript_id: int) -> List[Dict]:
        """
        Analyze a meeting transcript and generate suggestions for linking.
        Called after transcript is imported.
        """
        suggestions = []

        # Get transcript data
        transcript_data = self.execute_query("""
            SELECT id, title, summary, proposal_id, detected_project_code
            FROM meeting_transcripts
            WHERE id = ?
        """, [transcript_id])

        if not transcript_data:
            return []

        transcript = dict(transcript_data[0])

        # Check for transcript link suggestions
        link_suggestions = self._detect_transcript_links(transcript)
        suggestions.extend(link_suggestions)

        # Save suggestions to database
        for suggestion in suggestions:
            self._save_suggestion(suggestion)

        return suggestions

    def _save_suggestion(self, suggestion: Dict) -> int:
        """Save a suggestion to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_suggestions (
                    suggestion_type, priority, confidence_score,
                    source_type, source_id, source_reference,
                    title, description, suggested_action,
                    suggested_data, target_table, project_code,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
            """, (
                suggestion['suggestion_type'],
                suggestion['priority'],
                suggestion['confidence_score'],
                suggestion['source_type'],
                suggestion['source_id'],
                suggestion['source_reference'],
                suggestion['title'],
                suggestion['description'],
                suggestion['suggested_action'],
                suggestion['suggested_data'],
                suggestion['target_table'],
                suggestion.get('project_code')
            ))
            conn.commit()
            return cursor.lastrowid

    # =========================================================================
    # SUGGESTION REVIEW
    # =========================================================================

    def get_pending_suggestions(
        self,
        suggestion_type: Optional[str] = None,
        project_code: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get pending suggestions for review"""
        query = """
            SELECT * FROM pending_suggestions_view
            WHERE 1=1
        """
        params = []

        if suggestion_type:
            query += " AND suggestion_type = ?"
            params.append(suggestion_type)

        if project_code:
            query += " AND project_code = ?"
            params.append(project_code)

        query += " LIMIT ?"
        params.append(limit)

        results = self.execute_query(query, params)
        return [dict(r) for r in results]

    def approve_suggestion(
        self,
        suggestion_id: int,
        reviewed_by: str,
        apply_changes: bool = True
    ) -> Dict[str, Any]:
        """Approve a suggestion and optionally apply the changes"""

        # Get the suggestion
        suggestion = self.execute_query("""
            SELECT * FROM ai_suggestions WHERE suggestion_id = ?
        """, [suggestion_id])

        if not suggestion:
            return {'success': False, 'error': 'Suggestion not found'}

        suggestion = dict(suggestion[0])

        # Update status
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ai_suggestions
                SET status = 'approved',
                    reviewed_by = ?,
                    reviewed_at = datetime('now')
                WHERE suggestion_id = ?
            """, (reviewed_by, suggestion_id))
            conn.commit()

        # Apply changes if requested
        # Note: Use suggestion_type to find handler, not target_table
        # (handlers know their own target tables)
        applied = False
        if apply_changes:
            applied = self._apply_suggestion(suggestion)

        # Record positive feedback for learning
        self._record_feedback(
            suggestion_id=suggestion_id,
            feedback_type='suggestion_correction',
            original_value=None,
            corrected_value='approved',
            taught_by=reviewed_by
        )

        # NEW: Learn patterns from approved email_link suggestions
        if suggestion.get('suggestion_type') == 'email_link' and applied:
            try:
                pattern_ids = self.pattern_learner.on_email_link_approved(
                    suggestion, suggestion_id
                )
                if pattern_ids:
                    logger.info(
                        f"Learned {len(pattern_ids)} patterns from suggestion {suggestion_id}"
                    )
            except Exception as e:
                # Don't fail the approval if pattern learning fails
                logger.warning(f"Pattern learning failed for suggestion {suggestion_id}: {e}")

        return {
            'success': True,
            'suggestion_id': suggestion_id,
            'applied': applied
        }

    def reject_suggestion(
        self,
        suggestion_id: int,
        reviewed_by: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject a suggestion"""

        # Get the suggestion first (needed for pattern learning)
        suggestion = self.execute_query("""
            SELECT * FROM ai_suggestions WHERE suggestion_id = ?
        """, [suggestion_id])

        suggestion_data = dict(suggestion[0]) if suggestion else {}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ai_suggestions
                SET status = 'rejected',
                    reviewed_by = ?,
                    reviewed_at = datetime('now'),
                    review_notes = ?
                WHERE suggestion_id = ?
            """, (reviewed_by, reason, suggestion_id))
            conn.commit()

        # Record negative feedback for learning
        self._record_feedback(
            suggestion_id=suggestion_id,
            feedback_type='suggestion_correction',
            original_value='suggested',
            corrected_value='rejected',
            lesson=reason,
            taught_by=reviewed_by
        )

        # NEW: Penalize patterns when email_link suggestions are rejected
        if suggestion_data.get('suggestion_type') == 'email_link':
            try:
                self.pattern_learner.on_email_link_rejected(
                    suggestion_data, suggestion_id
                )
                logger.info(f"Penalized patterns for rejected suggestion {suggestion_id}")
            except Exception as e:
                # Don't fail the rejection if pattern learning fails
                logger.warning(f"Pattern penalization failed for suggestion {suggestion_id}: {e}")

        return {'success': True, 'suggestion_id': suggestion_id}

    def modify_suggestion(
        self,
        suggestion_id: int,
        reviewed_by: str,
        corrected_data: Dict,
        apply_changes: bool = True
    ) -> Dict[str, Any]:
        """Modify a suggestion with corrections and apply"""

        # Get original suggestion
        suggestion = self.execute_query("""
            SELECT * FROM ai_suggestions WHERE suggestion_id = ?
        """, [suggestion_id])

        if not suggestion:
            return {'success': False, 'error': 'Suggestion not found'}

        suggestion = dict(suggestion[0])
        original_data = suggestion.get('suggested_data')

        # Update with corrections
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ai_suggestions
                SET status = 'modified',
                    reviewed_by = ?,
                    reviewed_at = datetime('now'),
                    correction_data = ?,
                    suggested_data = ?
                WHERE suggestion_id = ?
            """, (
                reviewed_by,
                original_data,
                json.dumps(corrected_data),
                suggestion_id
            ))
            conn.commit()

        # Apply corrected changes
        applied = False
        if apply_changes and suggestion['target_table']:
            suggestion['suggested_data'] = json.dumps(corrected_data)
            applied = self._apply_suggestion(suggestion)

        # Record correction for learning
        self._record_feedback(
            suggestion_id=suggestion_id,
            feedback_type='suggestion_correction',
            original_value=original_data,
            corrected_value=json.dumps(corrected_data),
            taught_by=reviewed_by
        )

        return {
            'success': True,
            'suggestion_id': suggestion_id,
            'applied': applied
        }

    def _apply_suggestion(self, suggestion: Dict) -> bool:
        """
        Apply a suggestion to the database using the handler registry.

        Uses handler-based architecture for supported types, with fallback
        to legacy logic for types without handlers yet.
        """
        try:
            suggestion_type = suggestion.get('suggestion_type')
            suggestion_id = suggestion.get('suggestion_id')
            data = json.loads(suggestion['suggested_data']) if suggestion.get('suggested_data') else {}

            with self.get_connection() as conn:
                # Try to get a handler for this suggestion type
                handler = HandlerRegistry.get_handler(suggestion_type, conn)

                if handler:
                    # Validate first
                    errors = handler.validate(data)
                    if errors:
                        print(f"Validation errors for suggestion {suggestion_id}: {errors}")
                        return False

                    # Apply using handler
                    result = handler.apply(suggestion, data)

                    if result.success and result.rollback_data:
                        # Store rollback data in the suggestion for undo capability
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE ai_suggestions
                            SET rollback_data = ?
                            WHERE suggestion_id = ?
                        """, (json.dumps(result.rollback_data), suggestion_id))
                        conn.commit()

                    return result.success

                # Fallback to legacy handling for types without handlers
                target_table = suggestion.get('target_table')
                cursor = conn.cursor()

                if target_table == 'contacts':
                    # Legacy: Add new contact
                    cursor.execute("""
                        INSERT OR IGNORE INTO contacts (name, email, first_seen, source)
                        VALUES (?, ?, ?, ?)
                    """, (
                        data.get('name'),
                        data.get('email'),
                        data.get('first_seen'),
                        'ai_suggestion'
                    ))
                    conn.commit()
                    return True

                elif target_table == 'proposals':
                    # Legacy: Update proposal
                    if 'new_value' in data:
                        cursor.execute("""
                            UPDATE proposals
                            SET project_value = ?,
                                updated_at = datetime('now'),
                                updated_by = 'ai_suggestion'
                            WHERE project_code = ?
                        """, (data['new_value'], suggestion['project_code']))
                        conn.commit()
                        return True

                elif target_table == 'meeting_transcripts':
                    # Legacy: Link transcript to proposal
                    transcript_id = data.get('transcript_id')
                    proposal_id = data.get('proposal_id')
                    if transcript_id and proposal_id:
                        cursor.execute("""
                            UPDATE meeting_transcripts
                            SET proposal_id = ?,
                                detected_project_code = ?
                            WHERE id = ?
                        """, (proposal_id, suggestion.get('project_code'), transcript_id))
                        conn.commit()
                        return True

            return False
        except Exception as e:
            print(f"Error applying suggestion: {e}")
            return False

    # =========================================================================
    # LEARNING & FEEDBACK
    # =========================================================================

    def _record_feedback(
        self,
        suggestion_id: Optional[int],
        feedback_type: str,
        original_value: Optional[str],
        corrected_value: str,
        taught_by: str,
        lesson: Optional[str] = None,
        context_text: Optional[str] = None
    ):
        """Record feedback for training"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO training_feedback (
                    suggestion_id, feedback_type,
                    original_value, corrected_value,
                    lesson, taught_by, taught_at
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                suggestion_id,
                feedback_type,
                original_value,
                corrected_value,
                lesson,
                taught_by
            ))
            conn.commit()

    def teach_pattern(
        self,
        pattern_name: str,
        pattern_type: str,
        condition: Dict,
        action: Dict,
        taught_by: str
    ) -> Dict[str, Any]:
        """Explicitly teach the AI a new pattern"""

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learned_patterns (
                    pattern_name, pattern_type,
                    condition, action,
                    confidence_score, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, 0.8, 1, datetime('now'), datetime('now'))
            """, (
                pattern_name,
                pattern_type,
                json.dumps(condition),
                json.dumps(action)
            ))
            pattern_id = cursor.lastrowid
            conn.commit()

        # Record as explicit instruction
        self._record_feedback(
            suggestion_id=None,
            feedback_type='explicit_instruction',
            original_value=None,
            corrected_value=json.dumps({'pattern_id': pattern_id}),
            lesson=f"Pattern: {pattern_name}",
            taught_by=taught_by
        )

        return {'success': True, 'pattern_id': pattern_id}

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about AI learning"""

        stats = {}

        # Suggestion stats
        suggestion_stats = self.execute_query("""
            SELECT
                status,
                COUNT(*) as count
            FROM ai_suggestions
            GROUP BY status
        """, [])
        stats['suggestions'] = {r['status']: r['count'] for r in suggestion_stats}

        # Feedback stats
        feedback_stats = self.execute_query("""
            SELECT
                feedback_type,
                COUNT(*) as count
            FROM training_feedback
            GROUP BY feedback_type
        """, [])
        stats['feedback'] = {r['feedback_type']: r['count'] for r in feedback_stats}

        # Pattern stats
        pattern_stats = self.execute_query("""
            SELECT COUNT(*) as count FROM learned_patterns WHERE is_active = 1
        """, [])
        stats['active_patterns'] = pattern_stats[0]['count'] if pattern_stats else 0

        # Approval rate
        total = sum(stats['suggestions'].values()) if stats['suggestions'] else 0
        approved = stats['suggestions'].get('approved', 0) + stats['suggestions'].get('modified', 0)
        stats['approval_rate'] = approved / total if total > 0 else 0

        return stats

    def get_learned_patterns(
        self,
        pattern_type: str = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get learned patterns from the database"""

        query = """
            SELECT
                pattern_id,
                pattern_name,
                pattern_type,
                condition,
                action,
                confidence_score,
                evidence_count,
                is_active,
                created_at,
                updated_at
            FROM learned_patterns
            WHERE 1=1
        """
        params = []

        if active_only:
            query += " AND is_active = 1"

        if pattern_type:
            query += " AND pattern_type = ?"
            params.append(pattern_type)

        query += " ORDER BY confidence_score DESC, created_at DESC"

        results = self.execute_query(query, params)

        patterns = []
        for r in results:
            pattern = dict(r)
            # Parse JSON fields
            if pattern.get('condition'):
                try:
                    pattern['condition'] = json.loads(pattern['condition'])
                except:
                    pass
            if pattern.get('action'):
                try:
                    pattern['action'] = json.loads(pattern['action'])
                except:
                    pass
            patterns.append(pattern)

        return patterns

    def get_recent_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent AI suggestion decisions (approvals/rejections)"""
        results = self.execute_query("""
            SELECT
                tf.feedback_id,
                tf.suggestion_id,
                tf.feedback_type,
                tf.original_value,
                tf.corrected_value,
                tf.context_type,
                tf.context_id,
                tf.lesson,
                tf.project_code,
                tf.client_company,
                tf.taught_by,
                tf.taught_at,
                tf.incorporated,
                tf.times_applied
            FROM training_feedback tf
            ORDER BY tf.taught_at DESC
            LIMIT ?
        """, [limit])

        decisions = []
        for row in results:
            decision = dict(row)
            decisions.append(decision)

        return decisions

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    def process_recent_emails_for_suggestions(self, hours: int = 24, limit: int = 100) -> Dict:
        """Process recent emails to generate suggestions"""

        # Get recently processed emails that haven't been scanned for suggestions
        emails = self.execute_query("""
            SELECT ec.email_id
            FROM email_content ec
            JOIN emails e ON ec.email_id = e.email_id
            WHERE e.date >= datetime('now', '-' || ? || ' hours')
            AND ec.email_id NOT IN (
                SELECT DISTINCT source_id FROM ai_suggestions WHERE source_type = 'email'
            )
            ORDER BY e.date DESC
            LIMIT ?
        """, [hours, limit])

        total_suggestions = 0
        for email in emails:
            suggestions = self.generate_suggestions_from_email(email['email_id'])
            total_suggestions += len(suggestions)

        return {
            'emails_processed': len(emails),
            'suggestions_generated': total_suggestions
        }

    # =========================================================================
    # RULE GENERATION ENGINE
    # =========================================================================

    def generate_rules_from_feedback(self, min_evidence: int = 3) -> Dict[str, Any]:
        """
        Analyze accumulated feedback and automatically generate learned patterns.

        This is the core of the learning system - it finds patterns in human
        corrections and creates rules that improve future AI behavior.

        Args:
            min_evidence: Minimum number of similar corrections needed to create a rule

        Returns:
            Summary of rules created/updated
        """
        results = {
            'rules_created': 0,
            'rules_updated': 0,
            'patterns_found': []
        }

        # 1. Analyze rejection patterns (suggestions that keep getting rejected)
        rejection_rules = self._analyze_rejection_patterns(min_evidence)
        for rule in rejection_rules:
            pattern_id = self._create_or_update_pattern(rule)
            if pattern_id:
                if rule.get('is_new'):
                    results['rules_created'] += 1
                else:
                    results['rules_updated'] += 1
                results['patterns_found'].append(rule['pattern_name'])

        # 2. Analyze modification patterns (how suggestions were corrected)
        correction_rules = self._analyze_correction_patterns(min_evidence)
        for rule in correction_rules:
            pattern_id = self._create_or_update_pattern(rule)
            if pattern_id:
                if rule.get('is_new'):
                    results['rules_created'] += 1
                else:
                    results['rules_updated'] += 1
                results['patterns_found'].append(rule['pattern_name'])

        # 3. Analyze category correction patterns (email categorization mistakes)
        category_rules = self._analyze_category_corrections(min_evidence)
        for rule in category_rules:
            pattern_id = self._create_or_update_pattern(rule)
            if pattern_id:
                if rule.get('is_new'):
                    results['rules_created'] += 1
                else:
                    results['rules_updated'] += 1
                results['patterns_found'].append(rule['pattern_name'])

        # 4. Analyze link correction patterns (project linking mistakes)
        link_rules = self._analyze_link_corrections(min_evidence)
        for rule in link_rules:
            pattern_id = self._create_or_update_pattern(rule)
            if pattern_id:
                if rule.get('is_new'):
                    results['rules_created'] += 1
                else:
                    results['rules_updated'] += 1
                results['patterns_found'].append(rule['pattern_name'])

        # 5. Mark processed feedback as incorporated
        self._mark_feedback_incorporated()

        return results

    def _analyze_rejection_patterns(self, min_evidence: int) -> List[Dict]:
        """
        Find patterns in rejected suggestions to avoid repeating mistakes.

        Example: If follow-up suggestions for a certain client are always rejected,
        create a rule to not generate those suggestions.
        """
        patterns = []

        # Find suggestion types that are frequently rejected for certain conditions
        rejection_analysis = self.execute_query("""
            SELECT
                s.suggestion_type,
                s.project_code,
                SUBSTR(s.project_code, 1, INSTR(s.project_code, ':') - 1) as project_prefix,
                COUNT(*) as rejection_count,
                GROUP_CONCAT(DISTINCT tf.lesson) as rejection_reasons
            FROM ai_suggestions s
            JOIN training_feedback tf ON s.suggestion_id = tf.suggestion_id
            WHERE s.status = 'rejected'
            AND tf.feedback_type = 'suggestion_correction'
            GROUP BY s.suggestion_type, project_prefix
            HAVING rejection_count >= ?
        """, [min_evidence])

        for row in rejection_analysis:
            row = dict(row)
            pattern_name = f"reject_{row['suggestion_type']}_{row['project_prefix'] or 'general'}"

            patterns.append({
                'pattern_name': pattern_name,
                'pattern_type': 'business_rule',
                'condition': {
                    'suggestion_type': row['suggestion_type'],
                    'project_prefix': row['project_prefix']
                },
                'action': {
                    'suppress': True,
                    'reason': row['rejection_reasons']
                },
                'evidence_count': row['rejection_count'],
                'confidence_score': min(0.9, 0.5 + (row['rejection_count'] * 0.1))
            })

        return patterns

    def _analyze_correction_patterns(self, min_evidence: int) -> List[Dict]:
        """
        Find patterns in how suggestions were modified.

        Example: If fee suggestions are consistently reduced by 20%,
        learn to apply that adjustment.
        """
        patterns = []

        # Find modified suggestions and analyze the corrections
        modification_analysis = self.execute_query("""
            SELECT
                s.suggestion_type,
                s.suggested_data as original_data,
                s.correction_data,
                tf.lesson,
                COUNT(*) OVER (PARTITION BY s.suggestion_type) as type_count
            FROM ai_suggestions s
            JOIN training_feedback tf ON s.suggestion_id = tf.suggestion_id
            WHERE s.status = 'modified'
            AND s.correction_data IS NOT NULL
        """, [])

        # Group by suggestion type and analyze
        type_corrections = {}
        for row in modification_analysis:
            row = dict(row)
            stype = row['suggestion_type']
            if stype not in type_corrections:
                type_corrections[stype] = []
            type_corrections[stype].append({
                'original': row['original_data'],
                'corrected': row['correction_data'],
                'lesson': row['lesson']
            })

        for stype, corrections in type_corrections.items():
            if len(corrections) >= min_evidence:
                # Analyze the corrections to find common adjustments
                lessons = [c['lesson'] for c in corrections if c['lesson']]
                if lessons:
                    pattern_name = f"adjust_{stype}"
                    patterns.append({
                        'pattern_name': pattern_name,
                        'pattern_type': 'entity_pattern',
                        'condition': {
                            'suggestion_type': stype
                        },
                        'action': {
                            'adjustments': lessons[:5],  # Top 5 lessons
                            'apply_review': True
                        },
                        'evidence_count': len(corrections),
                        'confidence_score': min(0.85, 0.5 + (len(corrections) * 0.1))
                    })

        return patterns

    def _analyze_category_corrections(self, min_evidence: int) -> List[Dict]:
        """
        Find patterns in email category corrections.

        Example: Emails from domain X should always be category Y.
        """
        patterns = []

        # Find category corrections
        category_corrections = self.execute_query("""
            SELECT
                tf.original_value,
                tf.corrected_value,
                tf.context_text,
                tf.lesson,
                COUNT(*) as correction_count
            FROM training_feedback tf
            WHERE tf.feedback_type = 'category_correction'
            GROUP BY tf.original_value, tf.corrected_value
            HAVING correction_count >= ?
        """, [min_evidence])

        for row in category_corrections:
            row = dict(row)
            pattern_name = f"category_{row['original_value']}_to_{row['corrected_value']}"

            patterns.append({
                'pattern_name': pattern_name,
                'pattern_type': 'entity_pattern',
                'condition': {
                    'incorrect_category': row['original_value'],
                    'context_hint': row['context_text'][:100] if row['context_text'] else None
                },
                'action': {
                    'correct_category': row['corrected_value'],
                    'lesson': row['lesson']
                },
                'evidence_count': row['correction_count'],
                'confidence_score': min(0.9, 0.6 + (row['correction_count'] * 0.1))
            })

        return patterns

    def _analyze_link_corrections(self, min_evidence: int) -> List[Dict]:
        """
        Find patterns in project link corrections.

        Example: Emails mentioning "Wynn" should link to project 24 BK-089.
        """
        patterns = []

        # Find link corrections
        link_corrections = self.execute_query("""
            SELECT
                tf.original_value,
                tf.corrected_value,
                tf.lesson,
                COUNT(*) as correction_count
            FROM training_feedback tf
            WHERE tf.feedback_type = 'link_correction'
            GROUP BY tf.corrected_value
            HAVING correction_count >= ?
        """, [min_evidence])

        for row in link_corrections:
            row = dict(row)
            if row['corrected_value']:
                pattern_name = f"link_to_{row['corrected_value'].replace(' ', '_')}"

                patterns.append({
                    'pattern_name': pattern_name,
                    'pattern_type': 'entity_pattern',
                    'condition': {
                        'previous_links': row['original_value']
                    },
                    'action': {
                        'correct_project': row['corrected_value'],
                        'lesson': row['lesson']
                    },
                    'evidence_count': row['correction_count'],
                    'confidence_score': min(0.9, 0.6 + (row['correction_count'] * 0.1))
                })

        return patterns

    def _create_or_update_pattern(self, rule: Dict) -> Optional[int]:
        """
        Create a new pattern or update existing one with more evidence.
        """
        # Check for existing similar pattern
        existing = self.execute_query("""
            SELECT pattern_id, evidence_count, confidence_score
            FROM learned_patterns
            WHERE pattern_name = ?
            AND is_active = 1
        """, [rule['pattern_name']])

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if existing:
                # Update existing pattern
                existing = dict(existing[0])
                new_evidence = existing['evidence_count'] + rule['evidence_count']
                new_confidence = min(0.95, rule['confidence_score'] + 0.05)  # Boost confidence

                cursor.execute("""
                    UPDATE learned_patterns
                    SET evidence_count = ?,
                        confidence_score = ?,
                        condition = ?,
                        action = ?,
                        updated_at = datetime('now')
                    WHERE pattern_id = ?
                """, (
                    new_evidence,
                    new_confidence,
                    json.dumps(rule['condition']),
                    json.dumps(rule['action']),
                    existing['pattern_id']
                ))
                conn.commit()
                rule['is_new'] = False
                return existing['pattern_id']
            else:
                # Create new pattern
                cursor.execute("""
                    INSERT INTO learned_patterns (
                        pattern_name, pattern_type,
                        condition, action,
                        evidence_count, confidence_score,
                        is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'), datetime('now'))
                """, (
                    rule['pattern_name'],
                    rule['pattern_type'],
                    json.dumps(rule['condition']),
                    json.dumps(rule['action']),
                    rule['evidence_count'],
                    rule['confidence_score']
                ))
                conn.commit()
                rule['is_new'] = True
                return cursor.lastrowid

    def _mark_feedback_incorporated(self):
        """Mark processed feedback as incorporated into patterns"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE training_feedback
                SET incorporated = 1,
                    incorporated_at = datetime('now')
                WHERE incorporated = 0
            """)
            conn.commit()

    def should_suppress_suggestion(self, suggestion_type: str, project_code: str = None) -> bool:
        """
        Check if a suggestion should be suppressed based on learned patterns.

        Used by suggestion generation to avoid making known bad suggestions.
        """
        if not project_code:
            return False

        # Extract project prefix (e.g., "25 BK" from "25 BK-015")
        project_prefix = project_code.split('-')[0] if '-' in project_code else None

        # Check for suppression patterns
        suppression_patterns = self.execute_query("""
            SELECT pattern_id, confidence_score
            FROM learned_patterns
            WHERE pattern_type = 'business_rule'
            AND is_active = 1
            AND confidence_score > 0.7
            AND json_extract(condition, '$.suggestion_type') = ?
            AND (
                json_extract(condition, '$.project_prefix') IS NULL
                OR json_extract(condition, '$.project_prefix') = ?
            )
        """, [suggestion_type, project_prefix])

        return len(suppression_patterns) > 0

    def get_suggestion_adjustments(self, suggestion_type: str) -> List[Dict]:
        """
        Get learned adjustments for a suggestion type.

        Returns lessons/adjustments that should be applied to suggestions
        of this type based on past corrections.
        """
        adjustments = self.execute_query("""
            SELECT condition, action
            FROM learned_patterns
            WHERE pattern_type = 'entity_pattern'
            AND is_active = 1
            AND confidence_score > 0.6
            AND json_extract(condition, '$.suggestion_type') = ?
        """, [suggestion_type])

        return [
            {
                'condition': json.loads(a['condition']),
                'action': json.loads(a['action'])
            }
            for a in adjustments
        ]

    def validate_patterns(self, test_limit: int = 50) -> Dict[str, Any]:
        """
        Test learned patterns against recent suggestions to validate accuracy.

        Returns validation metrics for each pattern.
        """
        results = {
            'patterns_tested': 0,
            'validations': []
        }

        # Get active patterns
        patterns = self.execute_query("""
            SELECT pattern_id, pattern_name, pattern_type, condition, action, confidence_score
            FROM learned_patterns
            WHERE is_active = 1
        """, [])

        for pattern in patterns:
            pattern = dict(pattern)
            condition = json.loads(pattern['condition']) if pattern['condition'] else {}

            # Test pattern against recent reviewed suggestions
            validation_result = {
                'pattern_id': pattern['pattern_id'],
                'pattern_name': pattern['pattern_name'],
                'current_confidence': pattern['confidence_score'],
                'test_results': {}
            }

            # Different validation based on pattern type
            if pattern['pattern_type'] == 'business_rule':
                # For suppression rules, check if similar suggestions are still being rejected
                suggestion_type = condition.get('suggestion_type')
                if suggestion_type:
                    recent_rejections = self.execute_query("""
                        SELECT COUNT(*) as count
                        FROM ai_suggestions
                        WHERE suggestion_type = ?
                        AND status = 'rejected'
                        AND reviewed_at >= datetime('now', '-30 days')
                    """, [suggestion_type])

                    recent_approvals = self.execute_query("""
                        SELECT COUNT(*) as count
                        FROM ai_suggestions
                        WHERE suggestion_type = ?
                        AND status IN ('approved', 'modified')
                        AND reviewed_at >= datetime('now', '-30 days')
                    """, [suggestion_type])

                    rejections = recent_rejections[0]['count'] if recent_rejections else 0
                    approvals = recent_approvals[0]['count'] if recent_approvals else 0

                    validation_result['test_results'] = {
                        'recent_rejections': rejections,
                        'recent_approvals': approvals,
                        'still_valid': rejections > approvals
                    }

            results['validations'].append(validation_result)
            results['patterns_tested'] += 1

        return results

    def decay_unused_patterns(self, days_threshold: int = 30) -> int:
        """
        Reduce confidence of patterns that haven't been validated recently.

        This prevents stale patterns from over-influencing the system.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE learned_patterns
                SET confidence_score = MAX(0.3, confidence_score * 0.9),
                    updated_at = datetime('now')
                WHERE is_active = 1
                AND (
                    last_validated IS NULL
                    OR last_validated < datetime('now', '-' || ? || ' days')
                )
            """, [days_threshold])
            affected = cursor.rowcount
            conn.commit()
            return affected
