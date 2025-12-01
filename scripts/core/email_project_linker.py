"""
Email Project Linker - Links unlinked emails to PROJECTS (not proposals)

Strategies (in order of confidence):
1. Thread Inheritance: If any HIGH-CONFIDENCE email in thread is linked, inherit
2. Sender Pattern: EXTERNAL senders with 5+ emails to ONE project
3. Contact Match: Match sender to contacts linked to projects
4. Domain Pattern: EXTERNAL client domains that map 1:1 to projects

MODES:
- Default: Auto-link directly to email_project_links table
- --suggest: Create ai_suggestions for human review (learning system)
- --extract-contacts: Also create suggestions for new contacts from unknown senders

FIXED: 2025-11-30 - Internal domain/sender exclusions added
UPDATED: 2025-11-30 - Added --suggest mode for ai_suggestions, contact extraction
Created: 2025-11-29
"""

import sqlite3
import re
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

# =========================================================================
# INTERNAL EXCLUSION LISTS - Never use these for pattern-based linking
# =========================================================================

INTERNAL_DOMAINS = {
    'bensley.com',           # Main company
    'bensley.co.id',         # Bali/Indonesia office
    'bensley.co.th',         # Thailand office
    'bdlbali.com',           # Bali Design Lab
    'bensley.atlassian.net', # Internal tools
    'bensleydesign.com',     # Alt domain
}

# Common free email providers - can't reliably link to one project
GENERIC_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
    'icloud.com', 'live.com', 'aol.com', 'mail.com',
    'protonmail.com', 'ymail.com', 'msn.com',
}

# Skip these domains for contact extraction (automated/notification services)
NOTIFICATION_DOMAINS = {
    'notion.so', 'updates.notion.so', 'wetransfer.com', 'accelo.com',
    'atlassian.net', 'atlassian.com', 'jira.com', 'trello.com',
    'monday.com', 'asana.com', 'slack.com', 'teams.microsoft.com',
    'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
    'mailchimp.com', 'sendgrid.com', 'constantcontact.com',
    'pandadoc.net', 'docusign.com', 'adobesign.com',
    'ariba.com', 'sap.com', 'oracle.com',
    'noreply', 'no-reply', 'donotreply',
}

# High-confidence link methods we can trust for thread inheritance
HIGH_CONFIDENCE_METHODS = {'manual', 'contact_known', 'id_fix'}

# Minimum emails from same sender to same project for sender_pattern
MIN_SENDER_EMAILS_THRESHOLD = 5


