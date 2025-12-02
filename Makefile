.PHONY: help install dev backend frontend test lint format clean db-backup health-check todos

# Default target
help:
	@echo "Bensley Operations Platform - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install     - Install all dependencies (Python + Node)"
	@echo "  make dev         - Start development servers (backend + frontend)"
	@echo ""
	@echo "Development:"
	@echo "  make backend     - Start FastAPI backend only"
	@echo "  make frontend    - Start Next.js frontend only"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run linters (ruff)"
	@echo "  make format      - Format code (black + ruff)"
	@echo ""
	@echo "Database:"
	@echo "  make db-backup   - Create database backup"
	@echo "  make db-schema   - Show database schema"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean       - Remove cache files and logs"
	@echo "  make imports     - Run full data import pipeline"
	@echo "  make health-check - Run codebase health checks"
	@echo "  make todos       - Show all TODOs in codebase"

# =============================================================================
# Setup
# =============================================================================

install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installing Node dependencies..."
	cd frontend && npm install
	@echo "Done!"

# =============================================================================
# Development Servers
# =============================================================================

backend:
	@echo "Starting FastAPI backend on http://localhost:8000..."
	cd backend && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "Starting Next.js frontend on http://localhost:3000..."
	cd frontend && npm run dev

dev:
	@echo "Starting both backend and frontend..."
	@make -j2 backend frontend

# =============================================================================
# Testing & Quality
# =============================================================================

test:
	@echo "Running tests..."
	pytest tests/ -v

lint:
	@echo "Running linter..."
	ruff check backend/ scripts/core/ scripts/analysis/ scripts/maintenance/

format:
	@echo "Formatting code..."
	black backend/ scripts/core/ scripts/analysis/ scripts/maintenance/
	ruff check --fix backend/ scripts/core/ scripts/analysis/ scripts/maintenance/

# =============================================================================
# Database
# =============================================================================

db-backup:
	@echo "Creating database backup..."
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	cp database/bensley_master.db database/backups/bensley_master_$$TIMESTAMP.db && \
	echo "Backup created: database/backups/bensley_master_$$TIMESTAMP.db"

db-schema:
	@echo "Database tables:"
	@sqlite3 database/bensley_master.db ".tables"

db-stats:
	@echo "Database statistics:"
	@sqlite3 database/bensley_master.db "SELECT 'Projects:', COUNT(*) FROM projects UNION ALL SELECT 'Proposals:', COUNT(*) FROM proposals UNION ALL SELECT 'Invoices:', COUNT(*) FROM invoices UNION ALL SELECT 'Emails:', COUNT(*) FROM emails;"

# =============================================================================
# Data Import
# =============================================================================

imports:
	@echo "Running full import pipeline..."
	python scripts/core/import_all_data.py

import-emails:
	@echo "Processing emails..."
	python scripts/core/smart_email_brain.py

# =============================================================================
# Health & Validation
# =============================================================================

health-check:
	@echo "Running health checks..."
	python3 scripts/core/health_check.py

validate:
	@echo "Running tests and linting..."
	@make lint
	@make test

todos:
	@echo "=== TODOs by Location ==="
	@echo ""
	@echo "Backend API:"
	@grep -n "TODO" backend/api/main.py 2>/dev/null || echo "  None"
	@echo ""
	@echo "Backend Services:"
	@grep -rn "TODO" backend/services/ --include="*.py" 2>/dev/null || echo "  None"
	@echo ""
	@echo "Frontend Components:"
	@grep -rn "TODO" frontend/src/components/ --include="*.tsx" 2>/dev/null || echo "  None"
	@echo ""
	@echo "Scripts:"
	@grep -rn "TODO" scripts/core/ --include="*.py" 2>/dev/null || echo "  None"
	@echo ""
	@echo "See TODO.md for organized list by agent"

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache 2>/dev/null || true
	@echo "Clean complete!"

# =============================================================================
# Reports
# =============================================================================

report:
	@echo "Generating daily report..."
	python reports/enhanced_report_generator.py

weekly-report:
	@echo "Generating weekly proposal report..."
	python scripts/core/generate_weekly_proposal_report.py
