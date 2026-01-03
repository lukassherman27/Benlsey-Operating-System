#!/usr/bin/env python3
"""
Bensley Intelligence Platform - FastAPI Backend

A clean, modular API with domain-specific routers.
Start with: uvicorn api.main:app --reload --port 8000
Access docs at: http://localhost:8000/docs
"""

import os
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from api.rate_limit import limiter

# Add paths for imports
import sys
backend_path = Path(__file__).parent.parent
project_root = backend_path.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(project_root))

from utils.logger import get_logger

# Import DB_PATH from dependencies for consistency
from api.dependencies import DB_PATH

# Import all routers
from api.routers import (
    auth,
    health,
    proposals,
    projects,
    emails,
    invoices,
    suggestions,
    dashboard,
    query,
    rfis,
    meetings,
    training,
    admin,
    deliverables,
    documents,
    contracts,
    milestones,
    outreach,
    intelligence,
    context,
    files,
    transcripts,
    finance,
    analytics,
    learning,
    agent,
    contacts,
    tasks,
    my_day,
    previews,
    activities,
    story,
    weekly_report,
    team,
    upload,
    recordings,
    reports,
)

# Initialize logger
logger = get_logger(__name__)

# ============================================================================
# APP CONFIGURATION
# ============================================================================

ALLOWED_ORIGINS = os.getenv(
    'CORS_ORIGINS',
    'http://localhost:3000,http://localhost:3001,http://localhost:3002'
).split(',')

# ============================================================================
# APP LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Bensley Intelligence API starting up")
    logger.info(f"📂 Database: {DB_PATH}")
    logger.info("📚 API documentation available at /docs")
    yield
    logger.info("🛑 Bensley Intelligence API shutting down")


# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Bensley Intelligence API",
    description="AI-powered operations platform for Bensley Design Studios",
    version="2.0.0",
    lifespan=lifespan
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================================
# MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing"""
    start_time = time.perf_counter()

    # Skip logging for health checks
    if request.url.path in ["/", "/health", "/api/health"]:
        return await call_next(request)

    logger.info(f"{request.method} {request.url.path}")

    try:
        response = await call_next(request)
        duration = time.perf_counter() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
        return response
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"{request.method} {request.url.path} - ERROR ({duration:.3f}s): {e}", exc_info=True)
        raise


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Authentication
app.include_router(auth.router)

# Health & Status
app.include_router(health.router)

# Core Business
app.include_router(proposals.router)
app.include_router(projects.router)
app.include_router(emails.router)
app.include_router(invoices.router)
app.include_router(contracts.router)

# Operations
app.include_router(rfis.router)
app.include_router(meetings.router)
app.include_router(milestones.router)
app.include_router(deliverables.router)
app.include_router(outreach.router)
app.include_router(transcripts.router)

# Documents & Files
app.include_router(documents.router)
app.include_router(files.router)
app.include_router(upload.router)  # OneDrive upload (Issue #243)

# Intelligence & AI
app.include_router(suggestions.router)
app.include_router(dashboard.router)
app.include_router(query.router)
app.include_router(intelligence.router)

# Context & Admin
app.include_router(context.router)
app.include_router(training.router)
app.include_router(admin.router)

# Finance & Analytics
app.include_router(finance.router)
app.include_router(analytics.router)

# Learning & Agents
app.include_router(learning.router)
app.include_router(agent.router)

# Contacts
app.include_router(contacts.router)

# Tasks
app.include_router(tasks.router)

# Personal Workflow
app.include_router(my_day.router)

# Preview API (lightweight hover cards)
app.include_router(previews.router)

# Activity Tracking (Issue #140)
app.include_router(activities.router)

# Story Builder (Issue #141)
app.include_router(story.router)

# Weekly Report (Issue #142)
app.include_router(weekly_report.router)

# Team & PM Workload (Issue #192)
app.include_router(team.router)

# Meeting Recorder (Issue #194)
app.include_router(recordings.router)

# Reports API - Historical Reports (Issue #291)
app.include_router(reports.router)

# ============================================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions gracefully"""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": "Something went wrong. Our fault. Try again - we're not done yet.",
            "path": str(request.url.path)
        }
    )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API root - shows available documentation"""
    return {
        "name": "Bensley Intelligence API",
        "version": "2.0.0",
        "status": "BONG BANG! 🎉",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health"
    }


# ============================================================================
# API INFO
# ============================================================================

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Bensley Intelligence API",
        "version": "2.0.0",
        "description": "AI-powered operations platform for Bensley Design Studios",
        "routers": [
            {"name": "health", "prefix": "/api", "description": "Health checks"},
            {"name": "proposals", "prefix": "/api", "description": "Proposal management"},
            {"name": "projects", "prefix": "/api", "description": "Project management"},
            {"name": "emails", "prefix": "/api", "description": "Email processing"},
            {"name": "invoices", "prefix": "/api", "description": "Invoice management"},
            {"name": "contracts", "prefix": "/api", "description": "Contract management"},
            {"name": "rfis", "prefix": "/api", "description": "RFI management"},
            {"name": "meetings", "prefix": "/api", "description": "Meetings & calendar"},
            {"name": "milestones", "prefix": "/api", "description": "Milestone tracking"},
            {"name": "deliverables", "prefix": "/api", "description": "Deliverables management"},
            {"name": "outreach", "prefix": "/api", "description": "Client outreach"},
            {"name": "documents", "prefix": "/api", "description": "Document management"},
            {"name": "files", "prefix": "/api", "description": "File management"},
            {"name": "suggestions", "prefix": "/api", "description": "AI suggestions"},
            {"name": "dashboard", "prefix": "/api", "description": "Dashboard & KPIs"},
            {"name": "query", "prefix": "/api", "description": "Natural language queries"},
            {"name": "intelligence", "prefix": "/api", "description": "AI intelligence"},
            {"name": "context", "prefix": "/api", "description": "Context & notes"},
            {"name": "training", "prefix": "/api", "description": "AI training data"},
            {"name": "admin", "prefix": "/api", "description": "Admin & validation"},
            {"name": "tasks", "prefix": "/api", "description": "Task management"},
            {"name": "team", "prefix": "/api", "description": "Team & PM workload"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
