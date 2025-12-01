"""
Contacts Router - Contact management endpoints

Endpoints:
    GET /api/contacts - List contacts with filters
    GET /api/contacts/{id} - Get single contact with linked projects
    POST /api/contacts - Create new contact
    PUT /api/contacts/{id} - Update contact
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3

from api.dependencies import DB_PATH
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["contacts"])


# ============================================================================
# CONTACT LIST ENDPOINTS
# ============================================================================

@router.get("/contacts")
async def get_contacts(
    company: Optional[str] = Query(None, description="Filter by company name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    project_id: Optional[int] = Query(None, description="Filter by linked project"),
    search: Optional[str] = Query(None, description="Search in name, email, company"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get list of contacts with optional filtering"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query with filters
        where_clauses = []
        params = []

        if company:
            where_clauses.append("c.company LIKE ?")
            params.append(f"%{company}%")

        if role:
            where_clauses.append("c.role LIKE ?")
            params.append(f"%{role}%")

        if search:
            where_clauses.append("(c.name LIKE ? OR c.email LIKE ? OR c.company LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        if project_id:
            # Join with project_contacts or email_project_links via email matching
            where_clauses.append("""
                c.contact_id IN (
                    SELECT DISTINCT c2.contact_id
                    FROM contacts c2
                    JOIN emails e ON LOWER(c2.email) = LOWER(e.sender_email) OR LOWER(c2.email) = LOWER(e.sender_email)
                    JOIN email_project_links epl ON e.email_id = epl.email_id
                    WHERE epl.project_id = ?
                )
            """)
            params.append(project_id)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM contacts c WHERE {where_sql}", params)
        total = cursor.fetchone()[0]

        # Get paginated results
        cursor.execute(f"""
            SELECT
                c.contact_id,
                c.name,
                c.email,
                c.role,
                c.phone,
                c.company,
                c.position,
                c.context_notes,
                c.source,
                c.first_seen_date,
                c.notes,
                c.client_id
            FROM contacts c
            WHERE {where_sql}
            ORDER BY c.name ASC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])

        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "contacts": contacts,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contacts/stats")
async def get_contact_stats():
    """Get contact statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT company) as unique_companies,
                SUM(CASE WHEN email IS NOT NULL AND email != '' THEN 1 ELSE 0 END) as with_email,
                SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as with_phone
            FROM contacts
        """)

        row = cursor.fetchone()
        stats = dict(row) if row else {}

        # Get top companies
        cursor.execute("""
            SELECT company, COUNT(*) as count
            FROM contacts
            WHERE company IS NOT NULL AND company != ''
            GROUP BY company
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_companies'] = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return item_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: int):
    """Get a single contact with linked projects"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get contact
        cursor.execute("""
            SELECT
                c.*,
                cl.company_name as client_name
            FROM contacts c
            LEFT JOIN clients cl ON c.client_id = cl.client_id
            WHERE c.contact_id = ?
        """, (contact_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Contact not found")

        contact = dict(row)

        # Get linked projects via email matching
        cursor.execute("""
            SELECT DISTINCT
                p.project_id,
                p.project_code,
                p.project_title,
                p.status,
                COUNT(e.email_id) as email_count
            FROM projects p
            JOIN email_project_links epl ON p.project_id = epl.project_id
            JOIN emails e ON epl.email_id = e.email_id
            WHERE LOWER(e.sender_email) = LOWER(?)
            GROUP BY p.project_id
            ORDER BY email_count DESC
            LIMIT 20
        """, (contact.get('email'),))

        contact['linked_projects'] = [dict(row) for row in cursor.fetchall()]

        # Get recent emails from this contact
        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.date,
                e.snippet
            FROM emails e
            WHERE LOWER(e.sender_email) = LOWER(?)
            ORDER BY e.date DESC
            LIMIT 10
        """, (contact.get('email'),))

        contact['recent_emails'] = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return item_response(contact)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTACT CRUD ENDPOINTS
# ============================================================================

@router.post("/contacts")
async def create_contact(
    name: str = Query(..., description="Contact name"),
    email: str = Query(..., description="Email address"),
    company: Optional[str] = Query(None, description="Company name"),
    role: Optional[str] = Query(None, description="Role/title"),
    position: Optional[str] = Query(None, description="Position"),
    phone: Optional[str] = Query(None, description="Phone number"),
    context_notes: Optional[str] = Query(None, description="Context notes"),
    source: Optional[str] = Query("manual", description="Source of contact"),
    notes: Optional[str] = Query(None, description="Additional notes")
):
    """Create a new contact"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT contact_id FROM contacts WHERE email = ?", (email,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Contact with email {email} already exists")

        # Insert new contact
        cursor.execute("""
            INSERT INTO contacts (
                name, email, company, role, position, phone,
                context_notes, source, first_seen_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, date('now'), ?)
        """, (name, email, company, role, position, phone, context_notes, source, notes))

        contact_id = cursor.lastrowid
        conn.commit()

        # Fetch the created contact
        cursor.execute("SELECT * FROM contacts WHERE contact_id = ?", (contact_id,))
        contact = dict(cursor.fetchone())

        conn.close()

        return action_response(True, data=contact, message="Contact created successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/contacts/{contact_id}")
async def update_contact(
    contact_id: int,
    name: Optional[str] = Query(None, description="Contact name"),
    email: Optional[str] = Query(None, description="Email address"),
    company: Optional[str] = Query(None, description="Company name"),
    role: Optional[str] = Query(None, description="Role/title"),
    position: Optional[str] = Query(None, description="Position"),
    phone: Optional[str] = Query(None, description="Phone number"),
    context_notes: Optional[str] = Query(None, description="Context notes"),
    notes: Optional[str] = Query(None, description="Additional notes")
):
    """Update an existing contact"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if contact exists
        cursor.execute("SELECT * FROM contacts WHERE contact_id = ?", (contact_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            raise HTTPException(status_code=404, detail="Contact not found")

        # Build update query
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if company is not None:
            updates.append("company = ?")
            params.append(company)
        if role is not None:
            updates.append("role = ?")
            params.append(role)
        if position is not None:
            updates.append("position = ?")
            params.append(position)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        if context_notes is not None:
            updates.append("context_notes = ?")
            params.append(context_notes)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            conn.close()
            return action_response(True, message="No updates provided")

        params.append(contact_id)
        cursor.execute(f"""
            UPDATE contacts SET {', '.join(updates)} WHERE contact_id = ?
        """, params)

        conn.commit()

        # Fetch updated contact
        cursor.execute("SELECT * FROM contacts WHERE contact_id = ?", (contact_id,))
        contact = dict(cursor.fetchone())

        conn.close()

        return action_response(True, data=contact, message="Contact updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int):
    """Delete a contact"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if contact exists
        cursor.execute("SELECT contact_id FROM contacts WHERE contact_id = ?", (contact_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute("DELETE FROM contacts WHERE contact_id = ?", (contact_id,))
        conn.commit()
        conn.close()

        return action_response(True, message="Contact deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
