# AGENT 3: Backend Email APIs

**Your Mission:** Build 5 email API endpoints in FastAPI backend

**What You're Building:**
- Email detail endpoint (full email with AI insights)
- Email thread endpoint (conversation view)
- Email search endpoint (full-text search with filters)
- Bulk operations endpoint (batch actions)
- Email linking endpoints (link/unlink emails to proposals)

**CRITICAL RULES:**
- ✅ Add endpoints to existing `backend/api/main.py`
- ✅ Use existing database connection
- ✅ Test each endpoint with curl
- ❌ DO NOT create new files for these endpoints
- ❌ DO NOT modify existing endpoints

**Dependencies:** Wait for Agent 1 to complete (needs email_content populated)

---

## Add to backend/api/main.py

Add these endpoints to the existing FastAPI app:

```python
# ============================================================
# EMAIL ENDPOINTS - Added by Agent 3
# ============================================================

@app.get("/api/emails/{email_id}/detail")
async def get_email_detail(email_id: int):
    """
    Get full email with AI insights, linked proposals, and thread info
    """
    try:
        cursor = get_db_cursor()

        # Get email with AI content
        cursor.execute("""
            SELECT
                e.*,
                ec.clean_body,
                ec.ai_summary,
                ec.sentiment,
                ec.category,
                ec.urgency_level,
                ec.action_required,
                ec.key_points,
                ec.entities,
                ec.inferred_project_code,
                ec.requires_response
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.email_id = ?
        """, (email_id,))

        email_row = cursor.fetchone()
        if not email_row:
            raise HTTPException(status_code=404, detail="Email not found")

        email_dict = dict(email_row)

        # Parse JSON fields
        if email_dict.get('key_points'):
            email_dict['key_points'] = json.loads(email_dict['key_points'])
        if email_dict.get('entities'):
            email_dict['entities'] = json.loads(email_dict['entities'])

        # Get linked proposals
        cursor.execute("""
            SELECT
                p.proposal_id,
                p.project_code,
                p.project_name,
                p.current_status,
                p.client_name,
                epl.confidence_score,
                epl.link_type,
                epl.linked_at
            FROM email_proposal_links epl
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE epl.email_id = ?
            ORDER BY epl.confidence_score DESC
        """, (email_id,))

        email_dict['linked_proposals'] = [dict(row) for row in cursor.fetchall()]

        # Get thread info if email is in a thread
        if email_dict.get('thread_id'):
            cursor.execute("""
                SELECT
                    thread_id,
                    thread_subject,
                    email_count,
                    first_email_date,
                    last_email_date
                FROM email_threads
                WHERE thread_id = ?
            """, (email_dict['thread_id'],))

            thread_row = cursor.fetchone()
            if thread_row:
                email_dict['thread'] = dict(thread_row)

        return email_dict

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emails/thread/{thread_id}")
async def get_email_thread(thread_id: int):
    """
    Get all emails in a conversation thread, ordered chronologically
    """
    try:
        cursor = get_db_cursor()

        # Get thread metadata
        cursor.execute("""
            SELECT *
            FROM email_threads
            WHERE thread_id = ?
        """, (thread_id,))

        thread_row = cursor.fetchone()
        if not thread_row:
            raise HTTPException(status_code=404, detail="Thread not found")

        thread_dict = dict(thread_row)

        # Get all emails in thread
        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.body_full,
                ec.ai_summary,
                ec.sentiment,
                ec.category
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.thread_id = ?
            ORDER BY e.date ASC
        """, (thread_id,))

        thread_dict['emails'] = [dict(row) for row in cursor.fetchall()]

        return thread_dict

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emails/search")
async def search_emails(
    q: str = Query(None, description="Search query"),
    category: str = Query(None, description="Filter by category"),
    sentiment: str = Query(None, description="Filter by sentiment"),
    urgency: str = Query(None, description="Filter by urgency level"),
    proposal_id: int = Query(None, description="Filter by linked proposal"),
    limit: int = Query(50, le=200),
    offset: int = Query(0)
):
    """
    Search emails with filters
    """
    try:
        cursor = get_db_cursor()

        # Build query
        conditions = []
        params = []

        base_query = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                ec.ai_summary,
                ec.sentiment,
                ec.category,
                ec.urgency_level,
                p.project_code,
                p.project_name
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
        """

        if q:
            conditions.append("(e.subject LIKE ? OR e.body_full LIKE ? OR ec.ai_summary LIKE ?)")
            search_term = f"%{q}%"
            params.extend([search_term, search_term, search_term])

        if category:
            conditions.append("ec.category = ?")
            params.append(category)

        if sentiment:
            conditions.append("ec.sentiment = ?")
            params.append(sentiment)

        if urgency:
            conditions.append("ec.urgency_level = ?")
            params.append(urgency)

        if proposal_id:
            conditions.append("epl.proposal_id = ?")
            params.append(proposal_id)

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        base_query += " ORDER BY e.date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(base_query, params)

        results = [dict(row) for row in cursor.fetchall()]

        # Get total count
        count_query = "SELECT COUNT(DISTINCT e.email_id) FROM emails e LEFT JOIN email_content ec ON e.email_id = ec.email_id LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)

        cursor.execute(count_query, params[:-2])  # Exclude limit/offset from count
        total = cursor.fetchone()[0]

        return {
            "results": results,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/emails/bulk-action")
async def bulk_email_action(
    email_ids: List[int] = Body(...),
    action: str = Body(...),
    target_proposal_id: int = Body(None)
):
    """
    Perform bulk actions on emails
    Actions: link, unlink, categorize
    """
    try:
        cursor = get_db_cursor()

        if action == "link" and target_proposal_id:
            # Link emails to proposal
            for email_id in email_ids:
                cursor.execute("""
                    INSERT OR REPLACE INTO email_proposal_links (
                        email_id, proposal_id, confidence_score, link_type, linked_at
                    ) VALUES (?, ?, 1.0, 'manual', ?)
                """, (email_id, target_proposal_id, datetime.now().isoformat()))

            conn.commit()
            return {"success": True, "action": "link", "count": len(email_ids)}

        elif action == "unlink":
            # Unlink emails
            placeholders = ",".join(["?" for _ in email_ids])
            cursor.execute(f"""
                DELETE FROM email_proposal_links
                WHERE email_id IN ({placeholders})
            """, email_ids)

            conn.commit()
            return {"success": True, "action": "unlink", "count": len(email_ids)}

        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/emails/{email_id}/link-proposal")
async def link_email_to_proposal(
    email_id: int,
    proposal_id: int = Body(...),
    confidence_score: float = Body(1.0)
):
    """
    Link an email to a proposal
    """
    try:
        cursor = get_db_cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO email_proposal_links (
                email_id, proposal_id, confidence_score, link_type, linked_at
            ) VALUES (?, ?, ?, 'manual', ?)
        """, (email_id, proposal_id, confidence_score, datetime.now().isoformat()))

        conn.commit()

        return {"success": True, "email_id": email_id, "proposal_id": proposal_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/emails/{email_id}/unlink-proposal/{proposal_id}")
async def unlink_email_from_proposal(email_id: int, proposal_id: int):
    """
    Unlink an email from a proposal
    """
    try:
        cursor = get_db_cursor()

        cursor.execute("""
            DELETE FROM email_proposal_links
            WHERE email_id = ? AND proposal_id = ?
        """, (email_id, proposal_id))

        conn.commit()

        return {"success": True, "email_id": email_id, "proposal_id": proposal_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Testing

Test each endpoint:

```bash
# 1. Get email detail
curl http://localhost:8000/api/emails/123/detail | python3 -m json.tool

# 2. Get email thread
curl http://localhost:8000/api/emails/thread/1 | python3 -m json.tool

# 3. Search emails
curl "http://localhost:8000/api/emails/search?q=contract&limit=10" | python3 -m json.tool

# 4. Search by category
curl "http://localhost:8000/api/emails/search?category=proposal" | python3 -m json.tool

# 5. Link email to proposal
curl -X POST http://localhost:8000/api/emails/123/link-proposal \
  -H "Content-Type: application/json" \
  -d '{"proposal_id": 45, "confidence_score": 0.95}'

# 6. Bulk link
curl -X POST http://localhost:8000/api/emails/bulk-action \
  -H "Content-Type: application/json" \
  -d '{"email_ids": [123, 124, 125], "action": "link", "target_proposal_id": 45}'
```

---

## SUCCESS CRITERIA

All endpoints return 200 OK with data:
- ✅ `/api/emails/{id}/detail` returns email with AI insights
- ✅ `/api/emails/thread/{id}` returns thread emails
- ✅ `/api/emails/search` returns filtered results
- ✅ Bulk operations work
- ✅ Link/unlink operations persist to database

**Report back:** "Agent 3 complete. 5 email API endpoints added and tested."
