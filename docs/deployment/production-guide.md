# Production Deployment Guide

This guide covers deploying the Bensley Operations Platform to a production server.

## Recommended Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| OS | Ubuntu 22.04 LTS | Long-term support, stable |
| Backend | Python 3.11 + uvicorn | FastAPI server |
| Frontend | Node.js 20 LTS + Next.js 15 | React-based UI |
| Reverse Proxy | Caddy | Auto HTTPS, simple config |
| Database | SQLite | Current; PostgreSQL for scale |
| Process Manager | systemd | Native Linux service management |

## Server Requirements

### Minimum (Development/Testing)
- **CPU**: 1 vCPU
- **RAM**: 2 GB
- **Disk**: 20 GB SSD
- **Estimated Cost**: ~$12/month (DigitalOcean, Linode)

### Recommended (Production)
- **CPU**: 2 vCPU
- **RAM**: 4 GB
- **Disk**: 50 GB SSD
- **Estimated Cost**: ~$24/month

### For Growth (10+ users)
- **CPU**: 4 vCPU
- **RAM**: 8 GB
- **Disk**: 100 GB SSD
- Consider PostgreSQL migration

## Quick Start

If you have a fresh Ubuntu 22.04 server with SSH access:

```bash
# 1. Clone repository
git clone https://github.com/your-org/bensley-operating-system.git
cd bensley-operating-system

# 2. Run setup script (installs all dependencies)
sudo bash scripts/deploy/setup-server.sh

# 3. Configure environment
cp .env.example .env
nano .env  # Edit with your values

cp frontend/.env.example frontend/.env.local
nano frontend/.env.local  # Edit with production URL

# 4. Deploy
bash scripts/deploy/deploy.sh

# 5. Configure domain (edit Caddyfile)
sudo nano /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## Detailed Setup Steps

### Step 1: Server Provisioning

Create a VPS with your preferred provider:
- [DigitalOcean](https://www.digitalocean.com/) - Recommended for simplicity
- [Linode](https://www.linode.com/) - Good performance/price
- [Vultr](https://www.vultr.com/) - Budget option

Select Ubuntu 22.04 LTS and the appropriate size from requirements above.

### Step 2: Initial Server Setup

```bash
# SSH into your server
ssh root@your-server-ip

# Create non-root user
adduser bensley
usermod -aG sudo bensley

# Set up SSH key auth (recommended)
su - bensley
mkdir ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys  # Paste your public key
chmod 600 ~/.ssh/authorized_keys

# Exit and reconnect as bensley user
exit
exit
ssh bensley@your-server-ip

# Disable root login (optional but recommended)
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd
```

### Step 3: Install Dependencies

The setup script handles this, but here's what it installs:

```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Caddy (reverse proxy)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy -y

# SQLite and utilities
sudo apt install sqlite3 git build-essential -y
```

### Step 4: Clone and Configure

```bash
# Clone repository
cd /home/bensley
git clone https://github.com/your-org/bensley-operating-system.git
cd bensley-operating-system

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend
npm ci --production
npm run build
cd ..
```

### Step 5: Environment Configuration

#### Backend (.env)

```bash
cp .env.example .env
nano .env
```

Required production values:

```env
# Database
DATABASE_PATH=/home/bensley/bensley-operating-system/database/bensley_master.db

# API
API_HOST=127.0.0.1
API_PORT=8000
CORS_ORIGINS=https://your-domain.com

# Production mode
DEBUG=false

# Email sync (optional - configure when ready)
# EMAIL_SERVER=tmail.bensley.com
# EMAIL_PORT=993
# EMAIL_ACCOUNTS=[{"email":"lukas@bensley.com","password":"xxx"}]
# MAX_EMAILS_PER_RUN=100

# AI queries (optional)
# OPENAI_API_KEY=sk-...
```

#### Frontend (frontend/.env.local)

```bash
cp frontend/.env.example frontend/.env.local
nano frontend/.env.local
```

Required production values:

```env
# API URL (backend on same server, proxied through Caddy)
NEXT_PUBLIC_API_BASE_URL=https://your-domain.com

