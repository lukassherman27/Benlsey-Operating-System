"""
API Services - Centralized service initialization for all routers

This module initializes all services once and makes them available to routers.
Import services from here rather than initializing them in each router.

Usage:
    from api.services import proposal_service, email_service
"""

import sys
from pathlib import Path

# Add backend to path for service imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Add project root to path for utils
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.dependencies import DB_PATH
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Import all services
from services.proposal_service import ProposalService
from services.email_service import EmailService
from services.milestone_service import MilestoneService
from services.financial_service import FinancialService
from services.rfi_service import RFIService
from services.file_service import FileService
from services.context_service import ContextService
from services.meeting_service import MeetingService
from services.outreach_service import OutreachService
from services.override_service import OverrideService
from services.training_service import TrainingService
from services.proposal_query_service import ProposalQueryService
from services.query_service import QueryService
from services.contract_service import ContractService
from services.proposal_tracker_service import ProposalTrackerService
from services.training_data_service import TrainingDataService
from services.admin_service import AdminService
from services.email_intelligence_service import EmailIntelligenceService
from services.deliverables_service import DeliverablesService
from services.proposal_intelligence_service import ProposalIntelligenceService
from services.ai_learning_service import AILearningService
from services.follow_up_agent import FollowUpAgent
from services.calendar_service import CalendarService
from services.document_service import DocumentService
from services.meeting_briefing_service import MeetingBriefingService
from services.user_learning_service import UserLearningService
from services.invoice_service import InvoiceService
from services.email_orchestrator import EmailOrchestrator
from services.onedrive_service import get_onedrive_service

# Orphaned services now being connected (Dec 2025)
from services.pattern_first_linker import get_pattern_linker
from services.proposal_version_service import ProposalVersionService
from services.transcript_consolidation_service import TranscriptConsolidationService
from services.batch_suggestion_service import get_batch_service

# Initialize all services
try:
    logger.info(f"📂 Loading services with database: {DB_PATH}")

    proposal_service = ProposalService(DB_PATH)
    email_service = EmailService(DB_PATH)
    milestone_service = MilestoneService(DB_PATH)
    financial_service = FinancialService(DB_PATH)
    rfi_service = RFIService(DB_PATH)
    file_service = FileService(DB_PATH)
    context_service = ContextService(DB_PATH)
    meeting_service = MeetingService(DB_PATH)
    outreach_service = OutreachService(DB_PATH)
    override_service = OverrideService(DB_PATH)
    training_service = TrainingService(DB_PATH)
    proposal_query_service = ProposalQueryService(DB_PATH)
    query_service = QueryService(DB_PATH)
    contract_service = ContractService(DB_PATH)
    proposal_tracker_service = ProposalTrackerService(DB_PATH)
    admin_service = AdminService(DB_PATH)
    training_data_service = TrainingDataService(DB_PATH)
    email_intelligence_service = EmailIntelligenceService(DB_PATH)
    deliverables_service = DeliverablesService(DB_PATH)
    proposal_intelligence_service = ProposalIntelligenceService(DB_PATH)
    ai_learning_service = AILearningService(DB_PATH)
    follow_up_agent = FollowUpAgent(DB_PATH)
    calendar_service = CalendarService(DB_PATH)
    document_service = DocumentService(DB_PATH)
    meeting_briefing_service = MeetingBriefingService(DB_PATH)
    user_learning_service = UserLearningService(DB_PATH)
    invoice_service = InvoiceService(DB_PATH)
    email_orchestrator = EmailOrchestrator(DB_PATH)
    onedrive_service = get_onedrive_service(DB_PATH)

    # Orphaned services now being wired up (Dec 2025)
    pattern_linker = get_pattern_linker(DB_PATH)
    proposal_version_service = ProposalVersionService(DB_PATH)
    transcript_consolidation_service = TranscriptConsolidationService(DB_PATH)
    batch_suggestion_service = get_batch_service(DB_PATH)

    logger.info("✅ All services initialized successfully")

except Exception as e:
    logger.error(f"❌ Failed to initialize services: {e}")
    raise RuntimeError(f"Cannot initialize services: {e}")

# Export all services
__all__ = [
    'proposal_service',
    'email_service',
    'milestone_service',
    'financial_service',
    'rfi_service',
    'file_service',
    'context_service',
    'meeting_service',
    'outreach_service',
    'override_service',
    'training_service',
    'proposal_query_service',
    'query_service',
    'contract_service',
    'proposal_tracker_service',
    'admin_service',
    'training_data_service',
    'email_intelligence_service',
    'deliverables_service',
    'proposal_intelligence_service',
    'ai_learning_service',
    'follow_up_agent',
    'calendar_service',
    'document_service',
    'meeting_briefing_service',
    'user_learning_service',
    'invoice_service',
    'email_orchestrator',
    'onedrive_service',
    # Newly wired services (Dec 2025)
    'pattern_linker',
    'proposal_version_service',
    'transcript_consolidation_service',
    'batch_suggestion_service',
    'DB_PATH',
    'logger',
]
