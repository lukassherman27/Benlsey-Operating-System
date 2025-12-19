"""
Update contact handler for update_contact suggestions.

Updates existing contacts in the contacts table when suggestions are approved.
Tracks changes with before/after values for audit trail.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class UpdateContactHandler(BaseSuggestionHandler):
    """
    Handler for update_contact suggestions.

    Updates an existing contact's field (email, phone, role, company, name).
    Records old and new values for audit trail.
    """

    suggestion_type = "update_contact"
    target_table = "contacts"
    is_actionable = True

    # Map of allowed fields to database columns
    FIELD_MAP = {
        "email": "email",
        "phone": "phone",
        "role": "role",
        "company": "company",
        "name": "name",
        "notes": "notes",
    }

    def _find_contact(self, target: str) -> Optional[Dict[str, Any]]:
        """
        Find a contact by name or email.
        Returns contact dict or None if not found.
        """
        cursor = self.conn.cursor()

        # Try exact name match first
        cursor.execute(
            "SELECT contact_id, name, email, phone, role, company FROM contacts WHERE name = ?",
            (target,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)

        # Try case-insensitive name match
        cursor.execute(
            "SELECT contact_id, name, email, phone, role, company FROM contacts WHERE LOWER(name) = LOWER(?)",
            (target,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)

        # Try email match
        cursor.execute(
            "SELECT contact_id, name, email, phone, role, company FROM contacts WHERE email = ?",
            (target.lower(),)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)

        # Try partial name match (contains)
        cursor.execute(
            "SELECT contact_id, name, email, phone, role, company FROM contacts WHERE LOWER(name) LIKE ?",
            (f"%{target.lower()}%",)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for updating a contact.

        Required: target (name or email), field, new value.
        """
        errors = []

        target = suggested_data.get("target")
        if not target:
            errors.append("Target contact (name or email) is required")
            return errors

        field = suggested_data.get("field", "").lower()
        if field not in self.FIELD_MAP:
            errors.append(f"Invalid field '{field}'. Allowed: {', '.join(self.FIELD_MAP.keys())}")
            return errors

        new_value = suggested_data.get("new")
        if not new_value:
            errors.append("New value is required")
            return errors

        # Validate email format if updating email
        if field == "email":
            if "@" not in new_value or "." not in new_value:
                errors.append(f"Invalid email format: {new_value}")
            else:
                # Check if new email already exists
                cursor = self.conn.cursor()
                cursor.execute("SELECT contact_id FROM contacts WHERE email = ?", (new_value.lower(),))
                if cursor.fetchone():
                    errors.append(f"Email '{new_value}' is already used by another contact")

        # Check if contact exists
        contact = self._find_contact(target)
        if not contact:
            errors.append(f"Contact '{target}' not found")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the contact update.
        """
        target = suggested_data.get("target", "Unknown")
        field = suggested_data.get("field", "").lower()
        current = suggested_data.get("current", "")
        new_value = suggested_data.get("new", "")

        # Try to get actual current value from database
        contact = self._find_contact(target)
        if contact and field in self.FIELD_MAP:
            db_field = self.FIELD_MAP[field]
            current = contact.get(db_field, current) or current

        summary = f"Update {target}'s {field}: '{current}' → '{new_value}'"

        return ChangePreview(
            table="contacts",
            action="update",
            summary=summary,
            changes=[{
                "field": field,
                "old": current,
                "new": new_value
            }]
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Update the contact field in the contacts table.

        Returns rollback_data with the old value for undo.
        """
        cursor = self.conn.cursor()

        target = suggested_data.get("target", "")
        field = suggested_data.get("field", "").lower()
        new_value = suggested_data.get("new", "")
        suggestion_id = suggestion.get("suggestion_id")

        # Find the contact
        contact = self._find_contact(target)
        if not contact:
            return SuggestionResult(
                success=False,
                message=f"Contact '{target}' not found",
                changes_made=[],
                rollback_data={}
            )

        contact_id = contact["contact_id"]
        db_field = self.FIELD_MAP.get(field, field)
        old_value = contact.get(db_field, "")

        # Special handling for email (lowercase)
        if field == "email":
            new_value = new_value.lower().strip()

        # Update the contact
        cursor.execute(f"""
            UPDATE contacts
            SET {db_field} = ?
            WHERE contact_id = ?
        """, (new_value, contact_id))

        self.conn.commit()

        # Record the change in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name="contacts",
            record_id=contact_id,
            field_name=db_field,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value),
            change_type="update"
        )
        self.conn.commit()

        display_name = contact.get("name") or contact.get("email") or target
        return SuggestionResult(
            success=True,
            message=f"Updated {display_name}'s {field}: '{old_value}' → '{new_value}'",
            changes_made=[{
                "table": "contacts",
                "record_id": contact_id,
                "field": db_field,
                "old_value": old_value,
                "new_value": new_value,
                "change_type": "update"
            }],
            rollback_data={
                "contact_id": contact_id,
                "field": db_field,
                "old_value": old_value,
                "new_value": new_value
            }
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Restore the contact's previous value.
        """
        contact_id = rollback_data.get("contact_id")
        field = rollback_data.get("field")
        old_value = rollback_data.get("old_value")

        if not contact_id or not field:
            return False

        cursor = self.conn.cursor()

        # Restore the old value
        cursor.execute(f"""
            UPDATE contacts
            SET {field} = ?
            WHERE contact_id = ?
        """, (old_value, contact_id))

        # Mark the change record as rolled back
        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'contacts' AND record_id = ? AND field_name = ?
        """, (contact_id, field))

        self.conn.commit()

        return cursor.rowcount > 0 or True
