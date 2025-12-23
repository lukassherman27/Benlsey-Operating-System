"""
CLI Review Helper - Learning from Manual Corrections

This service provides methods for the CLI-based email review workflow
where Claude helps review suggestions and corrections are made manually.

It ensures that all corrections are captured as learned patterns so the
AI improves over time.

Usage (in CLI/Claude sessions):
    from services.cli_review_helper import CLIReviewHelper
    helper = CLIReviewHelper()

    # After approving suggestions
    helper.learn_from_approval(email_id, project_code, proposal_id)

    # After correcting a wrong suggestion
    helper.learn_from_correction(email_id, wrong_code, correct_code, correct_proposal_id)

    # After linking to internal category
    helper.learn_internal_link(email_id, category_code)  # e.g., 'INT-OPS'

    # After marking as skip (cancelled project, spam, etc)
    helper.learn_skip(email_id, reason)

    # After merging projects
    helper.learn_project_redirect(old_code, new_code, new_proposal_id)
"""

import sqlite3
import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

import os
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

logger = logging.getLogger(__name__)


class CLIReviewHelper:
    """
    Helper service for learning from CLI-based email review sessions.

    This bridges the gap between manual SQL corrections and the learning system.
    Call these methods after making manual corrections to ensure patterns are learned.
    """

    # Internal category mappings
    INTERNAL_CATEGORIES = {
        'INT-OPS': (2, 'IT/Operations'),
        'INT-FIN': (1, 'Finance'),
        'INT-LEGAL': (3, 'Legal'),
        'INT-MKTG': (4, 'Marketing'),
        'INT-BILL': (5, 'Bill/Principal'),
    }

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_email_info(self, email_id: int) -> Optional[Dict[str, Any]]:
        """Get email details needed for pattern creation."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT email_id, sender_email, sender_name, subject, thread_id
            FROM emails WHERE email_id = ?
        """, (email_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def _extract_email_address(self, email_str: str) -> Optional[str]:
        """Extract clean email from RFC 5322 format."""
        if not email_str or '@' not in email_str:
            return None
        match = re.search(r'<([^>]+@[^>]+)>', email_str)
        if match:
            return match.group(1).lower().strip()
        return email_str.lower().strip()

    def _extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address."""
        clean = self._extract_email_address(email)
        if clean and '@' in clean:
            return clean.split('@')[1].lower()
        return None

    def _is_internal_domain(self, domain: str) -> bool:
        """Check if domain is internal Bensley staff."""
        internal = {'bensley.com', 'bensleydesign.com', 'bensley.co.th', 'bensley.id', 'bensley.co.id'}
        return domain.lower() in internal if domain else False

    def _is_generic_domain(self, domain: str) -> bool:
        """Check if domain is a generic email provider."""
        generic = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                   'aol.com', 'icloud.com', 'mail.com', 'protonmail.com'}
        return domain.lower() in generic if domain else False

    def _get_proposal_info(self, proposal_id: int = None, project_code: str = None) -> Optional[Dict]:
        """Get proposal details by ID or code."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if proposal_id:
            cursor.execute("SELECT proposal_id, project_code, project_name FROM proposals WHERE proposal_id = ?", (proposal_id,))
        elif project_code:
            cursor.execute("SELECT proposal_id, project_code, project_name FROM proposals WHERE project_code = ?", (project_code,))
        else:
            conn.close()
            return None
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def _get_project_info(self, project_id: int = None, project_code: str = None) -> Optional[Dict]:
        """Get project details by ID or code."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if project_id:
            cursor.execute("SELECT project_id, project_code, project_title FROM projects WHERE project_id = ?", (project_id,))
        elif project_code:
            cursor.execute("SELECT project_id, project_code, project_title FROM projects WHERE project_code = ?", (project_code,))
        else:
            conn.close()
            return None
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def _store_pattern(
        self,
        pattern_type: str,
        pattern_key: str,
        target_type: str,
        target_id: int,
        target_code: str,
        target_name: str = None,
        confidence: float = 0.85,
        email_id: int = None,
        notes: str = None
    ) -> Optional[int]:
        """Store or update a learned pattern."""
        conn = self._get_connection()
        cursor = conn.cursor()

        pattern_key_normalized = pattern_key.lower().strip() if pattern_key else None

        # Check if pattern exists
        cursor.execute("""
            SELECT pattern_id, confidence, times_correct
            FROM email_learned_patterns
            WHERE pattern_type = ?
              AND pattern_key_normalized = ?
              AND target_type = ?
              AND target_id = ?
        """, (pattern_type, pattern_key_normalized, target_type, target_id))
        existing = cursor.fetchone()

        if existing:
            # Boost existing pattern
            new_confidence = min(existing['confidence'] + 0.05, 0.98)
            cursor.execute("""
                UPDATE email_learned_patterns
                SET confidence = ?,
                    times_correct = times_correct + 1,
                    last_used_at = datetime('now'),
                    notes = COALESCE(?, notes)
                WHERE pattern_id = ?
            """, (new_confidence, notes, existing['pattern_id']))
            conn.commit()
            pattern_id = existing['pattern_id']
            logger.info(f"Boosted pattern {pattern_id}: {pattern_key} -> {target_code} (conf: {new_confidence:.2f})")
        else:
            # Create new pattern
            cursor.execute("""
                INSERT INTO email_learned_patterns (
                    pattern_type, pattern_key, pattern_key_normalized,
                    target_type, target_id, target_code, target_name,
                    confidence, times_correct, created_from_email_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                pattern_type, pattern_key, pattern_key_normalized,
                target_type, target_id, target_code, target_name,
                confidence, email_id, notes
            ))
            conn.commit()
            pattern_id = cursor.lastrowid
            logger.info(f"Created pattern {pattern_id}: {pattern_type} '{pattern_key}' -> {target_code}")

        conn.close()
        return pattern_id

    # =========================================================================
    # PUBLIC METHODS - Call these after making corrections
    # =========================================================================

    def learn_from_approval(
        self,
        email_id: int,
        project_code: str,
        proposal_id: int = None,
        project_id: int = None
    ) -> List[int]:
        """
        Learn patterns from an approved email-to-project link.

        Call this after approving a correct suggestion or creating a manual link.
        Creates sender and domain patterns.

        Args:
            email_id: The email that was linked
            project_code: Project code (e.g., '25 BK-030')
            proposal_id: Proposal ID if linking to proposal
            project_id: Project ID if linking to active project

        Returns:
            List of created/updated pattern IDs
        """
        email = self._get_email_info(email_id)
        if not email:
            logger.warning(f"Email {email_id} not found")
            return []

        pattern_ids = []
        sender_email = self._extract_email_address(email.get('sender_email', ''))
        domain = self._extract_domain(email.get('sender_email', ''))

        # Determine target type and get name
        if proposal_id:
            target_type = 'proposal'
            target_id = proposal_id
            proposal = self._get_proposal_info(proposal_id=proposal_id)
            target_name = proposal.get('project_name') if proposal else None
        elif project_id:
            target_type = 'project'
            target_id = project_id
            project = self._get_project_info(project_id=project_id)
            target_name = project.get('project_title') if project else None
        else:
            # Try to find by code
            proposal = self._get_proposal_info(project_code=project_code)
            if proposal:
                target_type = 'proposal'
                target_id = proposal['proposal_id']
                target_name = proposal.get('project_name')
            else:
                project = self._get_project_info(project_code=project_code)
                if project:
                    target_type = 'project'
                    target_id = project['project_id']
                    target_name = project.get('project_title')
                else:
                    logger.warning(f"Could not find proposal/project for {project_code}")
                    return []

        # Skip internal staff
        if domain and self._is_internal_domain(domain):
            logger.info(f"Skipping patterns for internal domain: {domain}")
            return []

        # Create sender pattern
        if sender_email:
            pattern_type = f'sender_to_{target_type}'
            pid = self._store_pattern(
                pattern_type=pattern_type,
                pattern_key=sender_email,
                target_type=target_type,
                target_id=target_id,
                target_code=project_code,
                target_name=target_name,
                confidence=0.80,
                email_id=email_id,
                notes=f"Learned from CLI review approval"
            )
            if pid:
                pattern_ids.append(pid)

        # Create domain pattern (if corporate)
        if domain and not self._is_generic_domain(domain):
            pattern_type = f'domain_to_{target_type}'
            pid = self._store_pattern(
                pattern_type=pattern_type,
                pattern_key=domain,
                target_type=target_type,
                target_id=target_id,
                target_code=project_code,
                target_name=target_name,
                confidence=0.70,
                email_id=email_id,
                notes=f"Learned from CLI review approval"
            )
            if pid:
                pattern_ids.append(pid)

        return pattern_ids

    def learn_from_correction(
        self,
        email_id: int,
        wrong_code: str,
        correct_code: str,
        correct_proposal_id: int = None,
        correct_project_id: int = None
    ) -> Tuple[List[int], int]:
        """
        Learn from a correction (wrong suggestion → correct project).

        Call this after correcting an AI suggestion that linked to the wrong project.
        Creates positive patterns for the correct project and penalizes wrong patterns.

        Args:
            email_id: The email that was incorrectly linked
            wrong_code: The wrong project code that was suggested
            correct_code: The correct project code
            correct_proposal_id: Correct proposal ID (if proposal)
            correct_project_id: Correct project ID (if active project)

        Returns:
            Tuple of (created pattern IDs, number of penalized patterns)
        """
        email = self._get_email_info(email_id)
        if not email:
            logger.warning(f"Email {email_id} not found")
            return [], 0

        # First, create positive patterns for the correct project
        created = self.learn_from_approval(
            email_id=email_id,
            project_code=correct_code,
            proposal_id=correct_proposal_id,
            project_id=correct_project_id
        )

        # Then penalize patterns that led to the wrong suggestion
        sender_email = self._extract_email_address(email.get('sender_email', ''))

        conn = self._get_connection()
        cursor = conn.cursor()

        # Find and penalize wrong patterns
        cursor.execute("""
            UPDATE email_learned_patterns
            SET times_rejected = times_rejected + 1,
                confidence = MAX(confidence - 0.15, 0.3),
                notes = COALESCE(notes || ' | ', '') || 'Penalized: linked to ' || ? || ' but should be ' || ?
            WHERE pattern_key_normalized = ?
              AND target_code = ?
              AND is_active = 1
        """, (wrong_code, correct_code, sender_email, wrong_code))

        penalized = cursor.rowcount
        conn.commit()
        conn.close()

        if penalized:
            logger.info(f"Penalized {penalized} patterns for {sender_email} -> {wrong_code}")

        return created, penalized

    def learn_internal_link(
        self,
        email_id: int,
        category_code: str
    ) -> List[int]:
        """
        Learn that emails like this should be linked to an internal category.

        Call this after linking an email to INT-OPS, INT-FIN, etc.
        Creates domain_to_internal and sender_to_internal patterns.

        Args:
            email_id: The email linked to internal category
            category_code: Category code like 'INT-OPS', 'INT-FIN'

        Returns:
            List of created pattern IDs
        """
        if category_code not in self.INTERNAL_CATEGORIES:
            logger.warning(f"Unknown internal category: {category_code}")
            return []

        category_id, category_name = self.INTERNAL_CATEGORIES[category_code]

        email = self._get_email_info(email_id)
        if not email:
            logger.warning(f"Email {email_id} not found")
            return []

        pattern_ids = []
        domain = self._extract_domain(email.get('sender_email', ''))

        # Skip internal Bensley domains
        if domain and self._is_internal_domain(domain):
            logger.info(f"Skipping internal patterns for Bensley domain: {domain}")
            return []

        # Create domain_to_internal pattern
        if domain and not self._is_generic_domain(domain):
            pid = self._store_pattern(
                pattern_type='domain_to_internal',
                pattern_key=domain,
                target_type='internal',
                target_id=category_id,
                target_code=category_code,
                target_name=category_name,
                confidence=0.85,
                email_id=email_id,
                notes=f"Learned from CLI review - internal category"
            )
            if pid:
                pattern_ids.append(pid)

        return pattern_ids

    def learn_skip(
        self,
        email_id: int,
        reason: str = None
    ) -> List[int]:
        """
        Learn that emails like this should be skipped (not linked to any project).

        Call this after marking an email as skip (cancelled project, spam, irrelevant, etc.)
        Creates domain_to_skip pattern.

        Args:
            email_id: The email marked as skip
            reason: Why this is being skipped (e.g., "Cancelled project", "Spam")

        Returns:
            List of created pattern IDs
        """
        email = self._get_email_info(email_id)
        if not email:
            logger.warning(f"Email {email_id} not found")
            return []

        pattern_ids = []
        domain = self._extract_domain(email.get('sender_email', ''))

        # Only create skip patterns for non-generic, non-internal domains
        if domain and not self._is_generic_domain(domain) and not self._is_internal_domain(domain):
            pid = self._store_pattern(
                pattern_type='domain_to_skip',
                pattern_key=domain,
                target_type='skip',
                target_id=0,  # No specific target
                target_code='SKIP',
                target_name=reason or 'Skip - do not link',
                confidence=0.90,
                email_id=email_id,
                notes=f"Learned from CLI review - skip: {reason}"
            )
            if pid:
                pattern_ids.append(pid)

        return pattern_ids

    def learn_project_redirect(
        self,
        old_code: str,
        new_code: str,
        new_proposal_id: int = None
    ) -> Optional[int]:
        """
        Learn that one project code redirects to another (merged projects).

        Call this when projects are merged (e.g., 25 BK-043 → 25 BK-087).
        Creates a project_redirect pattern.

        Args:
            old_code: The old/merged project code
            new_code: The new/primary project code
            new_proposal_id: Proposal ID of the new project

        Returns:
            Pattern ID or None
        """
        # Get target info
        if new_proposal_id:
            target_type = 'proposal'
            target_id = new_proposal_id
            proposal = self._get_proposal_info(proposal_id=new_proposal_id)
            target_name = proposal.get('project_name') if proposal else None
        else:
            proposal = self._get_proposal_info(project_code=new_code)
            if proposal:
                target_type = 'proposal'
                target_id = proposal['proposal_id']
                target_name = proposal.get('project_name')
            else:
                project = self._get_project_info(project_code=new_code)
                if project:
                    target_type = 'project'
                    target_id = project['project_id']
                    target_name = project.get('project_title')
                else:
                    logger.warning(f"Could not find target project for {new_code}")
                    return None

        pid = self._store_pattern(
            pattern_type='project_redirect',
            pattern_key=old_code,
            target_type=target_type,
            target_id=target_id,
            target_code=new_code,
            target_name=target_name,
            confidence=1.0,  # Redirects are definitive
            notes=f"Project merge: {old_code} merged into {new_code}"
        )

        return pid

    def learn_keyword_pattern(
        self,
        keyword: str,
        project_code: str,
        proposal_id: int = None,
        project_id: int = None
    ) -> Optional[int]:
        """
        Learn a keyword pattern (e.g., "Sukhothai" → 25 BK-046).

        Call this when you notice emails with certain keywords always belong to a project.

        Args:
            keyword: The keyword to match in email subjects
            project_code: The project code to link to
            proposal_id: Proposal ID if linking to proposal
            project_id: Project ID if linking to active project

        Returns:
            Pattern ID or None
        """
        # Determine target
        if proposal_id:
            target_type = 'proposal'
            target_id = proposal_id
            proposal = self._get_proposal_info(proposal_id=proposal_id)
            target_name = proposal.get('project_name') if proposal else None
        elif project_id:
            target_type = 'project'
            target_id = project_id
            project = self._get_project_info(project_id=project_id)
            target_name = project.get('project_title') if project else None
        else:
            proposal = self._get_proposal_info(project_code=project_code)
            if proposal:
                target_type = 'proposal'
                target_id = proposal['proposal_id']
                target_name = proposal.get('project_name')
            else:
                project = self._get_project_info(project_code=project_code)
                if project:
                    target_type = 'project'
                    target_id = project['project_id']
                    target_name = project.get('project_title')
                else:
                    logger.warning(f"Could not find project for {project_code}")
                    return None

        pattern_type = f'keyword_to_{target_type}'
        pid = self._store_pattern(
            pattern_type=pattern_type,
            pattern_key=keyword,
            target_type=target_type,
            target_id=target_id,
            target_code=project_code,
            target_name=target_name,
            confidence=0.90,
            notes=f"Keyword pattern from CLI review"
        )

        return pid

    # =========================================================================
    # BATCH OPERATIONS - For processing multiple emails at once
    # =========================================================================

    def batch_learn_approvals(
        self,
        approvals: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Learn from a batch of approvals.

        Args:
            approvals: List of dicts with keys: email_id, project_code, proposal_id/project_id

        Returns:
            Summary of patterns created
        """
        total_created = 0
        for approval in approvals:
            created = self.learn_from_approval(
                email_id=approval['email_id'],
                project_code=approval['project_code'],
                proposal_id=approval.get('proposal_id'),
                project_id=approval.get('project_id')
            )
            total_created += len(created)

        return {'patterns_created': total_created, 'emails_processed': len(approvals)}

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learned patterns."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT pattern_type, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM email_learned_patterns
            WHERE is_active = 1
            GROUP BY pattern_type
            ORDER BY count DESC
        """)
        by_type = {row['pattern_type']: {'count': row['count'], 'avg_conf': round(row['avg_confidence'], 2)}
                   for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) as total FROM email_learned_patterns WHERE is_active = 1")
        total = cursor.fetchone()['total']

        cursor.execute("""
            SELECT target_code, target_name, COUNT(*) as patterns
            FROM email_learned_patterns
            WHERE is_active = 1
            GROUP BY target_code
            ORDER BY patterns DESC
            LIMIT 10
        """)
        top_projects = [{'code': row['target_code'], 'name': row['target_name'], 'patterns': row['patterns']}
                        for row in cursor.fetchall()]

        conn.close()

        return {
            'total_patterns': total,
            'by_type': by_type,
            'top_projects': top_projects
        }


