"""
Bensley API Routers

Each router handles a specific domain of the API.
Import routers here to make them available via:
    from api.routers import proposals, projects, etc.
"""

from api.routers import auth
from api.routers import health
from api.routers import proposals
from api.routers import projects
from api.routers import emails
from api.routers import invoices
from api.routers import suggestions
from api.routers import dashboard
from api.routers import query
from api.routers import rfis
from api.routers import meetings
from api.routers import training
from api.routers import admin
from api.routers import deliverables
from api.routers import documents
from api.routers import contracts
from api.routers import milestones
from api.routers import outreach
from api.routers import intelligence
from api.routers import context
from api.routers import files
from api.routers import transcripts
from api.routers import finance
from api.routers import analytics
from api.routers import learning
from api.routers import agent

__all__ = [
    'auth',
    'health',
    'proposals',
    'projects',
    'emails',
    'invoices',
    'suggestions',
    'dashboard',
    'query',
    'rfis',
    'meetings',
    'training',
    'admin',
    'deliverables',
    'documents',
    'contracts',
    'milestones',
    'outreach',
    'intelligence',
    'context',
    'files',
    'transcripts',
    'finance',
    'analytics',
    'learning',
    'agent',
]
