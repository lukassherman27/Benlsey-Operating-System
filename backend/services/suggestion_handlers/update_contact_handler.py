"""
Update contact handler for update_contact suggestions.

Updates existing contacts in the contacts table when suggestions are approved.
Tracks changes with before/after values for audit trail.

Supports two formats:
1. Single field update: {"target": "name/email", "field": "phone", "new": "123"}
2. Multi-field enrichment: {"contact_id": 123, "updates": {"phone": "123", "company": "ABC"}}
"""

from typing import Any, Dict, List, Optional

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class UpdateContactHandler(BaseSuggestionHandler):
    """Handler for update_contact suggestions with multi-field enrichment support."""

    suggestion_type = "update_contact"
    target_table = "contacts"
    is_actionable = True

    FIELD_MAP = {
        "email": "email",
        "phone": "phone",
        "role": "role",
        "company": "company",
        "name": "name",
        "notes": "notes",
        "linkedin_url": "linkedin_url",
        "location": "location",
        "position": "position",
    }

    def _is_enrichment_format(self, suggested_data: Dict[str, Any]) -> bool:
        """Check if data uses the multi-field enrichment format."""
        return "updates" in suggested_data and "contact_id" in suggested_data

    def _find_contact(self, target: str) -> Optional[Dict[str, Any]]:
        """Find a contact by name or email."""
        cursor = self.conn.cursor()
        for query in [
            ("SELECT contact_id, name, email, phone, role, company FROM contacts WHERE name = ?", (target,)),
            ("SELECT contact_id, name, email, phone, role, company FROM contacts WHERE LOWER(name) = LOWER(?)", (target,)),
            ("SELECT contact_id, name, email, phone, role, company FROM contacts WHERE email = ?", (target.lower(),)),
            ("SELECT contact_id, name, email, phone, role, company FROM contacts WHERE LOWER(name) LIKE ?", (f"%{target.lower()}%",)),
        ]:
            cursor.execute(query[0], query[1])
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def _get_contact_by_id(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Get contact by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT contact_id, name, email, phone, role, company, linkedin_url, location, position FROM contacts WHERE contact_id = ?",
            (contact_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """Validate the suggested data for updating a contact."""
        errors = []

        if self._is_enrichment_format(suggested_data):
            contact_id = suggested_data.get("contact_id")
            updates = suggested_data.get("updates", {})
            if not contact_id:
                return ["contact_id is required for enrichment"]
            if not updates:
                return ["updates dict is required for enrichment"]
            for field in updates.keys():
                if field not in self.FIELD_MAP:
                    errors.append(f"Invalid field '{field}'")
            if not self._get_contact_by_id(contact_id):
                errors.append(f"Contact ID {contact_id} not found")
            return errors

        target = suggested_data.get("target")
        if not target:
            return ["Target contact (name or email) is required"]
        field = suggested_data.get("field", "").lower()
        if field not in self.FIELD_MAP:
            return [f"Invalid field '{field}'"]
        new_value = suggested_data.get("new")
        if not new_value:
            return ["New value is required"]
        if field == "email" and ("@" not in new_value or "." not in new_value):
            return [f"Invalid email format: {new_value}"]
        if not self._find_contact(target):
            errors.append(f"Contact '{target}' not found")
        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """Generate preview of the contact update."""
        if self._is_enrichment_format(suggested_data):
            contact_id = suggested_data.get("contact_id")
            updates = suggested_data.get("updates", {})
            contact = self._get_contact_by_id(contact_id)
            if not contact:
                return ChangePreview(table="contacts", action="none", summary=f"Contact {contact_id} not found", changes=[])
            contact_name = contact.get("name") or contact.get("email") or f"Contact {contact_id}"
            changes = [{"field": f, "old": contact.get(self.FIELD_MAP.get(f, f), "") or "", "new": v} for f, v in updates.items()]
            return ChangePreview(table="contacts", action="update", summary=f"Enrich {contact_name}", changes=changes)

        target = suggested_data.get("target", "Unknown")
        field = suggested_data.get("field", "").lower()
        new_value = suggested_data.get("new", "")
        contact = self._find_contact(target)
        current = contact.get(self.FIELD_MAP.get(field, field), "") if contact else ""
        return ChangePreview(table="contacts", action="update", summary=f"Update {target}'s {field}", changes=[{"field": field, "old": current, "new": new_value}])

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """Update the contact field(s) in the contacts table."""
        cursor = self.conn.cursor()
        suggestion_id = suggestion.get("suggestion_id")

        if self._is_enrichment_format(suggested_data):
            contact_id = suggested_data.get("contact_id")
            updates = suggested_data.get("updates", {})
            contact = self._get_contact_by_id(contact_id)
            if not contact:
                return SuggestionResult(success=False, message=f"Contact ID {contact_id} not found", changes_made=[], rollback_data={})

            changes_made, rollback_fields, field_updates = [], {}, []
            for field, new_value in updates.items():
                db_field = self.FIELD_MAP.get(field, field)
                old_value = contact.get(db_field, "") or ""
                if field == "email":
                    new_value = new_value.lower().strip()
                cursor.execute(f"UPDATE contacts SET {db_field} = ? WHERE contact_id = ?", (new_value, contact_id))
                self._record_change(suggestion_id, "contacts", contact_id, db_field, str(old_value) if old_value else None, str(new_value), "update")
                changes_made.append({"table": "contacts", "record_id": contact_id, "field": db_field, "old_value": old_value, "new_value": new_value, "change_type": "update"})
                rollback_fields[db_field] = old_value
                field_updates.append(f"{field}: '{new_value}'")
            self.conn.commit()
            return SuggestionResult(success=True, message=f"Enriched contact: {', '.join(field_updates)}", changes_made=changes_made, rollback_data={"contact_id": contact_id, "fields": rollback_fields})

        target = suggested_data.get("target", "")
        field = suggested_data.get("field", "").lower()
        new_value = suggested_data.get("new", "")
        contact = self._find_contact(target)
        if not contact:
            return SuggestionResult(success=False, message=f"Contact '{target}' not found", changes_made=[], rollback_data={})

        contact_id = contact["contact_id"]
        db_field = self.FIELD_MAP.get(field, field)
        old_value = contact.get(db_field, "")
        if field == "email":
            new_value = new_value.lower().strip()
        cursor.execute(f"UPDATE contacts SET {db_field} = ? WHERE contact_id = ?", (new_value, contact_id))
        self.conn.commit()
        self._record_change(suggestion_id, "contacts", contact_id, db_field, str(old_value) if old_value else None, str(new_value), "update")
        self.conn.commit()
        return SuggestionResult(success=True, message=f"Updated {field}: '{old_value}' → '{new_value}'", changes_made=[{"table": "contacts", "record_id": contact_id, "field": db_field, "old_value": old_value, "new_value": new_value, "change_type": "update"}], rollback_data={"contact_id": contact_id, "field": db_field, "old_value": old_value, "new_value": new_value})

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """Restore the contact's previous value(s)."""
        contact_id = rollback_data.get("contact_id")
        if not contact_id:
            return False
        cursor = self.conn.cursor()
        if "fields" in rollback_data:
            for field, old_value in rollback_data["fields"].items():
                cursor.execute(f"UPDATE contacts SET {field} = ? WHERE contact_id = ?", (old_value, contact_id))
                cursor.execute("UPDATE suggestion_changes SET rolled_back = 1, rolled_back_at = datetime('now') WHERE table_name = 'contacts' AND record_id = ? AND field_name = ?", (contact_id, field))
            self.conn.commit()
            return True
        field = rollback_data.get("field")
        if not field:
            return False
        cursor.execute(f"UPDATE contacts SET {field} = ? WHERE contact_id = ?", (rollback_data.get("old_value"), contact_id))
        cursor.execute("UPDATE suggestion_changes SET rolled_back = 1, rolled_back_at = datetime('now') WHERE table_name = 'contacts' AND record_id = ? AND field_name = ?", (contact_id, field))
        self.conn.commit()
        return True