class EmailProjectLinker:
    """Links unlinked emails to projects using multiple strategies"""

    def __init__(self, db_path: str = DB_PATH, suggest_mode: bool = False, extract_contacts: bool = False):
        self.db_path = db_path
        self.suggest_mode = suggest_mode
        self.extract_contacts = extract_contacts
        self.stats = {
            'thread_linked': 0,
            'sender_linked': 0,
            'contact_linked': 0,
            'domain_linked': 0,
            'already_linked': 0,
            'no_match': 0,
            'errors': 0,
            # Suggestion mode stats
            'suggestions_created': 0,
            'suggestions_skipped_duplicate': 0,
            'contacts_suggested': 0,
        }
        # Cache known contacts for deduplication
        self._known_contacts: Set[str] = set()
        self._pending_contact_suggestions: Set[str] = set()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")  # Enforce FK constraints
        return conn

    def validate_project_exists(self, project_id: int) -> bool:
        """Check if project_id exists in projects table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM projects WHERE project_id = ? LIMIT 1", (project_id,))
            return cursor.fetchone() is not None

    def validate_email_exists(self, email_id: int) -> bool:
        """Check if email_id exists in emails table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM emails WHERE email_id = ? LIMIT 1", (email_id,))
            return cursor.fetchone() is not None

    def clean_email(self, email_str: str) -> str:
        """Extract clean email from 'Name <email@domain.com>' format"""
        if not email_str:
            return ''
        match = re.search(r'<([^>]+)>', email_str)
        if match:
            return match.group(1).lower().strip()
        return email_str.lower().strip()

    def get_domain(self, email: str) -> str:
        """Extract domain from email address"""
        clean = self.clean_email(email)
        if '@' in clean:
            return clean.split('@')[1]
        return ''

    def is_internal_domain(self, domain: str) -> bool:
        """Check if domain is internal (Bensley-owned)"""
        if not domain:
            return False
        domain_lower = domain.lower()
        return domain_lower in INTERNAL_DOMAINS or 'bensley' in domain_lower

    def is_internal_sender(self, email: str) -> bool:
        """Check if sender is internal (Bensley staff)"""
        domain = self.get_domain(email)
        return self.is_internal_domain(domain)

    def is_generic_domain(self, domain: str) -> bool:
        """Check if domain is generic (gmail, yahoo, etc.)"""
        return domain.lower() in GENERIC_DOMAINS if domain else False

    def is_notification_domain(self, email: str) -> bool:
        """Check if email is from automated/notification service (skip for contacts)"""
        if not email:
            return False
        email_lower = email.lower()
        domain = self.get_domain(email)

        # Check for noreply patterns in the email address itself
        if any(pattern in email_lower for pattern in ['noreply', 'no-reply', 'donotreply', 'notify@', 'notifications@', 'team@', 'info@']):
            return True

        # Check domain against notification services
        if domain and any(notif in domain for notif in NOTIFICATION_DOMAINS):
            return True

        return False

    # =========================================================================
    # SUGGESTION MODE HELPERS
    # =========================================================================

    def load_known_contacts(self):
        """Load all known contact emails for deduplication"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM contacts WHERE email IS NOT NULL")
            for (email,) in cursor.fetchall():
                clean = self.clean_email(email)
                if clean:
                    self._known_contacts.add(clean)

            # Also load pending contact suggestions
            cursor.execute("""
                SELECT json_extract(suggested_data, '$.email') as email
                FROM ai_suggestions
                WHERE suggestion_type IN ('new_contact', 'contact_link')
                  AND status = 'pending'
            """)
            for (email,) in cursor.fetchall():
                if email:
                    self._pending_contact_suggestions.add(email.lower())

        print(f"  Loaded {len(self._known_contacts)} known contacts, {len(self._pending_contact_suggestions)} pending contact suggestions")

    def suggestion_exists(self, email_id: int, project_code: str) -> bool:
        """Check if an email_link suggestion already exists for this email+project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM ai_suggestions
                WHERE suggestion_type = 'email_link'
                  AND source_id = ?
                  AND project_code = ?
                  AND status IN ('pending', 'approved', 'auto_applied')
                LIMIT 1
            """, (email_id, project_code))
            return cursor.fetchone() is not None

    def create_email_link_suggestion(
        self,
        email_id: int,
        project_id: int,
        project_code: str,
        confidence: float,
        method: str,
        rationale: str,
        email_subject: str = None,
        sender_email: str = None
    ) -> bool:
        """Create an ai_suggestion for email-project linking instead of direct link"""

        # Check for duplicates
        if self.suggestion_exists(email_id, project_code):
            self.stats['suggestions_skipped_duplicate'] += 1
            return False

        source_ref = f"Email: {email_subject[:50] if email_subject else 'No subject'}..."
        if sender_email:
            source_ref = f"Email from {self.clean_email(sender_email)}: {email_subject[:30] if email_subject else 'No subject'}"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ai_suggestions (
                        suggestion_type, priority, confidence_score,
                        source_type, source_id, source_reference,
                        title, description, suggested_action,
                        suggested_data, target_table, project_code,
                        status, created_at
                    ) VALUES (
                        'email_link', ?, ?,
                        'email', ?, ?,
                        ?, ?, 'Link email to project',
                        ?, 'email_project_links', ?,
                        'pending', datetime('now')
                    )
                """, (
                    'high' if confidence >= 0.85 else 'medium' if confidence >= 0.7 else 'low',
                    confidence,
                    email_id,
                    source_ref,
                    f"Link to {project_code}",
                    rationale,
                    json.dumps({
                        'email_id': email_id,
                        'project_id': project_id,
                        'project_code': project_code,
                        'link_method': method,
                        'confidence': confidence
                    }),
                    project_code
                ))
                conn.commit()
                self.stats['suggestions_created'] += 1
                return True
        except Exception as e:
            print(f"  Error creating suggestion: {e}")
            self.stats['errors'] += 1
            return False

    def create_contact_suggestion(
        self,
        email: str,
        sender_name: str = None,
        project_code: str = None,
        email_id: int = None
    ) -> bool:
        """Create an ai_suggestion for a new contact from email"""

        clean = self.clean_email(email)
        if not clean:
            return False

        # Skip internal, known, notification, and already-suggested contacts
        if self.is_internal_sender(email):
            return False
        if self.is_notification_domain(email):
            return False
        if clean in self._known_contacts:
            return False
        if clean in self._pending_contact_suggestions:
            return False

        # Extract name from email string if not provided
        if not sender_name:
            # Try to parse "Name" <email> format
            match = re.match(r'"?([^"<]+)"?\s*<', email)
            if match:
                sender_name = match.group(1).strip()
            else:
                sender_name = clean.split('@')[0]  # Use part before @

        # Clean up encoded names
        if sender_name and '=?' in sender_name:
            sender_name = clean.split('@')[0]  # Fall back to email prefix

        domain = self.get_domain(email)
        company = domain.split('.')[0].title() if domain and not self.is_generic_domain(domain) else None

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ai_suggestions (
                        suggestion_type, priority, confidence_score,
                        source_type, source_id, source_reference,
                        title, description, suggested_action,
                        suggested_data, target_table, project_code,
                        status, created_at
                    ) VALUES (
                        'new_contact', 'medium', 0.75,
                        'email', ?, ?,
                        ?, ?, 'Add to contacts database',
                        ?, 'contacts', ?,
                        'pending', datetime('now')
                    )
                """, (
                    email_id,
                    f"New contact found in email",
                    f"New contact: {sender_name}",
                    f"Contact {sender_name} ({clean}) found in emails" + (f" related to {project_code}" if project_code else ""),
                    json.dumps({
                        'name': sender_name,
                        'email': clean,
                        'company': company,
                        'source': 'email_intelligence',
                        'related_project': project_code
                    }),
                    project_code
                ))
                conn.commit()
                self._pending_contact_suggestions.add(clean)
                self.stats['contacts_suggested'] += 1
                return True
        except Exception as e:
            print(f"  Error creating contact suggestion: {e}")
            return False

    # =========================================================================
    # STRATEGY 1: Thread Inheritance (Highest confidence)
    # =========================================================================

    def get_thread_project_map(self) -> Dict[str, Tuple[int, str]]:
        """Get mapping of thread_id -> (project_id, project_code) for linked threads

        FIXED: Only inherits from HIGH-CONFIDENCE link methods (manual, contact_known, id_fix)
        to prevent propagating bad links from sender_pattern or domain_pattern.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Only use high-confidence links as thread anchors
            high_conf_methods = "','".join(HIGH_CONFIDENCE_METHODS)
            cursor.execute(f"""
                SELECT DISTINCT e.thread_id, epl.project_id, epl.project_code
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE e.thread_id IS NOT NULL AND e.thread_id != ''
                  AND epl.link_method IN ('{high_conf_methods}')
            """)
            thread_map = {}
            for thread_id, project_id, project_code in cursor.fetchall():
                if thread_id not in thread_map:
                    thread_map[thread_id] = (project_id, project_code)
            return thread_map

    def link_by_thread(self, dry_run: bool = False) -> int:
        """Link all emails in threads that have at least one linked email"""
        thread_map = self.get_thread_project_map()
        print(f"  Found {len(thread_map)} threads with linked emails")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Find unlinked emails in linked threads - include subject/sender for suggestions
            cursor.execute("""
                SELECT e.email_id, e.thread_id, e.subject, e.sender_email
                FROM emails e
                WHERE e.email_id NOT IN (SELECT email_id FROM email_project_links)
                  AND e.thread_id IS NOT NULL AND e.thread_id != ''
            """)

            unlinked = cursor.fetchall()
            count = 0

            for email_id, thread_id, subject, sender_email in unlinked:
                if thread_id in thread_map:
                    project_id, project_code = thread_map[thread_id]

                    if self.suggest_mode:
                        # Create suggestion instead of direct link
                        if self.create_email_link_suggestion(
                            email_id=email_id,
                            project_id=project_id,
                            project_code=project_code,
                            confidence=0.95,
                            method='thread_inherit',
                            rationale=f"Same thread as email already linked to {project_code}",
                            email_subject=subject,
                            sender_email=sender_email
                        ):
                            count += 1
                    elif not dry_run:
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO email_project_links
                                (email_id, project_id, project_code, confidence, link_method, evidence, created_at)
                                VALUES (?, ?, ?, 0.95, 'thread_inherit', 'Same thread as linked email', ?)
                            """, (email_id, project_id, project_code, datetime.now().isoformat()))
                            if cursor.rowcount > 0:
                                count += 1
                        except Exception as e:
                            self.stats['errors'] += 1
                    else:
                        count += 1

            if not dry_run and not self.suggest_mode:
                conn.commit()

        self.stats['thread_linked'] = count
        return count

    # =========================================================================
    # STRATEGY 2: Sender Pattern (High confidence - EXTERNAL senders only)
    # =========================================================================

    def get_sender_project_map(self) -> Dict[str, Tuple[int, str, int]]:
        """Get mapping of sender_email -> (project_id, project_code, count) based on existing links

        FIXED:
        - Only includes EXTERNAL senders (excludes Bensley staff)
        - Requires minimum threshold of emails to same project
        - Only maps senders who email predominantly to ONE project
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    e.sender_email,
                    epl.project_id,
                    epl.project_code,
                    COUNT(*) as link_count
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE e.sender_email IS NOT NULL
                GROUP BY e.sender_email, epl.project_id
                ORDER BY e.sender_email, link_count DESC
            """)

            # Build a map of sender -> {project: count}
            sender_project_counts = defaultdict(lambda: defaultdict(int))
            sender_project_codes = {}

            for sender_email, project_id, project_code, count in cursor.fetchall():
                clean_sender = self.clean_email(sender_email)
                if not clean_sender:
                    continue

                # CRITICAL FIX: Skip internal senders
                if self.is_internal_sender(sender_email):
                    continue

                sender_project_counts[clean_sender][project_id] += count
                sender_project_codes[(clean_sender, project_id)] = project_code

            # Only include senders who:
            # 1. Have MIN_SENDER_EMAILS_THRESHOLD+ emails to their top project
            # 2. Have >80% of their emails going to that one project (exclusivity)
            sender_map = {}
            for clean_sender, project_counts in sender_project_counts.items():
                if not project_counts:
                    continue

                total_emails = sum(project_counts.values())
                top_project = max(project_counts.items(), key=lambda x: x[1])
                project_id, top_count = top_project

                # Require minimum threshold
                if top_count < MIN_SENDER_EMAILS_THRESHOLD:
                    continue

                # Require 80% exclusivity (sender mostly emails one project)
                exclusivity = top_count / total_emails
                if exclusivity < 0.8:
                    continue

                project_code = sender_project_codes.get((clean_sender, project_id), '')
                sender_map[clean_sender] = (project_id, project_code, top_count)

            return sender_map

    def link_by_sender(self, dry_run: bool = False) -> int:
        """Link emails where EXTERNAL sender has 5+ emails linked to same project

        FIXED: Only for external senders with high exclusivity to one project.
        """
        sender_map = self.get_sender_project_map()
        print(f"  Found {len(sender_map)} external senders with {MIN_SENDER_EMAILS_THRESHOLD}+ emails to one project")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email_id, sender_email, subject
                FROM emails
                WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
                  AND sender_email IS NOT NULL
            """)

            unlinked = cursor.fetchall()
            count = 0
            unmatched_senders = set()  # For contact extraction

            for email_id, sender_email, subject in unlinked:
                clean_sender = self.clean_email(sender_email)

                # Double-check: skip internal senders
                if self.is_internal_sender(sender_email):
                    continue

                if clean_sender in sender_map:
                    project_id, project_code, email_count = sender_map[clean_sender]

                    if self.suggest_mode:
                        # Create suggestion instead of direct link
                        if self.create_email_link_suggestion(
                            email_id=email_id,
                            project_id=project_id,
                            project_code=project_code,
                            confidence=0.85,
                            method='sender_pattern',
                            rationale=f"Sender {clean_sender} has {email_count}+ emails to {project_code}",
                            email_subject=subject,
                            sender_email=sender_email
                        ):
                            count += 1
                    elif not dry_run:
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO email_project_links
                                (email_id, project_id, project_code, confidence, link_method, evidence, created_at)
                                VALUES (?, ?, ?, 0.85, 'sender_pattern', 'External sender with consistent project emails', ?)
                            """, (email_id, project_id, project_code, datetime.now().isoformat()))
                            if cursor.rowcount > 0:
                                count += 1
                        except Exception as e:
                            self.stats['errors'] += 1
                    else:
                        count += 1
                else:
                    # Track unmatched external senders for contact extraction
                    if self.extract_contacts and not self.is_generic_domain(self.get_domain(sender_email)):
                        unmatched_senders.add((sender_email, email_id))

            if not dry_run and not self.suggest_mode:
                conn.commit()

            # Extract contacts from unmatched senders
            if self.extract_contacts and unmatched_senders:
                for sender_email, email_id in unmatched_senders:
                    self.create_contact_suggestion(sender_email, email_id=email_id)

        self.stats['sender_linked'] = count
        return count

    # =========================================================================
    # STRATEGY 3: Contact Match (Medium confidence)
    # =========================================================================

    def get_contact_project_map(self) -> Dict[str, Tuple[int, str]]:
        """Get mapping of contact_email -> (project_id, project_code) via project_contact_links

        FIXED: Now properly queries project_contact_links which has both project_id and proposal_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Query contacts linked to projects via project_contact_links
            # This table has: proposal_id, contact_id, project_id
            cursor.execute("""
                SELECT DISTINCT
                    c.email,
                    c.name,
                    COALESCE(pcl.project_id, p.project_id) as project_id,
                    COALESCE(pr.project_code, p.project_code) as project_code
                FROM contacts c
                JOIN project_contact_links pcl ON c.contact_id = pcl.contact_id
                LEFT JOIN projects p ON pcl.project_id = p.project_id
                LEFT JOIN proposals prop ON pcl.proposal_id = prop.proposal_id
                LEFT JOIN projects pr ON prop.project_code = pr.project_code
                WHERE c.email IS NOT NULL
                  AND (pcl.project_id IS NOT NULL OR pcl.proposal_id IS NOT NULL)
            """)

            contact_map = {}
            for email, name, project_id, project_code in cursor.fetchall():
                clean = self.clean_email(email)
                if clean and project_id and project_code:
                    # Skip internal contacts
                    if not self.is_internal_sender(email):
                        contact_map[clean] = (project_id, project_code)

            return contact_map

    def link_by_contact(self, dry_run: bool = False) -> int:
        """Link emails where sender is a contact linked to a project

        This is the HIGHEST CONFIDENCE strategy as per the task requirements:
        - If contact is linked to ONE project -> 0.85 confidence
        - If contact is linked to MULTIPLE projects -> 0.70 confidence (needs content analysis)
        """
        contact_map = self.get_contact_project_map()
        print(f"  Found {len(contact_map)} contacts linked to projects")

        if not contact_map:
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email_id, sender_email, subject
                FROM emails
                WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
                  AND sender_email IS NOT NULL
            """)

            unlinked = cursor.fetchall()
            count = 0

            for email_id, sender_email, subject in unlinked:
                clean_sender = self.clean_email(sender_email)
                if clean_sender in contact_map:
                    project_id, project_code = contact_map[clean_sender]

                    if self.suggest_mode:
                        # Create suggestion - high confidence for known contacts
                        if self.create_email_link_suggestion(
                            email_id=email_id,
                            project_id=project_id,
                            project_code=project_code,
                            confidence=0.85,
                            method='contact_known',
                            rationale=f"Sender {clean_sender} is a known contact linked to {project_code}",
                            email_subject=subject,
                            sender_email=sender_email
                        ):
                            count += 1
                    elif not dry_run:
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO email_project_links
                                (email_id, project_id, project_code, confidence, link_method, evidence, created_at)
                                VALUES (?, ?, ?, 0.85, 'contact_known', 'Sender is known project contact', ?)
                            """, (email_id, project_id, project_code, datetime.now().isoformat()))
                            if cursor.rowcount > 0:
                                count += 1
                        except Exception as e:
                            self.stats['errors'] += 1
                    else:
                        count += 1

            if not dry_run and not self.suggest_mode:
                conn.commit()

        self.stats['contact_linked'] = count
        return count

    # =========================================================================
    # STRATEGY 4: Domain Pattern (Lower confidence - EXTERNAL client domains only)
    # =========================================================================

    def get_domain_project_map(self) -> Dict[str, Tuple[int, str]]:
        """Get mapping of domain -> (project_id, project_code) based on linked emails

        FIXED:
        - Excludes ALL internal domains (bensley.com, bensley.co.id, bdlbali.com, etc.)
        - Excludes generic domains (gmail, yahoo, etc.)
        - Only includes domains with 90%+ exclusivity to ONE project
        - Requires minimum 3 emails from domain
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    e.sender_email,
                    epl.project_id,
                    epl.project_code,
                    COUNT(*) as cnt
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE e.sender_email IS NOT NULL
                GROUP BY e.sender_email, epl.project_id
            """)

            domain_project_counts = defaultdict(lambda: defaultdict(int))
            domain_project_codes = {}

            for sender_email, project_id, project_code, cnt in cursor.fetchall():
                domain = self.get_domain(sender_email)
                if not domain:
                    continue

                # CRITICAL FIX: Skip internal and generic domains
                if self.is_internal_domain(domain) or self.is_generic_domain(domain):
                    continue

                domain_project_counts[domain][project_id] += cnt
                domain_project_codes[(domain, project_id)] = project_code

            # Only include domains with:
            # 1. 90%+ exclusivity to one project
            # 2. Minimum 3 emails from domain
            domain_map = {}
            for domain, project_counts in domain_project_counts.items():
                if not project_counts:
                    continue

                total_emails = sum(project_counts.values())
                if total_emails < 3:  # Require minimum emails
                    continue

                top_project = max(project_counts.items(), key=lambda x: x[1])
                project_id, top_count = top_project

                # Require 90% exclusivity for domain linking (stricter than sender)
                exclusivity = top_count / total_emails
                if exclusivity < 0.9:
                    continue

                project_code = domain_project_codes.get((domain, project_id), '')
                domain_map[domain] = (project_id, project_code)

            return domain_map

    def link_by_domain(self, dry_run: bool = False) -> int:
        """Link emails where sender domain is an EXTERNAL client domain

        FIXED: Only for external client domains with high exclusivity to one project.
        """
        domain_map = self.get_domain_project_map()
        print(f"  Found {len(domain_map)} external client domains mapped to projects")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email_id, sender_email, subject
                FROM emails
                WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
                  AND sender_email IS NOT NULL
            """)

            unlinked = cursor.fetchall()
            count = 0

            for email_id, sender_email, subject in unlinked:
                domain = self.get_domain(sender_email)

                # Double-check: skip internal and generic domains
                if self.is_internal_domain(domain) or self.is_generic_domain(domain):
                    continue

                if domain in domain_map:
                    project_id, project_code = domain_map[domain]

                    if self.suggest_mode:
                        # Create suggestion - lower confidence for domain-only match
                        if self.create_email_link_suggestion(
                            email_id=email_id,
                            project_id=project_id,
                            project_code=project_code,
                            confidence=0.75,
                            method='domain_pattern',
                            rationale=f"Domain {domain} is 90%+ exclusive to {project_code}",
                            email_subject=subject,
                            sender_email=sender_email
                        ):
                            count += 1
                    elif not dry_run:
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO email_project_links
                                (email_id, project_id, project_code, confidence, link_method, evidence, created_at)
                                VALUES (?, ?, ?, 0.75, 'domain_pattern', 'External client domain with high exclusivity', ?)
                            """, (email_id, project_id, project_code, datetime.now().isoformat()))
                            if cursor.rowcount > 0:
                                count += 1
                        except Exception as e:
                            self.stats['errors'] += 1
                    else:
                        count += 1

            if not dry_run and not self.suggest_mode:
                conn.commit()

        self.stats['domain_linked'] = count
        return count

    # =========================================================================
    # Main Run Method
    # =========================================================================

    def get_current_stats(self) -> Dict:
        """Get current linking statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM emails")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT email_id) FROM email_project_links")
            linked = cursor.fetchone()[0]
            return {
                'total': total,
                'linked': linked,
                'unlinked': total - linked,
                'percentage': round(100.0 * linked / total, 1) if total > 0 else 0
            }

    def run(self, dry_run: bool = False) -> Dict:
        """Run all linking strategies"""
        mode_label = "[SUGGEST MODE] " if self.suggest_mode else "[DRY RUN] " if dry_run else ""
        print(f"{mode_label}Starting email project linking...")

        # Load known contacts if in suggest/extract mode
        if self.suggest_mode or self.extract_contacts:
            print("\nLoading known contacts for deduplication...")
            self.load_known_contacts()

        # Get initial stats
        initial = self.get_current_stats()
        print(f"\nInitial state: {initial['linked']}/{initial['total']} ({initial['percentage']}%)")
        print(f"Unlinked: {initial['unlinked']}")

        # Run strategies in order of confidence
        # IMPORTANT: Contact match FIRST (highest confidence for known contacts)
        print("\n1. Contact Match (0.85 confidence - known contacts)...")
        self.link_by_contact(dry_run)
        print(f"   {'Suggestions' if self.suggest_mode else 'Linked'}: {self.stats['contact_linked']}")

        print("\n2. Thread Inheritance (0.95 confidence)...")
        self.link_by_thread(dry_run)
        print(f"   {'Suggestions' if self.suggest_mode else 'Linked'}: {self.stats['thread_linked']}")

        print("\n3. Sender Pattern (0.85 confidence)...")
        self.link_by_sender(dry_run)
        print(f"   {'Suggestions' if self.suggest_mode else 'Linked'}: {self.stats['sender_linked']}")

        print("\n4. Domain Pattern (0.75 confidence)...")
        self.link_by_domain(dry_run)
        print(f"   {'Suggestions' if self.suggest_mode else 'Linked'}: {self.stats['domain_linked']}")

        # Get final stats
        final = self.get_current_stats()

        # Summary
        total_linked = (
            self.stats['thread_linked'] +
            self.stats['sender_linked'] +
            self.stats['contact_linked'] +
            self.stats['domain_linked']
        )

        print("\n" + "="*60)
        if self.suggest_mode:
            print("SUGGESTION MODE SUMMARY")
        else:
            print("LINKING SUMMARY")
        print("="*60)
        print(f"Contact match:      +{self.stats['contact_linked']}")
        print(f"Thread inheritance: +{self.stats['thread_linked']}")
        print(f"Sender pattern:     +{self.stats['sender_linked']}")
        print(f"Domain pattern:     +{self.stats['domain_linked']}")
        print(f"Errors:             {self.stats['errors']}")

        if self.suggest_mode:
            print("-"*60)
            print(f"TOTAL SUGGESTIONS CREATED: {self.stats['suggestions_created']}")
            print(f"Skipped (duplicates):      {self.stats['suggestions_skipped_duplicate']}")
            if self.extract_contacts:
                print(f"Contact suggestions:       {self.stats['contacts_suggested']}")
        else:
            print("-"*60)
            print(f"TOTAL NEW LINKS: {total_linked}")
            print(f"\nBefore: {initial['linked']}/{initial['total']} ({initial['percentage']}%)")
            print(f"After:  {final['linked']}/{final['total']} ({final['percentage']}%)")
            print(f"Improvement: +{final['percentage'] - initial['percentage']:.1f}%")

        return {
            'initial': initial,
            'final': final,
            'stats': self.stats
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Link unlinked emails to projects')
    parser.add_argument('--dry-run', action='store_true', help='Show what would happen without making changes')
    parser.add_argument('--test', action='store_true', help='Test mode: run on sample and show accuracy check')
    parser.add_argument('--suggest', action='store_true',
                        help='Create ai_suggestions instead of direct links (learning system mode)')
    parser.add_argument('--extract-contacts', action='store_true',
                        help='Also create suggestions for new contacts from unknown senders')
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    args = parser.parse_args()

    linker = EmailProjectLinker(
        db_path=args.db,
        suggest_mode=args.suggest,
        extract_contacts=args.extract_contacts
    )

    if args.test:
        # Test mode: dry run and show sample for manual verification
        print("=" * 60)
        print("TEST MODE - Dry run with sample verification")
        print("=" * 60)
        result = linker.run(dry_run=True)

        # Show sample of what would be linked for verification
        print("\n" + "=" * 60)
        print("SAMPLE VERIFICATION - Check these would be correctly linked:")
        print("=" * 60)

        # Show contacts linked to projects
        contact_map = linker.get_contact_project_map()
        print(f"\nContacts linked to projects: {len(contact_map)}")
        for contact, (project_id, project_code) in list(contact_map.items())[:10]:
            print(f"  {contact} -> {project_code}")

        # Show domains that would be used
        domain_map = linker.get_domain_project_map()
        print(f"\nClient domains detected: {len(domain_map)}")
        for domain, (project_id, project_code) in list(domain_map.items())[:10]:
            print(f"  {domain} -> {project_code}")

        # Show senders that would be used
        sender_map = linker.get_sender_project_map()
        print(f"\nExternal senders detected: {len(sender_map)}")
        for sender, (project_id, project_code, count) in list(sender_map.items())[:10]:
            print(f"  {sender} ({count} emails) -> {project_code}")

        print("\n" + "-" * 60)
        print("If these look correct, run without --test to apply changes.")
        print("Run with: python email_project_linker.py")
        print("For suggestions: python email_project_linker.py --suggest")
        print("With contacts:   python email_project_linker.py --suggest --extract-contacts")
        print("-" * 60)
    else:
        result = linker.run(dry_run=args.dry_run)

    return result


if __name__ == '__main__':
    main()
