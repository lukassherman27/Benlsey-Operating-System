#!/usr/bin/env python3
"""
Bensley Intelligence Platform - FastAPI Backend

This API exposes the intelligence layer built from your existing scripts.
Start with: uvicorn backend.api.main:app --reload
Access docs at: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="Bensley Intelligence API",
    description="AI-powered operations platform for Bensley Design Studios",
    version="1.0.0"
)

# Add CORS middleware for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection helper
def get_db_connection():
    """Get database connection"""
    db_path = os.getenv('DATABASE_PATH', os.path.expanduser('~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db'))
    if not os.path.exists(db_path):
        raise HTTPException(status_code=500, detail=f"Database not found at {db_path}")
    return sqlite3.connect(db_path)

# Pydantic models for request/response
class EmailInput(BaseModel):
    sender_email: str
    subject: str
    snippet: str
    body: Optional[str] = None

class ProjectResponse(BaseModel):
    project_id: int
    project_code: str
    project_name: str
    client_name: Optional[str] = None
    status: Optional[str] = None
    value: Optional[float] = None

class MetricsResponse(BaseModel):
    active_projects: int
    pending_rfis: int
    proposals_in_progress: int
    unprocessed_emails: int
    emails_processed_today: int
    last_updated: str

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Bensley Intelligence Platform API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "projects": "/projects",
            "emails": "/emails",
            "intelligence": "/intelligence"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "projects_in_db": project_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# ============================================================================
# DASHBOARD METRICS
# ============================================================================

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get real-time business metrics for dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Active projects
        cursor.execute("""
            SELECT COUNT(*) FROM projects
            WHERE status IN ('active', 'in-progress', 'ongoing')
        """)
        active_projects = cursor.fetchone()[0]

        # Pending RFIs (if table exists)
        try:
            cursor.execute("SELECT COUNT(*) FROM rfis WHERE status = 'pending'")
            pending_rfis = cursor.fetchone()[0]
        except:
            pending_rfis = 0

        # Proposals in progress
        try:
            cursor.execute("SELECT COUNT(*) FROM proposals WHERE status IN ('draft', 'in-progress')")
            proposals = cursor.fetchone()[0]
        except:
            proposals = 0

        # Unprocessed emails
        cursor.execute("SELECT COUNT(*) FROM emails WHERE processed = 0")
        unprocessed = cursor.fetchone()[0]

        # Emails processed today
        cursor.execute("""
            SELECT COUNT(*) FROM emails
            WHERE processed = 1
            AND date(date) = date('now')
        """)
        processed_today = cursor.fetchone()[0]

        return MetricsResponse(
            active_projects=active_projects,
            pending_rfis=pending_rfis,
            proposals_in_progress=proposals,
            unprocessed_emails=unprocessed,
            emails_processed_today=processed_today,
            last_updated=datetime.now().isoformat()
        )

    finally:
        conn.close()

# ============================================================================
# PROJECTS ENDPOINTS
# ============================================================================

@app.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all projects with optional filtering"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT project_id, project_code, project_name, client_name, status, value
            FROM projects
        """

        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)

        query += " ORDER BY project_id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)

        projects = []
        for row in cursor.fetchall():
            projects.append(ProjectResponse(
                project_id=row[0],
                project_code=row[1],
                project_name=row[2],
                client_name=row[3],
                status=row[4],
                value=row[5]
            ))

        return projects

    finally:
        conn.close()

