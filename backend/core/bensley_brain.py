#!/usr/bin/env python3
"""
Bensley Brain - Unified Context & Intelligence Layer

The central nervous system that connects all services:
- Provides unified context for any entity (project, proposal, contact, email)
- Shares learned patterns across all processors
- Maintains consistency in entity recognition
- Feeds intelligence back into all services

USAGE:
    from backend.core.bensley_brain import BensleyBrain

    brain = BensleyBrain()
    context = brain.get_full_context("24001")  # Get everything about a project
    brain.process_email(email_id)  # Process with full context
"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache


# =============================================================================
# CONFIGURATION - Single source of truth for all paths
# =============================================================================

def get_db_path() -> str:
    """Get database path from environment or default to OneDrive location"""
    return os.getenv(
        'DATABASE_PATH',
        'database/bensley_master.db'
    )

def get_project_root() -> Path:
    """Get project root directory"""
    # Walk up from this file to find the root (contains database/ folder)
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "database").exists():
            return parent
    return Path.cwd()

# Export for other modules
DB_PATH = get_db_path()
PROJECT_ROOT = get_project_root()


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ProjectContext:
    """Complete context for a project/proposal"""
    project_code: str
    project_title: str
    is_active: bool
    status: str
    client_name: Optional[str]
    total_fee: Optional[float]

    # Related entities
    contacts: List[Dict]
    emails: List[Dict]
    invoices: List[Dict]
    phases: List[Dict]
    milestones: List[Dict]
    meetings: List[Dict]
    rfis: List[Dict]

    # Learned patterns
    common_senders: List[str]
    key_topics: List[str]

    # Timeline
    first_contact: Optional[datetime]
    last_activity: Optional[datetime]
    days_since_contact: int


@dataclass
class ContactContext:
    """Complete context for a contact"""
    contact_id: int
    name: str
    email: str
    company: Optional[str]
    role: Optional[str]

    # Related projects
    projects: List[str]
    proposals: List[str]

    # Communication history
    total_emails: int
    last_email_date: Optional[datetime]
    email_sentiment_avg: Optional[float]


@dataclass
class EmailContext:
    """Context for processing an email"""
    email_id: int
    sender_email: str
    sender_name: Optional[str]
    subject: str

    # Matched entities
    matched_project: Optional[str]
    matched_contact: Optional[int]
    confidence: float

    # Related context
    sender_history: List[Dict]
    thread_context: List[Dict]
    mentioned_projects: List[str]


# =============================================================================
# BENSLEY BRAIN - Main Class
# =============================================================================

class BensleyBrain:
    """
    Central intelligence layer that connects all Bensley services.

    Key responsibilities:
    1. Provide unified context for any entity
    2. Share learned patterns across processors
    3. Maintain entity recognition consistency
    4. Feed intelligence back into services
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or get_db_path()
        self._ensure_db_exists()

        # Cache for frequently accessed data
        self._project_cache = {}
        self._contact_cache = {}
        self._pattern_cache = {}

        # Load learned patterns on init
        self._load_patterns()

    def _ensure_db_exists(self):
        """Verify database exists"""
        db_file = Path(self.db_path)
        if not db_file.is_absolute():
            db_file = PROJECT_ROOT / self.db_path
        if not db_file.exists():
            raise FileNotFoundError(f"Database not found: {db_file}")
        self.db_path = str(db_file)

    def _get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # PATTERN LEARNING
    # =========================================================================

    def _load_patterns(self):
        """Load learned patterns from database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Load project-email sender patterns
            try:
                cursor.execute("""
                    SELECT project_code, sender_email, COUNT(*) as count
                    FROM emails e
                    JOIN email_project_links epl ON e.email_id = epl.email_id
                    GROUP BY project_code, sender_email
                    HAVING count > 2
                    ORDER BY count DESC
                """)

                self._pattern_cache['project_senders'] = {}
                for row in cursor.fetchall():
                    code = row['project_code']
                    if code not in self._pattern_cache['project_senders']:
                        self._pattern_cache['project_senders'][code] = []
                    self._pattern_cache['project_senders'][code].append({
                        'email': row['sender_email'],
                        'count': row['count']
                    })
            except sqlite3.OperationalError:
                self._pattern_cache['project_senders'] = {}

            # Load contact-company patterns
            try:
                cursor.execute("""
                    SELECT company, COUNT(*) as count,
                           GROUP_CONCAT(DISTINCT email) as emails
                    FROM contacts
                    WHERE company IS NOT NULL
                    GROUP BY company
                    HAVING count > 1
                """)

                self._pattern_cache['company_contacts'] = {}
                for row in cursor.fetchall():
                    self._pattern_cache['company_contacts'][row['company']] = {
                        'count': row['count'],
                        'emails': row['emails'].split(',') if row['emails'] else []
                    }
            except sqlite3.OperationalError:
                self._pattern_cache['company_contacts'] = {}

    # =========================================================================
    # PROJECT CONTEXT
    # =========================================================================

    def get_project_context(self, project_code: str) -> Optional[ProjectContext]:
        """
        Get complete context for a project/proposal.
        Pulls from: projects, proposals, contacts, emails, invoices, phases, etc.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get base project info
            cursor.execute("""
                SELECT
                    p.project_code,
                    p.project_title,
                    p.is_active_project,
                    p.status,
                    c.company_name as client_name,
                    p.total_fee_usd,
                    p.country,
                    p.city
                FROM projects p
                LEFT JOIN clients c ON p.client_id = c.client_id
                WHERE p.project_code = ?
            """, (project_code,))

            project = cursor.fetchone()
            if not project:
                # Try proposals table
                cursor.execute("""
                    SELECT
                        project_code,
                        project_name as project_title,
                        0 as is_active_project,
                        status,
                        client_company as client_name,
                        project_value as total_fee_usd,
                        country,
                        NULL as city
                    FROM proposals
                    WHERE project_code = ?
                """, (project_code,))
                project = cursor.fetchone()

            if not project:
                return None

            # Get contacts - try multiple methods
            contacts = []
            try:
                # Method 1: Through email_project_links and sender emails
                cursor.execute("""
                    SELECT DISTINCT c.*
                    FROM contacts c
                    JOIN emails e ON c.email = e.sender_email
                    JOIN email_project_links epl ON e.email_id = epl.email_id
                    WHERE epl.project_code = ?
                    LIMIT 20
                """, (project_code,))
                contacts = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass

            if not contacts:
                try:
                    # Method 2: Through proposal contacts
                    cursor.execute("""
                        SELECT c.*
                        FROM contacts c
                        JOIN project_contact_links pcl ON c.contact_id = pcl.contact_id
                        JOIN proposals p ON pcl.proposal_id = p.proposal_id
                        WHERE p.project_code = ?
                    """, (project_code,))
                    contacts = [dict(row) for row in cursor.fetchall()]
                except sqlite3.OperationalError:
                    pass

            # Get recent emails
            emails = []
            try:
                cursor.execute("""
                    SELECT e.email_id, e.subject, e.sender_email, e.sender_name,
                           e.date, e.category, e.snippet
                    FROM emails e
                    JOIN email_project_links epl ON e.email_id = epl.email_id
                    WHERE epl.project_code = ?
                    ORDER BY e.date DESC
                    LIMIT 50
                """, (project_code,))
                emails = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass

            # Get invoices (uses project_id, need to get it first)
            invoices = []
            try:
                # First get project_id
                cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
                proj_row = cursor.fetchone()
                if proj_row:
                    cursor.execute("""
                        SELECT *
                        FROM invoices
                        WHERE project_id = ?
                        ORDER BY invoice_date DESC
                    """, (proj_row['project_id'],))
                    invoices = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass

            # Get phases/fee breakdown
            phases = []
            try:
                cursor.execute("""
                    SELECT *
                    FROM project_fee_breakdown
                    WHERE project_code = ?
                """, (project_code,))
                phases = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass

            # Get milestones
            milestones = []
            try:
                cursor.execute("""
                    SELECT *
                    FROM project_milestones
                    WHERE project_code = ?
                    ORDER BY planned_date
                """, (project_code,))
                milestones = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass

            # Get meetings
            meetings = []
            try:
                cursor.execute("""
                    SELECT *
                    FROM meetings
                    WHERE project_code = ?
                    ORDER BY meeting_date DESC
                """, (project_code,))
                meetings = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass

            # Get RFIs
            rfis = []
            try:
                cursor.execute("""
                    SELECT *
                    FROM rfis
                    WHERE project_code = ?
                    ORDER BY created_at DESC
                """, (project_code,))
                rfis = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass

            # Calculate timeline
            first_contact = None
            last_activity = None
            if emails:
                dates = [e.get('date') for e in emails if e.get('date')]
                if dates:
                    first_contact = min(dates)
                    last_activity = max(dates)

            # Get common senders from patterns
            common_senders = []
            if project_code in self._pattern_cache.get('project_senders', {}):
                common_senders = [
                    p['email'] for p in
                    self._pattern_cache['project_senders'][project_code][:5]
                ]

            # Extract key topics from email subjects
            key_topics = self._extract_topics([e.get('subject', '') for e in emails])

            days_since = 0
            if last_activity:
                try:
                    last_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    days_since = (datetime.now(last_dt.tzinfo) - last_dt).days
                except:
                    pass

            return ProjectContext(
                project_code=project['project_code'],
                project_title=project['project_title'],
                is_active=bool(project['is_active_project']),
                status=project['status'] or 'unknown',
                client_name=project['client_name'],
                total_fee=project['total_fee_usd'],
                contacts=contacts,
                emails=emails,
                invoices=invoices,
                phases=phases,
                milestones=milestones,
                meetings=meetings,
                rfis=rfis,
                common_senders=common_senders,
                key_topics=key_topics,
                first_contact=first_contact,
                last_activity=last_activity,
                days_since_contact=days_since
            )

    def _extract_topics(self, subjects: List[str]) -> List[str]:
        """Extract common topics from email subjects"""
        # Simple word frequency approach
        word_counts = {}
        stop_words = {'re', 'fwd', 'fw', 'the', 'a', 'an', 'and', 'or', 'to', 'from', 'for'}

        for subject in subjects:
            if not subject:
                continue
            words = subject.lower().split()
            for word in words:
                word = ''.join(c for c in word if c.isalnum())
                if word and len(word) > 2 and word not in stop_words:
                    word_counts[word] = word_counts.get(word, 0) + 1

        # Return top 10 words
        sorted_words = sorted(word_counts.items(), key=lambda x: -x[1])
        return [w[0] for w in sorted_words[:10]]

    # =========================================================================
    # CONTACT CONTEXT
    # =========================================================================

    def get_contact_context(self, contact_id: int = None, email: str = None) -> Optional[ContactContext]:
        """Get complete context for a contact by ID or email"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if contact_id:
                cursor.execute("SELECT * FROM contacts WHERE contact_id = ?", (contact_id,))
            elif email:
                cursor.execute("SELECT * FROM contacts WHERE email = ?", (email,))
            else:
                return None

            contact = cursor.fetchone()
            if not contact:
                return None

            contact = dict(contact)

            # Get linked projects
            cursor.execute("""
                SELECT DISTINCT pcl.project_code, p.is_active_project
                FROM project_contact_links pcl
                LEFT JOIN projects p ON pcl.project_code = p.project_code
                WHERE pcl.contact_id = ?
            """, (contact['contact_id'],))

            projects = []
            proposals = []
            for row in cursor.fetchall():
                if row['is_active_project']:
                    projects.append(row['project_code'])
                else:
                    proposals.append(row['project_code'])

            # Get email stats
            cursor.execute("""
                SELECT COUNT(*) as count, MAX(date) as last_date,
                       AVG(CASE
                           WHEN ec.sentiment = 'positive' THEN 1
                           WHEN ec.sentiment = 'negative' THEN -1
                           ELSE 0
                       END) as avg_sentiment
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE e.sender_email = ?
            """, (contact['email'],))

            stats = cursor.fetchone()

            return ContactContext(
                contact_id=contact['contact_id'],
                name=contact.get('name') or contact.get('full_name', ''),
                email=contact['email'],
                company=contact.get('company'),
                role=contact.get('role') or contact.get('title'),
                projects=projects,
                proposals=proposals,
                total_emails=stats['count'] if stats else 0,
                last_email_date=stats['last_date'] if stats else None,
                email_sentiment_avg=stats['avg_sentiment'] if stats else None
            )

    # =========================================================================
    # EMAIL CONTEXT (for processing)
    # =========================================================================

    def get_email_context(self, email_id: int) -> Optional[EmailContext]:
        """Get context for processing an email"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get email
            cursor.execute("""
                SELECT e.*, epl.project_code, epl.confidence
                FROM emails e
                LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE e.email_id = ?
            """, (email_id,))

            email = cursor.fetchone()
            if not email:
                return None

            email = dict(email)

            # Get sender history
            cursor.execute("""
                SELECT e.email_id, e.subject, e.date, epl.project_code
                FROM emails e
                LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE e.sender_email = ?
                ORDER BY e.date DESC
                LIMIT 20
            """, (email['sender_email'],))
            sender_history = [dict(row) for row in cursor.fetchall()]

            # Get thread context (by thread_id or subject matching)
            thread_context = []
            if email.get('thread_id'):
                cursor.execute("""
                    SELECT e.email_id, e.subject, e.date, e.sender_name, e.snippet
                    FROM emails e
                    WHERE e.thread_id = ?
                    ORDER BY e.date
                """, (email['thread_id'],))
                thread_context = [dict(row) for row in cursor.fetchall()]

            # Find mentioned projects (look for project codes in subject/body)
            mentioned = self._find_mentioned_projects(
                email.get('subject', ''),
                cursor
            )

            # Get matched contact
            cursor.execute("""
                SELECT contact_id FROM contacts WHERE email = ?
            """, (email['sender_email'],))
            contact_row = cursor.fetchone()

            return EmailContext(
                email_id=email['email_id'],
                sender_email=email['sender_email'],
                sender_name=email.get('sender_name'),
                subject=email.get('subject', ''),
                matched_project=email.get('project_code'),
                matched_contact=contact_row['contact_id'] if contact_row else None,
                confidence=email.get('confidence', 0.0),
                sender_history=sender_history,
                thread_context=thread_context,
                mentioned_projects=mentioned
            )

    def _find_mentioned_projects(self, text: str, cursor) -> List[str]:
        """Find project codes mentioned in text"""
        import re

        # Pattern: BK-XXX or variations
        matches = re.findall(r'\b(BK[-_]?\d{3,4})\b', text, re.IGNORECASE)

        # Validate against actual projects
        valid = []
        for match in matches:
            normalized = match.upper().replace('_', '-')
            if '-' not in normalized:
                normalized = f"BK-{normalized[2:]}"

            cursor.execute(
                "SELECT project_code FROM projects WHERE project_code = ?",
                (normalized,)
            )
            if cursor.fetchone():
                valid.append(normalized)

        return list(set(valid))

    # =========================================================================
    # INTELLIGENT EMAIL MATCHING
    # =========================================================================

    def match_email_to_project(self, email_id: int) -> Tuple[Optional[str], float]:
        """
        Intelligently match an email to a project using all available context.
        Returns (project_code, confidence)
        """
        context = self.get_email_context(email_id)
        if not context:
            return None, 0.0

        scores = {}

        # 1. Direct mention in subject (highest weight)
        for project in context.mentioned_projects:
            scores[project] = scores.get(project, 0) + 0.5

        # 2. Sender history (which projects has this sender emailed about?)
        for hist in context.sender_history:
            if hist.get('project_code'):
                scores[hist['project_code']] = scores.get(hist['project_code'], 0) + 0.1

        # 3. Thread context (what project is the thread about?)
        for thread_email in context.thread_context:
            # Would need to look up project links for thread emails
            pass

        # 4. Sender patterns (learned associations)
        sender = context.sender_email
        for project_code, senders in self._pattern_cache.get('project_senders', {}).items():
            sender_emails = [s['email'] for s in senders]
            if sender in sender_emails:
                scores[project_code] = scores.get(project_code, 0) + 0.2

        # 5. Contact links (is sender a known contact for a project?)
        if context.matched_contact:
            contact_context = self.get_contact_context(context.matched_contact)
            if contact_context:
                for proj in contact_context.projects + contact_context.proposals:
                    scores[proj] = scores.get(proj, 0) + 0.3

        if not scores:
            return None, 0.0

        # Get best match
        best = max(scores.items(), key=lambda x: x[1])
        confidence = min(best[1], 1.0)

        return best[0], confidence

    # =========================================================================
    # UNIFIED SEARCH
    # =========================================================================

    def search(self, query: str, limit: int = 20) -> Dict[str, List[Dict]]:
        """
        Search across all entities: projects, contacts, emails.
        Returns grouped results.
        """
        results = {
            'projects': [],
            'contacts': [],
            'emails': []
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            query_lower = f"%{query.lower()}%"

            # Search projects
            cursor.execute("""
                SELECT project_code, project_title, client_name, status,
                       is_active_project
                FROM projects
                WHERE project_code LIKE ? OR project_title LIKE ?
                   OR client_name LIKE ?
                LIMIT ?
            """, (query_lower, query_lower, query_lower, limit))
            results['projects'] = [dict(row) for row in cursor.fetchall()]

            # Search contacts
            cursor.execute("""
                SELECT contact_id, name, email, company, role
                FROM contacts
                WHERE name LIKE ? OR email LIKE ? OR company LIKE ?
                LIMIT ?
            """, (query_lower, query_lower, query_lower, limit))
            results['contacts'] = [dict(row) for row in cursor.fetchall()]

            # Search emails (using FTS if available)
            try:
                cursor.execute("""
                    SELECT email_id, subject, sender_email, date, snippet
                    FROM emails
                    WHERE subject LIKE ? OR snippet LIKE ?
                    ORDER BY date DESC
                    LIMIT ?
                """, (query_lower, query_lower, limit))
                results['emails'] = [dict(row) for row in cursor.fetchall()]
            except:
                pass

        return results

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_brain_stats(self) -> Dict[str, Any]:
        """Get statistics about the brain's knowledge"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Count entities
            for table in ['projects', 'proposals', 'contacts', 'emails', 'invoices']:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f'{table}_count'] = cursor.fetchone()[0]
                except:
                    stats[f'{table}_count'] = 0

            # Pattern stats
            stats['learned_project_patterns'] = len(
                self._pattern_cache.get('project_senders', {})
            )
            stats['learned_company_patterns'] = len(
                self._pattern_cache.get('company_contacts', {})
            )

            # Email linking stats - check BOTH link tables (using subqueries to avoid JOIN duplicates)
            cursor.execute("SELECT COUNT(*) FROM emails")
            stats['emails_total'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT email_id) FROM email_project_links")
            stats['emails_linked_to_projects'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT email_id) FROM email_proposal_links")
            stats['emails_linked_to_proposals'] = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM emails
                WHERE email_id IN (SELECT email_id FROM email_project_links)
                   OR email_id IN (SELECT email_id FROM email_proposal_links)
            """)
            stats['emails_linked'] = cursor.fetchone()[0]
            stats['emails_unlinked'] = stats['emails_total'] - stats['emails_linked']

            return stats


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_brain_instance = None