# Convenience function for quick access
def get_cli_helper(db_path: str = None) -> CLIReviewHelper:
    """Get CLI review helper instance."""
    return CLIReviewHelper(db_path or DB_PATH)


def show_pending_reviews(limit: int = 20) -> List[Dict]:
    """
    Display pending email_link suggestions with full context for CLI review.
    Returns list of suggestions for easy reference.
    """
    helper = get_cli_helper()
    conn = helper._get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.suggestion_id,
            s.source_id as email_id,
            e.date,
            e.sender_email,
            e.sender_name,
            e.recipient_emails,
            e.subject,
            SUBSTR(e.body_full, 1, 300) as body_preview,
            e.email_direction,
            s.project_code as suggested_code,
            s.confidence_score,
            s.description as reasoning,
            json_extract(s.suggested_data, '$.project_name') as suggested_name,
            json_extract(s.suggested_data, '$.gpt_reasoning') as gpt_reasoning,
            json_extract(s.suggested_data, '$.gpt_evidence') as gpt_evidence,
            json_extract(s.suggested_data, '$.email_type') as email_type
        FROM ai_suggestions s
        JOIN emails e ON s.source_id = e.email_id
        WHERE s.status = 'pending'
        AND s.suggestion_type = 'email_link'
        ORDER BY e.date ASC
        LIMIT ?
    """, (limit,))

    reviews = [dict(row) for row in cursor.fetchall()]
    conn.close()

    print(f"\n{'='*80}")
    print(f"📧 {len(reviews)} PENDING EMAIL LINK REVIEWS")
    print(f"{'='*80}\n")

    for i, r in enumerate(reviews, 1):
        direction_icon = {
            'internal_to_internal': '🔄',
            'internal_to_external': '📤',
            'external_to_internal': '📥',
            'external_to_external': '🔀',
        }.get(r.get('email_direction'), '❓')

        print(f"[{i}] ID: {r['suggestion_id']} | Email ID: {r['email_id']}")
        print(f"    {direction_icon} Direction: {r.get('email_direction', 'unknown')}")
        print(f"    📅 Date: {r['date']}")
        print(f"    👤 From: {r['sender_email']}")
        if r.get('recipient_emails'):
            print(f"    📬 To: {r['recipient_emails'][:60]}")
        print(f"    📝 Subject: {r['subject']}")
        print(f"    💡 Suggested: {r['suggested_code']} ({r.get('suggested_name', 'N/A')})")
        print(f"    📊 Confidence: {r['confidence_score']:.0%}")
        if r.get('gpt_reasoning'):
            print(f"    🤖 GPT Reason: {r['gpt_reasoning'][:100]}")
        if r.get('gpt_evidence'):
            try:
                evidence = json.loads(r['gpt_evidence']) if isinstance(r['gpt_evidence'], str) else r['gpt_evidence']
                if evidence:
                    print(f"    📌 Evidence: {', '.join(evidence[:3])}")
            except (json.JSONDecodeError, TypeError):
                pass
        print()

    return reviews


def bulk_reject_suggestions(suggestion_ids: List[int], reason: str = None) -> int:
    """
    Bulk reject a list of suggestion IDs.

    Args:
        suggestion_ids: List of suggestion IDs to reject
        reason: Optional reason for rejection

    Returns:
        Number of rejected suggestions
    """
    helper = get_cli_helper()
    conn = helper._get_connection()
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(suggestion_ids))
    cursor.execute(f"""
        UPDATE ai_suggestions
        SET status = 'rejected',
            review_notes = ?,
            reviewed_at = datetime('now')
        WHERE suggestion_id IN ({placeholders})
    """, (reason,) + tuple(suggestion_ids))

    rejected = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"✅ Rejected {rejected} suggestions")
    return rejected


def approve_suggestion(suggestion_id: int, learn_patterns: bool = True) -> Dict:
    """
    Approve a single suggestion and optionally learn patterns.

    Args:
        suggestion_id: The suggestion to approve
        learn_patterns: Whether to create sender/domain patterns

    Returns:
        Result dict
    """
    helper = get_cli_helper()
    conn = helper._get_connection()
    cursor = conn.cursor()

    # Get suggestion details
    cursor.execute("""
        SELECT s.*, e.sender_email
        FROM ai_suggestions s
        JOIN emails e ON s.source_id = e.email_id
        WHERE s.suggestion_id = ?
    """, (suggestion_id,))
    suggestion = cursor.fetchone()

    if not suggestion:
        conn.close()
        return {'success': False, 'error': 'Suggestion not found'}

    suggestion = dict(suggestion)
    suggested_data = json.loads(suggestion.get('suggested_data', '{}'))
    email_id = suggestion['source_id']
    project_code = suggested_data.get('project_code')
    proposal_id = suggested_data.get('proposal_id')

    # Apply the link
    if proposal_id:
        cursor.execute("""
            INSERT OR IGNORE INTO email_proposal_links
            (email_id, proposal_id, confidence_score, match_method, created_at)
            VALUES (?, ?, ?, 'approved_suggestion', datetime('now'))
        """, (email_id, proposal_id, suggestion['confidence_score']))

    # Update suggestion status
    cursor.execute("""
        UPDATE ai_suggestions
        SET status = 'approved',
            reviewed_at = datetime('now')
        WHERE suggestion_id = ?
    """, (suggestion_id,))

    conn.commit()
    conn.close()

    # Learn patterns
    patterns_created = []
    if learn_patterns:
        patterns_created = helper.learn_from_approval(
            email_id=email_id,
            project_code=project_code,
            proposal_id=proposal_id
        )

    print(f"✅ Approved: Email {email_id} → {project_code}")
    if patterns_created:
        print(f"   📚 Created {len(patterns_created)} patterns")

    return {'success': True, 'patterns_created': len(patterns_created)}


def correct_suggestion(suggestion_id: int, correct_code: str) -> Dict:
    """
    Correct a suggestion to a different project.

    Args:
        suggestion_id: The suggestion to correct
        correct_code: The correct project code

    Returns:
        Result dict
    """
    helper = get_cli_helper()
    conn = helper._get_connection()
    cursor = conn.cursor()

    # Get suggestion details
    cursor.execute("""
        SELECT s.*, e.sender_email
        FROM ai_suggestions s
        JOIN emails e ON s.source_id = e.email_id
        WHERE s.suggestion_id = ?
    """, (suggestion_id,))
    suggestion = cursor.fetchone()

    if not suggestion:
        conn.close()
        return {'success': False, 'error': 'Suggestion not found'}

    suggestion = dict(suggestion)
    suggested_data = json.loads(suggestion.get('suggested_data', '{}'))
    email_id = suggestion['source_id']
    wrong_code = suggested_data.get('project_code')

    # Find correct proposal
    cursor.execute("""
        SELECT proposal_id, project_name FROM proposals WHERE project_code = ?
    """, (correct_code,))
    correct_proposal = cursor.fetchone()

    if not correct_proposal:
        conn.close()
        return {'success': False, 'error': f'Proposal {correct_code} not found'}

    # Apply correct link
    cursor.execute("""
        INSERT OR IGNORE INTO email_proposal_links
        (email_id, proposal_id, confidence_score, match_method, created_at)
        VALUES (?, ?, 0.95, 'corrected', datetime('now'))
    """, (email_id, correct_proposal['proposal_id']))

    # Update suggestion status
    cursor.execute("""
        UPDATE ai_suggestions
        SET status = 'corrected',
            review_notes = ?,
            reviewed_at = datetime('now')
        WHERE suggestion_id = ?
    """, (f"Corrected: {wrong_code} → {correct_code}", suggestion_id))

    conn.commit()
    conn.close()

    # Learn from correction
    created, penalized = helper.learn_from_correction(
        email_id=email_id,
        wrong_code=wrong_code,
        correct_code=correct_code,
        correct_proposal_id=correct_proposal['proposal_id']
    )

    print(f"✅ Corrected: Email {email_id}")
    print(f"   ❌ Wrong: {wrong_code}")
    print(f"   ✓ Correct: {correct_code} ({correct_proposal['project_name']})")
    print(f"   📚 Created {len(created)} patterns, penalized {penalized}")

    return {'success': True, 'patterns_created': len(created), 'patterns_penalized': penalized}


if __name__ == '__main__':
    """Test the CLI review helper."""
    helper = CLIReviewHelper()

    print("📊 Learning Pattern Summary")
    print("=" * 60)

    summary = helper.get_learning_summary()
    print(f"\nTotal Patterns: {summary['total_patterns']}")

    print("\nBy Type:")
    for ptype, info in summary['by_type'].items():
        print(f"  {ptype}: {info['count']} (avg conf: {info['avg_conf']})")

    print("\nTop Projects:")
    for proj in summary['top_projects']:
        print(f"  {proj['code']}: {proj['patterns']} patterns - {proj['name']}")