@app.get("/projects/{project_code}")
async def get_project(project_code: str):
    """Get detailed information about a specific project"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get project details
        cursor.execute("""
            SELECT project_id, project_code, project_name, client_name, status, value
            FROM projects
            WHERE project_code = ?
        """, (project_code,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        project = {
            "project_id": row[0],
            "project_code": row[1],
            "project_name": row[2],
            "client_name": row[3],
            "status": row[4],
            "value": row[5]
        }

        # Get linked emails count
        cursor.execute("""
            SELECT COUNT(*) FROM email_project_links
            WHERE project_id = ?
        """, (row[0],))
        project["email_count"] = cursor.fetchone()[0]

        # Get recent activity
        cursor.execute("""
            SELECT e.date, e.subject, e.sender_email
            FROM emails e
            JOIN email_project_links epl ON e.email_id = epl.email_id
            WHERE epl.project_id = ?
            ORDER BY e.date DESC
            LIMIT 5
        """, (row[0],))

        project["recent_activity"] = [
            {"date": r[0], "subject": r[1], "sender": r[2]}
            for r in cursor.fetchall()
        ]

        return project

    finally:
        conn.close()

@app.get("/projects/{project_code}/emails")
async def get_project_emails(
    project_code: str,
    limit: int = 50,
    offset: int = 0
):
    """Get all emails linked to a project"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT e.email_id, e.date, e.sender_email, e.subject, e.snippet,
                   epl.confidence, epl.link_method
            FROM emails e
            JOIN email_project_links epl ON e.email_id = epl.email_id
            JOIN projects p ON epl.project_id = p.project_id
            WHERE p.project_code = ?
            ORDER BY e.date DESC
            LIMIT ? OFFSET ?
        """, (project_code, limit, offset))

        emails = []
        for row in cursor.fetchall():
            emails.append({
                "email_id": row[0],
                "date": row[1],
                "sender": row[2],
                "subject": row[3],
                "snippet": row[4],
                "confidence": row[5],
                "link_method": row[6]
            })

        return emails

    finally:
        conn.close()

# ============================================================================
# EMAIL PROCESSING ENDPOINTS
# ============================================================================

@app.post("/emails/process")
async def process_email(email: EmailInput):
    """Process a new email through the intelligence pipeline"""
    # Import your existing email processor
    from backend.core.email_processor import EmailProcessor

    processor = EmailProcessor()

    # Note: You'll need to adapt your EmailProcessor to work with
    # individual emails rather than batch processing

    result = {
        "success": True,
        "email": email.dict(),
        "processing": {
            "tags_added": [],
            "projects_linked": [],
            "confidence": 0.0
        }
    }

    return result

@app.get("/emails/unprocessed")
async def get_unprocessed_emails(limit: int = 100):
    """Get list of unprocessed emails"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT email_id, date, sender_email, subject, snippet
            FROM emails
            WHERE processed = 0
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))

        emails = []
        for row in cursor.fetchall():
            emails.append({
                "email_id": row[0],
                "date": row[1],
                "sender": row[2],
                "subject": row[3],
                "snippet": row[4]
            })

        return emails

    finally:
        conn.close()

# ============================================================================
# INTELLIGENCE & PATTERNS
# ============================================================================

@app.get("/intelligence/patterns")
async def get_learned_patterns(pattern_type: Optional[str] = None):
    """Get learned patterns from the intelligence system"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT pattern_type, pattern_key, pattern_value,
                   confidence, occurrences, last_seen
            FROM learned_patterns
        """

        params = []
        if pattern_type:
            query += " WHERE pattern_type = ?"
            params.append(pattern_type)

        query += " ORDER BY confidence DESC, occurrences DESC LIMIT 100"

        cursor.execute(query, params)

        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                "type": row[0],
                "key": row[1],
                "value": row[2],
                "confidence": row[3],
                "occurrences": row[4],
                "last_seen": row[5]
            })

        return patterns

    finally:
        conn.close()

@app.get("/intelligence/stats")
async def get_intelligence_stats():
    """Get statistics about the intelligence system"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        stats = {}

        # Pattern counts
        cursor.execute("SELECT pattern_type, COUNT(*) FROM learned_patterns GROUP BY pattern_type")
        stats["patterns_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

        # Email processing stats
        cursor.execute("SELECT COUNT(*) FROM emails WHERE processed = 1")
        stats["emails_processed"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT email_id) FROM email_project_links")
        stats["emails_linked"] = cursor.fetchone()[0]

        # Tag stats
        cursor.execute("SELECT tag, COUNT(*) FROM email_tags GROUP BY tag ORDER BY COUNT(*) DESC LIMIT 10")
        stats["top_tags"] = {row[0]: row[1] for row in cursor.fetchall()}

        return stats

    finally:
        conn.close()

# ============================================================================
# QUERY INTERFACE (Natural Language)
# ============================================================================

@app.post("/query")
async def natural_language_query(query: Dict[str, str]):
    """
    Natural language query interface
    Future: This will use OpenAI to interpret queries
    """
    user_query = query.get("query", "")

    # For now, return a placeholder
    # You'll integrate OpenAI here to interpret queries and generate SQL

    return {
        "query": user_query,
        "answer": "Natural language queries coming soon. Use specific endpoints for now.",
        "suggested_endpoint": "/projects or /metrics"
    }

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))

    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║   Bensley Intelligence Platform API                      ║
    ╚══════════════════════════════════════════════════════════╝

    🚀 Starting server...
    📡 API:  http://localhost:{port}
    📚 Docs: http://localhost:{port}/docs
    🔍 Health: http://localhost:{port}/health

    Press Ctrl+C to stop
    """)

    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