def get_brain() -> BensleyBrain:
    """Get singleton brain instance"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = BensleyBrain()
    return _brain_instance


def get_project_context(project_code: str) -> Optional[ProjectContext]:
    """Convenience function to get project context"""
    return get_brain().get_project_context(project_code)


def get_contact_context(contact_id: int = None, email: str = None) -> Optional[ContactContext]:
    """Convenience function to get contact context"""
    return get_brain().get_contact_context(contact_id, email)


def match_email(email_id: int) -> Tuple[Optional[str], float]:
    """Convenience function to match an email"""
    return get_brain().match_email_to_project(email_id)


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import sys

    brain = BensleyBrain()

    print("=" * 60)
    print("BENSLEY BRAIN - Intelligence Status")
    print("=" * 60)

    stats = brain.get_brain_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print()

    if len(sys.argv) > 1:
        code = sys.argv[1]
        print(f"Getting context for: {code}")
        print("-" * 40)

        ctx = brain.get_project_context(code)
        if ctx:
            print(f"Project: {ctx.project_title}")
            print(f"Status: {ctx.status}")
            print(f"Active: {ctx.is_active}")
            print(f"Contacts: {len(ctx.contacts)}")
            print(f"Emails: {len(ctx.emails)}")
            print(f"Invoices: {len(ctx.invoices)}")
            print(f"Key topics: {', '.join(ctx.key_topics[:5])}")
            print(f"Common senders: {', '.join(ctx.common_senders[:3])}")
        else:
            print("Project not found")
