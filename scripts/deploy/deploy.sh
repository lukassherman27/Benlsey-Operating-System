#!/bin/bash
#
# Bensley Operations Platform - Deployment Script
#
# Deploys the latest code and restarts services.
# Run from the project root directory.
#
# Usage: bash scripts/deploy/deploy.sh
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[DEPLOY]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/home/bensley/bensley-operating-system}"
BACKUP_DIR="${BACKUP_DIR:-/home/bensley/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Ensure we're in the right directory
cd "$PROJECT_DIR" || error "Project directory not found: $PROJECT_DIR"

log "Starting deployment at $(date)"

# ============================================================================
# Pre-deployment checks
# ============================================================================

log "Running pre-deployment checks..."

# Check .env exists
if [ ! -f ".env" ]; then
    error ".env file not found. Copy from .env.example and configure."
fi

# Check frontend .env.local exists
if [ ! -f "frontend/.env.local" ]; then
    error "frontend/.env.local not found. Copy from .env.example and configure."
fi

# ============================================================================
# Backup database
# ============================================================================

log "Backing up database..."
mkdir -p "$BACKUP_DIR"

if [ -f "database/bensley_master.db" ]; then
    cp database/bensley_master.db "$BACKUP_DIR/bensley_master_$TIMESTAMP.db"
    log "Database backed up to $BACKUP_DIR/bensley_master_$TIMESTAMP.db"

    # Keep only last 7 backups
    cd "$BACKUP_DIR"
    ls -t bensley_master_*.db | tail -n +8 | xargs -r rm --
    cd "$PROJECT_DIR"
    log "Old backups cleaned up (keeping last 7)"
else
    warn "No existing database found, skipping backup"
fi

# ============================================================================
# Pull latest code
# ============================================================================

log "Pulling latest code from git..."

# Stash any local changes
git stash --quiet || true

# Pull latest
git pull origin main || error "Git pull failed"

# Pop stashed changes if any
git stash pop --quiet 2>/dev/null || true

log "Code updated to $(git rev-parse --short HEAD)"

# ============================================================================
# Update Python dependencies
# ============================================================================

log "Updating Python dependencies..."

if [ ! -d "venv" ]; then
    log "Creating Python virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r backend/requirements.txt --quiet
log "Python dependencies updated"

# ============================================================================
# Update Node.js dependencies and build frontend
# ============================================================================

log "Building frontend..."
cd frontend

npm ci --production --quiet
npm run build || error "Frontend build failed"

cd "$PROJECT_DIR"
log "Frontend built successfully"

# ============================================================================
# Install/update systemd services
# ============================================================================

log "Updating systemd services..."

# Check if running as root or with sudo
if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
    sudo cp systemd/bensley-backend.service /etc/systemd/system/
    sudo cp systemd/bensley-frontend.service /etc/systemd/system/
    sudo cp systemd/bensley-email-sync.service /etc/systemd/system/
    sudo cp systemd/bensley-email-sync.timer /etc/systemd/system/
    sudo systemctl daemon-reload
    log "Systemd services updated"
else
    warn "Cannot update systemd services without sudo. Skipping."
    warn "Run manually: sudo cp systemd/*.service /etc/systemd/system/"
fi

# ============================================================================
# Restart services
# ============================================================================

log "Restarting services..."

if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
    sudo systemctl restart bensley-backend
    sudo systemctl restart bensley-frontend

    # Enable email sync timer if configured
    if grep -q "EMAIL_SERVER" .env 2>/dev/null; then
        sudo systemctl enable bensley-email-sync.timer
        sudo systemctl start bensley-email-sync.timer
        log "Email sync timer enabled"
    fi

    log "Services restarted"
else
    warn "Cannot restart services without sudo. Restart manually:"
    warn "  sudo systemctl restart bensley-backend"
    warn "  sudo systemctl restart bensley-frontend"
fi

# ============================================================================
# Health check
# ============================================================================

log "Running health checks..."
sleep 3  # Give services time to start

# Check backend
if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    log "Backend health check: PASSED"
else
    warn "Backend health check: FAILED (may still be starting)"
fi

# Check frontend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    log "Frontend health check: PASSED"
else
    warn "Frontend health check: FAILED (may still be starting)"
fi

# ============================================================================
# Complete
# ============================================================================

echo ""
echo "=============================================="
echo -e "${GREEN}Deployment complete!${NC}"
echo "=============================================="
echo ""
echo "Deployed: $(git rev-parse --short HEAD) - $(git log -1 --format=%s)"
echo "Time: $(date)"
echo ""
echo "Check status:"
echo "  sudo systemctl status bensley-backend"
echo "  sudo systemctl status bensley-frontend"
echo ""
echo "View logs:"
echo "  sudo journalctl -u bensley-backend -f"
echo "  sudo journalctl -u bensley-frontend -f"
echo ""
