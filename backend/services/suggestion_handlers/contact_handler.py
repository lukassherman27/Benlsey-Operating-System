"""
Contact handler for new_contact suggestions.

Creates contacts in the contacts table when suggestions are approved.
"""

from datetime import datetime
from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class ContactHandler(BaseSuggestionHandler):
    """
    Handler for new_contact suggestions.

    Creates a new contact in the contacts table.
    Validates email uniqueness before insert.
    """

    suggestion_type = "new_contact"
    target_table = "contacts"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for creating a contact.

        Required: email address (must be unique).
        """
        errors = []

        email = suggested_data.get("email")
        if not email:
            errors.append("Email address is required")
            return errors

        # Basic email format validation
        if "@" not in email or "." not in email:
            errors.append(f"Invalid email format: {email}")
            return errors

        # Check if email already exists
        cursor = self.conn.cursor()
        cursor.execute("SELECT contact_id FROM contacts WHERE email = ?", (email.lower(),))
        if cursor.fetchone():
            errors.append(f"Contact with email '{email}' already exists")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the contact that will be created.
        """
        email = suggested_data.get("email", "").lower()
        name = suggested_data.get("name") or suggested_data.get("contact_name")
        company = suggested_data.get("company") or suggested_data.get("organization")
        role = suggested_data.get("role") or suggested_data.get("position")

        summary = f"Create contact: {name or email}"
        if company:
            summary += f" at {company}"

        changes = [{"field": "email", "new": email}]

        if name:
            changes.append({"field": "name", "new": name})
        if company:
            changes.append({"field": "company", "new": company})
        if role:
            changes.append({"field": "role", "new": role})

        return ChangePreview(
            table="contacts",
            action="insert",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Create a new contact in the contacts table.

        Returns rollback_data with the contact_id for undo.
        """
        cursor = self.conn.cursor()

        email = suggested_data.get("email", "").lower().strip()
        name = suggested_data.get("name") or suggested_data.get("contact_name")
        company = suggested_data.get("company") or suggested_data.get("organization")
        role = suggested_data.get("role") or suggested_data.get("position")
        phone = suggested_data.get("phone")
        notes = suggested_data.get("notes") or suggested_data.get("context")
        suggestion_id = suggestion.get("suggestion_id")

        # Build source info
        source = "ai_suggestion"
        if suggestion.get("source_type") == "email":
            source = f"email:{suggestion.get('source_id')}"
        elif suggestion.get("source_type") == "transcript":
            source = f"transcript:{suggestion.get('source_id')}"

        today = datetime.now().strftime("%Y-%m-%d")

        # Insert the contact
        cursor.execute("""
            INSERT INTO contacts (
                email, name, company, role, phone,
                notes, source, first_seen_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email,
            name,
            company,
            role,
            phone,
            notes,
            source,
            today
        ))

        contact_id = cursor.lastrowid
        self.conn.commit()

        # Record the change in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name="contacts",
            record_id=contact_id,
            field_name=None,
            old_value=None,
            new_value=f"email={email}",
            change_type="insert"
        )
        self.conn.commit()

        display_name = name or email
        return SuggestionResult(
            success=True,
            message=f"Created contact #{contact_id}: {display_name}",
            changes_made=[{
                "table": "contacts",
                "record_id": contact_id,
                "change_type": "insert"
            }],
            rollback_data={"contact_id": contact_id, "email": email}
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Delete the created contact.
        """
        contact_id = rollback_data.get("contact_id")
        if not contact_id:
            return False

        cursor = self.conn.cursor()

        # Delete the contact
        cursor.execute("DELETE FROM contacts WHERE contact_id = ?", (contact_id,))

        # Mark the change record as rolled back
        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'contacts' AND record_id = ? AND change_type = 'insert'
        """, (contact_id,))

        self.conn.commit()

        return cursor.rowcount > 0 or True
