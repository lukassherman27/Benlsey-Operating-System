#!/bin/bash
#
# Bensley Operations Platform - Rollback Script
#
# Rolls back to a previous commit and restores database.
# Use when a deployment goes wrong.
#
# Usage:
#   bash scripts/deploy/rollback.sh              # Interactive - shows options
#   bash scripts/deploy/rollback.sh HEAD~1       # Rollback 1 commit
#   bash scripts/deploy/rollback.sh abc123       # Rollback to specific commit
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[ROLLBACK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/home/bensley/bensley-operating-system}"
BACKUP_DIR="${BACKUP_DIR:-/home/bensley/backups}"

cd "$PROJECT_DIR" || error "Project directory not found"

log "Rollback script started"

# ============================================================================
# Interactive mode if no commit specified
# ============================================================================

TARGET_COMMIT="$1"

if [ -z "$TARGET_COMMIT" ]; then
    echo ""
    echo "Recent commits:"
    echo "==============="
    git log --oneline -10
    echo ""
    echo "Available database backups:"
    echo "==========================="
    ls -lh "$BACKUP_DIR"/bensley_master_*.db 2>/dev/null || echo "No backups found"
    echo ""
    read -p "Enter commit hash to rollback to (or 'q' to quit): " TARGET_COMMIT

    if [ "$TARGET_COMMIT" = "q" ] || [ -z "$TARGET_COMMIT" ]; then
        log "Rollback cancelled"
        exit 0
    fi
fi

# ============================================================================
# Verify commit exists
# ============================================================================

if ! git cat-file -e "$TARGET_COMMIT^{commit}" 2>/dev/null; then
    error "Commit not found: $TARGET_COMMIT"
fi

TARGET_FULL=$(git rev-parse "$TARGET_COMMIT")
CURRENT_COMMIT=$(git rev-parse HEAD)

log "Current commit: $CURRENT_COMMIT"
log "Rolling back to: $TARGET_FULL"

# ============================================================================
# Confirm rollback
# ============================================================================

echo ""
warn "This will:"
echo "  1. Checkout commit $TARGET_COMMIT"
echo "  2. Rebuild frontend"
echo "  3. Restart services"
echo ""
read -p "Continue? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    log "Rollback cancelled"
    exit 0
fi

# ============================================================================
# Stop services
# ============================================================================

log "Stopping services..."
if sudo -n true 2>/dev/null; then
    sudo systemctl stop bensley-frontend || true
    sudo systemctl stop bensley-backend || true
else
    warn "Cannot stop services without sudo"
fi

# ============================================================================
# Checkout target commit
# ============================================================================

log "Checking out $TARGET_COMMIT..."
git checkout "$TARGET_COMMIT" --force

# ============================================================================
# Optional: Restore database backup
# ============================================================================

echo ""
echo "Available database backups:"
ls -lh "$BACKUP_DIR"/bensley_master_*.db 2>/dev/null || echo "No backups found"
echo ""
read -p "Restore a database backup? (Enter filename or 'n' to skip): " DB_BACKUP

if [ "$DB_BACKUP" != "n" ] && [ -n "$DB_BACKUP" ]; then
    if [ -f "$BACKUP_DIR/$DB_BACKUP" ]; then
        log "Backing up current database..."
        cp database/bensley_master.db database/bensley_master_pre_rollback.db

        log "Restoring $DB_BACKUP..."
        cp "$BACKUP_DIR/$DB_BACKUP" database/bensley_master.db
        log "Database restored"
    else
        warn "Backup file not found: $DB_BACKUP"
    fi
fi

# ============================================================================
# Rebuild
# ============================================================================

log "Updating dependencies..."
source venv/bin/activate
pip install -r backend/requirements.txt --quiet

log "Rebuilding frontend..."
cd frontend
npm ci --production --quiet
npm run build
cd "$PROJECT_DIR"

# ============================================================================
# Restart services
# ============================================================================

log "Restarting services..."
if sudo -n true 2>/dev/null; then
    sudo systemctl start bensley-backend
    sudo systemctl start bensley-frontend
    log "Services restarted"
else
    warn "Cannot restart services without sudo. Restart manually."
fi

# ============================================================================
# Verify
# ============================================================================

log "Waiting for services to start..."
sleep 3

if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    log "Backend: OK"
else
    warn "Backend: May still be starting"
fi

# ============================================================================
# Complete
# ============================================================================

echo ""
echo "=============================================="
echo -e "${GREEN}Rollback complete!${NC}"
echo "=============================================="
echo ""
echo "Rolled back from: $CURRENT_COMMIT"
echo "            to: $(git rev-parse HEAD)"
echo ""
echo "Note: You are now in detached HEAD state."
echo "To return to main branch: git checkout main"
echo ""
echo "If issues persist, check logs:"
echo "  sudo journalctl -u bensley-backend -n 50"
echo ""
