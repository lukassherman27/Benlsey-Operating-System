"""
Contact-Project Linker - Creates suggestions to link contacts to projects/proposals

IMPORTANT: This script creates AI suggestions for human review.
It analyzes email_project_links and email_proposal_links to discover
which contacts should be linked to which projects/proposals.

The intelligence loop:
1. Email → Project/Proposal (via email links)
2. Email → Contact (via sender_email → contacts.email)
3. Contact → Project/Proposal (suggested by this script)

Once approved, these links enable:
- Auto-categorization of future emails
- Contact-based project context
- Richer proposal intelligence

Created: 2025-12-01
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict

# Default database path
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


class ContactProjectLinker:
    """Creates suggestions to link contacts to projects/proposals"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.stats = {
            'project_links_found': 0,
            'proposal_links_found': 0,
            'already_linked': 0,
            'already_suggested': 0,
            'suggestions_created': 0,
            'new_contacts_suggested': 0,
            'errors': 0
        }

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_contact_project_links_from_emails(self) -> List[Dict]:
        """
        Find contact-project pairs from email_project_links.

        For each email linked to a project, extract the sender's contact.
        Group by (contact_id, project_id) with email counts.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.contact_id,
                    c.email as contact_email,
                    c.name as contact_name,
                    p.project_id,
                    p.project_code,
                    p.project_title as project_name,
                    COUNT(DISTINCT e.email_id) as email_count,
                    MIN(e.date) as first_email,
                    MAX(e.date) as last_email
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                JOIN projects p ON epl.project_code = p.project_code
                JOIN contacts c ON LOWER(e.sender_email) = LOWER(c.email)
                WHERE e.sender_email NOT LIKE '%bensley%'
                  AND e.sender_email IS NOT NULL
                GROUP BY c.contact_id, p.project_id
                ORDER BY email_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_contact_proposal_links_from_emails(self) -> List[Dict]:
        """
        Find contact-proposal pairs from email_proposal_links.

        For each email linked to a proposal, extract the sender's contact.
        Group by (contact_id, proposal_id) with email counts.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.contact_id,
                    c.email as contact_email,
                    c.name as contact_name,
                    pr.proposal_id,
                    pr.project_code,
                    pr.project_name,
                    COUNT(DISTINCT e.email_id) as email_count,
                    MIN(e.date) as first_email,
                    MAX(e.date) as last_email
                FROM emails e
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                JOIN proposals pr ON epl.proposal_id = pr.proposal_id
                JOIN contacts c ON LOWER(e.sender_email) = LOWER(c.email)
                WHERE e.sender_email NOT LIKE '%bensley%'
                  AND e.sender_email IS NOT NULL
                GROUP BY c.contact_id, pr.proposal_id
                ORDER BY email_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_unknown_senders(self) -> List[Dict]:
        """
        Find email senders from linked emails who don't have contact records.
        These will generate new_contact suggestions.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # From project-linked emails
            cursor.execute("""
                SELECT
                    e.sender_email,
                    e.sender_name,
                    epl.project_code,
                    p.project_id,
                    NULL as proposal_id,
                    COUNT(DISTINCT e.email_id) as email_count
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                JOIN projects p ON epl.project_code = p.project_code
                WHERE e.sender_email NOT LIKE '%bensley%'
                  AND e.sender_email IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM contacts c
                      WHERE LOWER(c.email) = LOWER(e.sender_email)
                  )
                GROUP BY e.sender_email, epl.project_code

                UNION ALL

                SELECT
                    e.sender_email,
                    e.sender_name,
                    pr.project_code,
                    NULL as project_id,
                    pr.proposal_id,
                    COUNT(DISTINCT e.email_id) as email_count
                FROM emails e
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                JOIN proposals pr ON epl.proposal_id = pr.proposal_id
                WHERE e.sender_email NOT LIKE '%bensley%'
                  AND e.sender_email IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM contacts c
                      WHERE LOWER(c.email) = LOWER(e.sender_email)
                  )
                GROUP BY e.sender_email, pr.proposal_id

                ORDER BY email_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def is_already_linked(
        self,
        contact_id: int,
        project_id: int = None,
        proposal_id: int = None
    ) -> bool:
        """Check if contact is already linked to project/proposal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("""
                    SELECT 1 FROM project_contact_links
                    WHERE contact_id = ? AND project_id = ?
                """, (contact_id, project_id))
            elif proposal_id:
                cursor.execute("""
                    SELECT 1 FROM project_contact_links
                    WHERE contact_id = ? AND proposal_id = ?
                """, (contact_id, proposal_id))
            else:
                return False
            return cursor.fetchone() is not None

    def suggestion_exists(
        self,
        contact_id: int,
        project_id: int = None,
        proposal_id: int = None
    ) -> bool:
        """Check if a pending suggestion already exists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("""
                    SELECT 1 FROM ai_suggestions
                    WHERE suggestion_type = 'contact_link'
                      AND status = 'pending'
                      AND json_extract(suggested_data, '$.contact_id') = ?
                      AND json_extract(suggested_data, '$.project_id') = ?
                """, (contact_id, project_id))
            elif proposal_id:
                cursor.execute("""
                    SELECT 1 FROM ai_suggestions
                    WHERE suggestion_type = 'contact_link'
                      AND status = 'pending'
                      AND json_extract(suggested_data, '$.contact_id') = ?
                      AND json_extract(suggested_data, '$.proposal_id') = ?
                """, (contact_id, proposal_id))
            else:
                return False
            return cursor.fetchone() is not None

    def new_contact_suggestion_exists(self, email: str) -> bool:
        """Check if a new_contact suggestion already exists for this email"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM ai_suggestions
                WHERE suggestion_type = 'new_contact'
                  AND status = 'pending'
                  AND json_extract(suggested_data, '$.email') = ?
            """, (email.lower(),))
            return cursor.fetchone() is not None

    def calculate_confidence(self, email_count: int) -> float:
        """Calculate confidence score based on email count"""
        if email_count >= 10:
            return 0.95
        elif email_count >= 5:
            return 0.85
        elif email_count >= 3:
            return 0.75
        elif email_count >= 2:
            return 0.65
        else:
            return 0.55

    def create_contact_link_suggestion(self, link_data: Dict, link_type: str) -> bool:
        """
        Create a contact_link suggestion.

        Args:
            link_data: Dict with contact_id, project_id or proposal_id, email_count, etc.
            link_type: 'project' or 'proposal'
        """
        contact_id = link_data['contact_id']
        project_id = link_data.get('project_id')
        proposal_id = link_data.get('proposal_id')
        project_code = link_data.get('project_code')
        email_count = link_data.get('email_count', 1)

        # Check for existing link
        if self.is_already_linked(contact_id, project_id, proposal_id):
            self.stats['already_linked'] += 1
            return False

        # Check for existing suggestion
        if self.suggestion_exists(contact_id, project_id, proposal_id):
            self.stats['already_suggested'] += 1
            return False

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                confidence = self.calculate_confidence(email_count)
                contact_name = link_data.get('contact_name') or link_data.get('contact_email')

                # Build suggested data
                suggested_data = {
                    'contact_id': contact_id,
                    'email_count': email_count,
                    'confidence_score': confidence
                }
                if project_id:
                    suggested_data['project_id'] = project_id
                if proposal_id:
                    suggested_data['proposal_id'] = proposal_id
                if project_code:
                    suggested_data['project_code'] = project_code

                # Determine priority
                if confidence >= 0.85:
                    priority = 'high'
                elif confidence >= 0.70:
                    priority = 'medium'
                else:
                    priority = 'low'

                target_desc = project_code or f"{'project' if project_id else 'proposal'}"
                title = f"Link {contact_name} to {target_desc}"
                description = (
                    f"Contact sent {email_count} email(s) to this "
                    f"{'project' if project_id else 'proposal'}. "
                    f"First: {link_data.get('first_email', 'unknown')}, "
                    f"Last: {link_data.get('last_email', 'unknown')}"
                )

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
                        project_code,
                        proposal_id,
                        status,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
                """, (
                    'contact_link',
                    priority,
                    confidence,
                    'email',  # Source is email analysis
                    contact_id,  # Use contact_id as source_id
                    f"Contact {contact_name} ({link_data.get('contact_email')})",
                    title,
                    description,
                    f"Create project_contact_links record",
                    json.dumps(suggested_data),
                    'project_contact_links',
                    project_code,
                    proposal_id
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating suggestion: {e}")
            self.stats['errors'] += 1
            return False

    def create_new_contact_suggestion(self, sender_data: Dict) -> bool:
        """Create a new_contact suggestion for unknown email sender"""
        email = sender_data.get('sender_email', '').lower().strip()
        name = sender_data.get('sender_name', '')

        # Clean up name (remove email from display name)
        if name:
            # Remove email-style suffix like "Name <email@domain.com>"
            if '<' in name:
                name = name.split('<')[0].strip()
            # Remove quotes
            name = name.strip('"\'')

        if not email or '@' not in email:
            return False

        # Check for existing suggestion
        if self.new_contact_suggestion_exists(email):
            self.stats['already_suggested'] += 1
            return False

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                project_code = sender_data.get('project_code')
                email_count = sender_data.get('email_count', 1)

                suggested_data = {
                    'email': email,
                    'name': name or None,
                    'project_code': project_code
                }

                title = f"Create contact: {name or email}"
                description = (
                    f"Sender found in {email_count} email(s) linked to {project_code}. "
                    f"No matching contact record exists."
                )

                cursor.execute("""
                    INSERT INTO ai_suggestions (
                        suggestion_type,
                        priority,
                        confidence_score,
                        source_type,
                        source_reference,
                        title,
                        description,
                        suggested_action,
                        suggested_data,
                        target_table,
                        project_code,
                        status,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
                """, (
                    'new_contact',
                    'medium',
                    0.8,
                    'email',
                    f"Email sender: {email}",
                    title,
                    description,
                    "Create contacts record",
                    json.dumps(suggested_data),
                    'contacts',
                    project_code
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating new_contact suggestion: {e}")
            self.stats['errors'] += 1
            return False

    def run(self, dry_run: bool = False, min_emails: int = 1) -> Dict:
        """
        Run the contact-project linking pipeline.

        Args:
            dry_run: If True, just report what would be created
            min_emails: Minimum email count to create a suggestion

        Returns:
            Statistics dict
        """
        print(f"{'[DRY RUN] ' if dry_run else ''}Starting contact-project linking...")

        # Process project links
        print("\nFinding contacts from email_project_links...")
        project_links = self.get_contact_project_links_from_emails()
        print(f"  Found {len(project_links)} contact-project pairs")

        for link in project_links:
            if link['email_count'] < min_emails:
                continue

            self.stats['project_links_found'] += 1

            if dry_run:
                print(
                    f"  Would suggest: {link['contact_name']} -> "
                    f"{link['project_code']} ({link['email_count']} emails)"
                )
            else:
                if self.create_contact_link_suggestion(link, 'project'):
                    self.stats['suggestions_created'] += 1

        # Process proposal links
        print("\nFinding contacts from email_proposal_links...")
        proposal_links = self.get_contact_proposal_links_from_emails()
        print(f"  Found {len(proposal_links)} contact-proposal pairs")

        for link in proposal_links:
            if link['email_count'] < min_emails:
                continue

            self.stats['proposal_links_found'] += 1

            if dry_run:
                print(
                    f"  Would suggest: {link['contact_name']} -> "
                    f"{link['project_code']} (proposal) ({link['email_count']} emails)"
                )
            else:
                if self.create_contact_link_suggestion(link, 'proposal'):
                    self.stats['suggestions_created'] += 1

        # Process unknown senders (create new contacts)
        print("\nFinding unknown email senders...")
        unknown_senders = self.get_unknown_senders()
        print(f"  Found {len(unknown_senders)} unknown senders")

        for sender in unknown_senders:
            if sender['email_count'] < min_emails:
                continue

            if dry_run:
                print(
                    f"  Would suggest new contact: {sender['sender_email']} "
                    f"({sender['email_count']} emails to {sender['project_code']})"
                )
            else:
                if self.create_new_contact_suggestion(sender):
                    self.stats['new_contacts_suggested'] += 1

        # Print summary
        print("\n" + "=" * 50)
        print("CONTACT-PROJECT LINKING SUMMARY")
        print("=" * 50)
        print(f"Project links found:       {self.stats['project_links_found']}")
        print(f"Proposal links found:      {self.stats['proposal_links_found']}")
        print(f"Already linked:            {self.stats['already_linked']}")
        print(f"Already has suggestion:    {self.stats['already_suggested']}")
        print(f"New contacts suggested:    {self.stats['new_contacts_suggested']}")
        print(f"Errors:                    {self.stats['errors']}")
        print(f"\nSuggestions created:       {self.stats['suggestions_created']}")

        return self.stats


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Create suggestions to link contacts to projects/proposals'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without creating suggestions'
    )
    parser.add_argument(
        '--min-emails',
        type=int,
        default=1,
        help='Minimum email count to create a suggestion (default: 1)'
    )
    parser.add_argument(
        '--db',
        default=DB_PATH,
        help='Database path'
    )
    args = parser.parse_args()

    linker = ContactProjectLinker(args.db)
    stats = linker.run(dry_run=args.dry_run, min_emails=args.min_emails)

    return stats


if __name__ == '__main__':
    main()
