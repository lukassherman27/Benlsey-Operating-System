#!/bin/bash
#
# Bensley Operations Platform - Server Setup Script
#
# This script installs all dependencies on a fresh Ubuntu 22.04 server.
# Run as root or with sudo.
#
# Usage: sudo bash scripts/deploy/setup-server.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[SETUP]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root or with sudo"
fi

log "Starting Bensley Operations Platform server setup..."

# ============================================================================
# System Updates
# ============================================================================

log "Updating system packages..."
apt update && apt upgrade -y

# ============================================================================
# Essential Tools
# ============================================================================

log "Installing essential tools..."
apt install -y \
    curl \
    wget \
    git \
    build-essential \
    sqlite3 \
    unzip \
    htop \
    ncdu

# ============================================================================
# Python 3.11
# ============================================================================

log "Installing Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3.11-distutils

# Verify installation
python3.11 --version || error "Python 3.11 installation failed"
log "Python 3.11 installed successfully"

# ============================================================================
# Node.js 20 LTS
# ============================================================================

log "Installing Node.js 20 LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Verify installation
node --version || error "Node.js installation failed"
npm --version || error "npm installation failed"
log "Node.js $(node --version) installed successfully"

# ============================================================================
# Caddy (Reverse Proxy)
# ============================================================================

log "Installing Caddy..."
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install -y caddy

# Create log directory
mkdir -p /var/log/caddy
chown caddy:caddy /var/log/caddy

# Verify installation
caddy version || error "Caddy installation failed"
log "Caddy installed successfully"

# ============================================================================
# UFW Firewall
# ============================================================================

log "Configuring firewall..."
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable
ufw status
log "Firewall configured"

# ============================================================================
# Create bensley user (if not exists)
# ============================================================================

if id "bensley" &>/dev/null; then
    log "User 'bensley' already exists"
else
    log "Creating 'bensley' user..."
    adduser --disabled-password --gecos "" bensley
    usermod -aG sudo bensley
    log "User 'bensley' created"
fi

# ============================================================================
# Directory Structure
# ============================================================================

log "Setting up directory structure..."
mkdir -p /home/bensley/backups
chown -R bensley:bensley /home/bensley

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "=============================================="
echo -e "${GREEN}Server setup complete!${NC}"
echo "=============================================="
echo ""
echo "Installed:"
echo "  - Python $(python3.11 --version | cut -d' ' -f2)"
echo "  - Node.js $(node --version)"
echo "  - npm $(npm --version)"
echo "  - Caddy $(caddy version | head -1)"
echo "  - SQLite $(sqlite3 --version | cut -d' ' -f1)"
echo ""
echo "Next steps:"
echo "  1. Clone the repository to /home/bensley/"
echo "  2. Run: cd /home/bensley/bensley-operating-system"
echo "  3. Copy and edit .env files"
echo "  4. Run: bash scripts/deploy/deploy.sh"
echo ""
echo "See docs/deployment/production-guide.md for detailed instructions."
echo ""
