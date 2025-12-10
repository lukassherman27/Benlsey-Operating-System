"""
Proposal Version Service - Track proposal versions, fee changes, and documents

Provides:
- get_proposal_versions(project_code) - All versions with documents and fees
- get_fee_history(project_code) - Fee change timeline
- search_proposals_by_client(client) - Find proposals by client name
- record_proposal_sent(proposal_id, email_id, attachment_id, fee) - Record new version

Usage:
    from backend.services.proposal_version_service import ProposalVersionService
    svc = ProposalVersionService()
    versions = svc.get_proposal_versions('25 BK-087')  # Vahine Island
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base_service import BaseService

logger = logging.getLogger(__name__)


class ProposalVersionService(BaseService):
    """Service for tracking proposal versions, documents, and fee history"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)

    def get_proposal_versions(self, project_code: str) -> Dict[str, Any]:
        """
        Get all versions of a proposal with documents and fee history.

        Args:
            project_code: Project code like "25 BK-087"

        Returns:
            Dict with proposal info, versions list, and fee_changes list
        """
        # Get basic proposal info
        proposal = self.execute_query("""
            SELECT
                proposal_id, project_code, project_name, client_company,
                contact_person, contact_email, project_value as current_fee,
                num_proposals_sent, status, created_at, updated_at
            FROM proposals
            WHERE project_code = ?
        """, (project_code,), fetch_one=True)

        if not proposal:
            return {'success': False, 'error': f'Proposal {project_code} not found'}

        # Get proposal document versions from email_attachments
        versions = self.execute_query("""
            SELECT
                ea.attachment_id,
                ea.filename,
                ea.filepath,
                ea.version_number,
                ea.key_terms,
                COALESCE(DATE(e.date), DATE(ea.created_at)) as version_date,
                e.email_id,
                e.subject as email_subject,
                e.recipient_emails,
                e.sender_email
            FROM email_attachments ea
            LEFT JOIN emails e ON ea.email_id = e.email_id
            WHERE ea.proposal_id = ?
            AND ea.document_type = 'proposal'
            AND COALESCE(ea.is_junk, 0) = 0
            ORDER BY COALESCE(ea.version_number, 0), ea.created_at
        """, (proposal['proposal_id'],))

        # Assign version numbers if not set
        for i, v in enumerate(versions, 1):
            if not v.get('version_number'):
                v['version_number'] = i

        # Get fee change history from audit log
        fee_changes = self.execute_query("""
            SELECT
                old_value as previous_fee,
                new_value as new_fee,
                changed_at,
                changed_by,
                change_source
            FROM proposals_audit_log
            WHERE proposal_id = ?
            AND field_name IN ('project_value', 'total_fee', 'fee')
            ORDER BY changed_at DESC
        """, (proposal['proposal_id'],))

        return {
            'success': True,
            'project_code': proposal['project_code'],
            'project_name': proposal['project_name'],
            'client_company': proposal['client_company'],
            'contact_person': proposal['contact_person'],
            'contact_email': proposal['contact_email'],
            'current_fee': proposal['current_fee'],
            'num_versions': len(versions),
            'status': proposal['status'],
            'versions': [
                {
                    'version': v['version_number'],
                    'date': v['version_date'],
                    'document': v['filename'],
                    'filepath': v['filepath'],
                    'key_terms': v['key_terms'],
                    'email_id': v['email_id'],
                    'email_subject': v['email_subject'],
                    'sent_to': v['recipient_emails']
                }
                for v in versions
            ],
            'fee_changes': [
                {
                    'date': fc['changed_at'],
                    'previous_fee': fc['previous_fee'],
                    'new_fee': fc['new_fee'],
                    'changed_by': fc['changed_by'],
                    'source': fc['change_source']
                }
                for fc in fee_changes
            ]
        }

    def get_fee_history(self, project_code: str) -> List[Dict[str, Any]]:
        """
        Get fee change timeline for a proposal.

        Args:
            project_code: Project code like "25 BK-087"

        Returns:
            List of fee changes with dates and values
        """
        # First get the proposal_id
        proposal = self.execute_query("""
            SELECT proposal_id, project_value as current_fee, created_at
            FROM proposals WHERE project_code = ?
        """, (project_code,), fetch_one=True)

        if not proposal:
            return []

        # Get fee changes from audit log
        changes = self.execute_query("""
            SELECT
                old_value as previous_fee,
                new_value as new_fee,
                changed_at,
                changed_by,
                change_source,
                change_reason
            FROM proposals_audit_log
            WHERE proposal_id = ?
            AND field_name IN ('project_value', 'total_fee', 'fee')
            ORDER BY changed_at ASC
        """, (proposal['proposal_id'],))

        # Build timeline starting from initial creation
        timeline = []

        # Add initial fee if we have changes (first old_value is the initial)
        if changes and changes[0].get('previous_fee'):
            timeline.append({
                'date': proposal['created_at'],
                'fee': changes[0]['previous_fee'],
                'change_type': 'initial',
                'note': 'Initial fee'
            })

        # Add each change
        for change in changes:
            timeline.append({
                'date': change['changed_at'],
                'fee': change['new_fee'],
                'previous_fee': change['previous_fee'],
                'change_type': 'update',
                'changed_by': change['changed_by'],
                'source': change['change_source'],
                'note': change.get('change_reason')
            })

        # If no changes, just return current fee
        if not timeline:
            timeline.append({
                'date': proposal['created_at'],
                'fee': proposal['current_fee'],
                'change_type': 'initial',
                'note': 'Current fee (no changes recorded)'
            })

        return timeline

    def search_proposals_by_client(self, client: str, include_versions: bool = False) -> List[Dict[str, Any]]:
        """
        Search proposals by client name or company.

        Args:
            client: Client name to search (partial match)
            include_versions: If True, include version count for each proposal

        Returns:
            List of matching proposals
        """
        search_term = f'%{client}%'

        proposals = self.execute_query("""
            SELECT
                p.proposal_id,
                p.project_code,
                p.project_name,
                p.client_company,
                p.contact_person,
                p.contact_email,
                p.project_value as current_fee,
                p.num_proposals_sent,
                p.status,
                p.created_at
            FROM proposals p
            WHERE p.client_company LIKE ?
               OR p.contact_person LIKE ?
               OR p.project_name LIKE ?
            ORDER BY p.created_at DESC
            LIMIT 50
        """, (search_term, search_term, search_term))

        results = []
        for p in proposals:
            result = {
                'proposal_id': p['proposal_id'],
                'project_code': p['project_code'],
                'project_name': p['project_name'],
                'client_company': p['client_company'],
                'contact_person': p['contact_person'],
                'current_fee': p['current_fee'],
                'num_proposals_sent': p['num_proposals_sent'] or 0,
                'status': p['status']
            }

            if include_versions:
                # Count actual documents
                doc_count = self.execute_query("""
                    SELECT COUNT(*) as count
                    FROM email_attachments
                    WHERE proposal_id = ?
                    AND document_type = 'proposal'
                    AND COALESCE(is_junk, 0) = 0
                """, (p['proposal_id'],), fetch_one=True)

                result['document_count'] = doc_count['count'] if doc_count else 0

            results.append(result)

        return results

    def record_proposal_sent(
        self,
        proposal_id: int,
        email_id: int = None,
        attachment_id: int = None,
        fee: float = None,
        version_number: int = None
    ) -> Dict[str, Any]:
        """
        Record that a proposal was sent.

        This increments num_proposals_sent and optionally:
        - Links the email attachment
        - Records fee change in audit log
        - Sets version number on attachment

        Args:
            proposal_id: ID of the proposal
            email_id: ID of the sent email (optional)
            attachment_id: ID of the proposal attachment (optional)
            fee: Fee amount if known from proposal document (optional)
            version_number: Version number to assign (optional, auto-increments)

        Returns:
            Dict with success status and updated counts
        """
        # Get current proposal info
        proposal = self.execute_query("""
            SELECT project_code, project_name, num_proposals_sent, project_value
            FROM proposals WHERE proposal_id = ?
        """, (proposal_id,), fetch_one=True)

        if not proposal:
            return {'success': False, 'error': f'Proposal {proposal_id} not found'}

        current_count = proposal['num_proposals_sent'] or 0
        new_count = current_count + 1

        # Determine version number
        if version_number is None:
            version_number = new_count

        # Update proposal count
        self.execute_update("""
            UPDATE proposals
            SET num_proposals_sent = ?,
                updated_at = datetime('now')
            WHERE proposal_id = ?
        """, (new_count, proposal_id))

        # Update attachment version if provided
        if attachment_id:
            self.execute_update("""
                UPDATE email_attachments
                SET version_number = ?,
                    proposal_id = ?
                WHERE attachment_id = ?
            """, (version_number, proposal_id, attachment_id))

        # Record fee change if different from current
        if fee is not None and fee != proposal['project_value']:
            self.execute_update("""
                INSERT INTO proposals_audit_log
                (proposal_id, project_code, field_name, old_value, new_value,
                 changed_at, changed_by, change_source)
                VALUES (?, ?, 'project_value', ?, ?, datetime('now'), 'system', 'proposal_sent')
            """, (proposal_id, proposal['project_code'], proposal['project_value'], fee))

            # Update the actual fee
            self.execute_update("""
                UPDATE proposals
                SET project_value = ?,
                    updated_at = datetime('now')
                WHERE proposal_id = ?
            """, (fee, proposal_id))

        logger.info(
            f"Recorded proposal sent: {proposal['project_code']} "
            f"({proposal['project_name']}) version {version_number}"
        )

        return {
            'success': True,
            'project_code': proposal['project_code'],
            'project_name': proposal['project_name'],
            'version': version_number,
            'num_proposals_sent': new_count,
            'fee_updated': fee is not None and fee != proposal['project_value']
        }

    def get_version_summary_by_client(self, client: str) -> Dict[str, Any]:
        """
        Get a summary of all proposals sent to a client with version counts.

        Answers questions like: "How many proposals did we send to Vahine Island?"

        Args:
            client: Client name to search

        Returns:
            Summary with total proposals, versions, and fee timeline
        """
        proposals = self.search_proposals_by_client(client, include_versions=True)

        if not proposals:
            return {
                'success': True,
                'client': client,
                'total_proposals': 0,
                'total_versions_sent': 0,
                'proposals': []
            }

        total_versions = sum(p.get('document_count', 0) or p.get('num_proposals_sent', 0) for p in proposals)
        total_fee = sum(p.get('current_fee') or 0 for p in proposals)

        return {
            'success': True,
            'client': client,
            'total_proposals': len(proposals),
            'total_versions_sent': total_versions,
            'total_current_fee': total_fee,
            'proposals': [
                {
                    'project_code': p['project_code'],
                    'project_name': p['project_name'],
                    'versions_sent': p.get('document_count', 0) or p.get('num_proposals_sent', 0),
                    'current_fee': p['current_fee'],
                    'status': p['status']
                }
                for p in proposals
            ]
        }


# Singleton instance for easy import
_version_service_instance = None


def get_version_service(db_path: str = None) -> ProposalVersionService:
    """Get or create singleton ProposalVersionService instance"""
    global _version_service_instance
    if _version_service_instance is None or db_path:
        _version_service_instance = ProposalVersionService(db_path)
    return _version_service_instance