# NextAuth
AUTH_SECRET=generate-a-secure-random-string-here
AUTH_URL=https://your-domain.com
```

Generate a secure AUTH_SECRET:
```bash
openssl rand -base64 32
```

### Step 6: Configure Caddy (HTTPS)

```bash
sudo nano /etc/caddy/Caddyfile
```

See `docs/deployment/https-setup.md` for Caddyfile configuration.

### Step 7: Configure Systemd Services

```bash
# Copy service files
sudo cp systemd/bensley-backend.service /etc/systemd/system/
sudo cp systemd/bensley-frontend.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable bensley-backend
sudo systemctl enable bensley-frontend

# Start services
sudo systemctl start bensley-backend
sudo systemctl start bensley-frontend

# Check status
sudo systemctl status bensley-backend
sudo systemctl status bensley-frontend
```

### Step 8: Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443

# Enable firewall
sudo ufw enable

# Verify
sudo ufw status
```

### Step 9: Database Migration (if existing data)

If migrating from a development machine:

```bash
# On development machine
scp database/bensley_master.db bensley@your-server-ip:/home/bensley/bensley-operating-system/database/

# On server - verify
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM proposals;"
```

## Verification

After deployment, verify everything works:

```bash
# Check services
sudo systemctl status bensley-backend
sudo systemctl status bensley-frontend
sudo systemctl status caddy

# Check logs
sudo journalctl -u bensley-backend -f
sudo journalctl -u bensley-frontend -f

# Test API
curl https://your-domain.com/api/health

# Test frontend
curl -I https://your-domain.com
```

## Ongoing Operations

### Viewing Logs

```bash
# Backend logs
sudo journalctl -u bensley-backend -n 100 -f

# Frontend logs
sudo journalctl -u bensley-frontend -n 100 -f

# Caddy logs
sudo journalctl -u caddy -n 100 -f
```

### Restarting Services

```bash
sudo systemctl restart bensley-backend
sudo systemctl restart bensley-frontend
```

### Deploying Updates

```bash
cd /home/bensley/bensley-operating-system
bash scripts/deploy/deploy.sh
```

### Database Backups

Set up automated backups:

```bash
# Add to crontab (daily backup at 2 AM)
crontab -e

# Add this line:
0 2 * * * /home/bensley/bensley-operating-system/scripts/deploy/backup-db.sh
```

### Rollback

If a deployment fails:

```bash
bash scripts/deploy/rollback.sh
```

## Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u bensley-backend -n 50

# Common issues:
# - Missing .env file
# - Python dependencies not installed
# - Database path incorrect
# - Port already in use

# Test manually
cd /home/bensley/bensley-operating-system
source venv/bin/activate
python -c "import backend.api.main"
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

### Frontend won't start

```bash
# Check logs
sudo journalctl -u bensley-frontend -n 50

# Common issues:
# - Missing .env.local
# - Build failed (run npm run build again)
# - Port conflict

# Test manually
cd /home/bensley/bensley-operating-system/frontend
npm run start
```

### HTTPS not working

```bash
# Check Caddy logs
sudo journalctl -u caddy -n 50

# Verify DNS points to server
dig your-domain.com

# Check Caddyfile syntax
caddy validate --config /etc/caddy/Caddyfile
```

### Database errors

```bash
# Check permissions
ls -la database/bensley_master.db

# Should be owned by bensley user
sudo chown bensley:bensley database/bensley_master.db

# Check integrity
sqlite3 database/bensley_master.db "PRAGMA integrity_check;"
```

## Security Checklist

- [ ] SSH key authentication enabled
- [ ] Root login disabled
- [ ] Firewall configured (UFW)
- [ ] HTTPS configured via Caddy
- [ ] Strong AUTH_SECRET generated
- [ ] Non-root user for services
- [ ] Regular backups configured
- [ ] Database not exposed to internet

## Next Steps

After initial deployment:

1. **Configure Email Sync** - Add email credentials to .env
2. **Set Up Monitoring** - Consider UptimeRobot or similar
3. **Configure Backups** - Automate database backups to offsite storage
4. **Plan PostgreSQL Migration** - When data volume increases

## Related Documentation

- [HTTPS Setup Guide](./https-setup.md) - Detailed Caddy/TLS configuration
- [Architecture Overview](../ARCHITECTURE.md) - System design
- [Roadmap](../ROADMAP.md) - Future plans
