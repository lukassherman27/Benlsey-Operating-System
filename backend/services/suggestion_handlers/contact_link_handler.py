"""
Contact link handler for contact_link suggestions.

Links existing contacts to projects or proposals when suggestions are approved.
"""

from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class ContactLinkHandler(BaseSuggestionHandler):
    """
    Handler for contact_link suggestions.

    Creates a link in project_contact_links table.
    Links can be to either a project_id or proposal_id (or both).
    """

    suggestion_type = "contact_link"
    target_table = "project_contact_links"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for linking a contact.

        Required: contact_id and either project_id or proposal_id.
        """
        errors = []

        contact_id = suggested_data.get("contact_id")
        if not contact_id:
            errors.append("Contact ID is required")
            return errors

        project_id = suggested_data.get("project_id")
        proposal_id = suggested_data.get("proposal_id")

        if not project_id and not proposal_id:
            errors.append("Either project_id or proposal_id is required")
            return errors

        cursor = self.conn.cursor()

        # Verify contact exists
        cursor.execute(
            "SELECT contact_id, email, name FROM contacts WHERE contact_id = ?",
            (contact_id,)
        )
        if not cursor.fetchone():
            errors.append(f"Contact #{contact_id} not found")
            return errors

        # Verify project exists if provided
        if project_id:
            cursor.execute(
                "SELECT project_id, project_code FROM projects WHERE project_id = ?",
                (project_id,)
            )
            if not cursor.fetchone():
                errors.append(f"Project #{project_id} not found")
                return errors

        # Verify proposal exists if provided
        if proposal_id:
            cursor.execute(
                "SELECT proposal_id, project_code FROM proposals WHERE proposal_id = ?",
                (proposal_id,)
            )
            if not cursor.fetchone():
                errors.append(f"Proposal #{proposal_id} not found")
                return errors

        # Check for duplicate link
        if project_id:
            cursor.execute("""
                SELECT link_id FROM project_contact_links
                WHERE contact_id = ? AND project_id = ?
            """, (contact_id, project_id))
            if cursor.fetchone():
                errors.append(
                    f"Contact #{contact_id} is already linked to project #{project_id}"
                )
        elif proposal_id:
            cursor.execute("""
                SELECT link_id FROM project_contact_links
                WHERE contact_id = ? AND proposal_id = ?
            """, (contact_id, proposal_id))
            if cursor.fetchone():
                errors.append(
                    f"Contact #{contact_id} is already linked to proposal #{proposal_id}"
                )

        return errors

    def preview(
        self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]
    ) -> ChangePreview:
        """
        Generate preview of the contact link that will be created.
        """
        contact_id = suggested_data.get("contact_id")
        project_id = suggested_data.get("project_id")
        proposal_id = suggested_data.get("proposal_id")
        project_code = suggested_data.get("project_code")

        cursor = self.conn.cursor()

        # Get contact info for display
        cursor.execute(
            "SELECT email, name FROM contacts WHERE contact_id = ?",
            (contact_id,)
        )
        row = cursor.fetchone()
        contact_desc = row[1] or row[0] if row else f"Contact #{contact_id}"

        # Build target description
        if project_code:
            target_desc = project_code
        elif project_id:
            target_desc = f"project #{project_id}"
        elif proposal_id:
            target_desc = f"proposal #{proposal_id}"
        else:
            target_desc = "unknown"

        email_count = suggested_data.get("email_count", 0)
        summary = f"Link {contact_desc} to {target_desc}"
        if email_count:
            summary += f" ({email_count} emails)"

        changes = [
            {"field": "contact_id", "new": contact_id},
        ]

        if project_id:
            changes.append({"field": "project_id", "new": project_id})
        if proposal_id:
            changes.append({"field": "proposal_id", "new": proposal_id})
        if suggested_data.get("confidence_score"):
            changes.append({
                "field": "confidence_score",
                "new": suggested_data["confidence_score"]
            })
        if suggested_data.get("role"):
            changes.append({"field": "role", "new": suggested_data["role"]})

        return ChangePreview(
            table="project_contact_links",
            action="insert",
            summary=summary,
            changes=changes
        )

    def apply(
        self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]
    ) -> SuggestionResult:
        """
        Create a link in project_contact_links table.

        Returns rollback_data with link_id for undo.
        """
        cursor = self.conn.cursor()

        contact_id = suggested_data.get("contact_id")
        project_id = suggested_data.get("project_id")
        proposal_id = suggested_data.get("proposal_id")
        email_count = suggested_data.get("email_count", 0)
        confidence_score = suggested_data.get("confidence_score", 0.8)
        role = suggested_data.get("role")
        suggestion_id = suggestion.get("suggestion_id")

        # Insert the link
        cursor.execute("""
            INSERT INTO project_contact_links (
                contact_id, project_id, proposal_id, role,
                email_count, confidence_score, source, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contact_id,
            project_id,
            proposal_id,
            role,
            email_count,
            confidence_score,
            "ai_suggestion",
            f"suggestion_id={suggestion_id}"
        ))

        link_id = cursor.lastrowid
        self.conn.commit()

        # Record the change in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name="project_contact_links",
            record_id=link_id,
            field_name=None,
            old_value=None,
            new_value=f"contact_id={contact_id},project_id={project_id}",
            change_type="insert"
        )
        self.conn.commit()

        # Get contact name for message
        cursor.execute(
            "SELECT email, name FROM contacts WHERE contact_id = ?",
            (contact_id,)
        )
        row = cursor.fetchone()
        contact_desc = row[1] or row[0] if row else f"Contact #{contact_id}"

        project_code = suggested_data.get("project_code")
        if project_code:
            target_desc = project_code
        elif project_id:
            target_desc = f"project #{project_id}"
        else:
            target_desc = f"proposal #{proposal_id}"

        return SuggestionResult(
            success=True,
            message=f"Linked {contact_desc} to {target_desc}",
            changes_made=[{
                "table": "project_contact_links",
                "record_id": link_id,
                "change_type": "insert"
            }],
            rollback_data={
                "link_id": link_id,
                "contact_id": contact_id,
                "project_id": project_id,
                "proposal_id": proposal_id
            }
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Delete the created contact link.
        """
        link_id = rollback_data.get("link_id")
        if not link_id:
            return False

        cursor = self.conn.cursor()

        # Delete the link
        cursor.execute(
            "DELETE FROM project_contact_links WHERE link_id = ?",
            (link_id,)
        )

        # Mark the change record as rolled back
        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'project_contact_links'
              AND record_id = ?
              AND change_type = 'insert'
        """, (link_id,))

        self.conn.commit()

        return cursor.rowcount > 0 or True
