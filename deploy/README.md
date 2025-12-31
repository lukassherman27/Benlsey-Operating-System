# Bensley Operations Platform - Production Deployment Guide

This directory contains configuration files for deploying the Bensley Operations Platform with HTTPS/TLS.

## Architecture Overview

```
                    ┌─────────────────────────────────────────┐
                    │              Nginx (443/80)             │
                    │         - SSL Termination               │
                    │         - Rate Limiting                 │
                    │         - Static File Caching           │
                    └─────────────┬───────────────────────────┘
                                  │
                    ┌─────────────┴───────────────┐
                    │                             │
              ┌─────▼─────┐                 ┌─────▼─────┐
              │  FastAPI  │                 │  Next.js  │
              │   :8000   │                 │   :3002   │
              │  /api/*   │                 │    /*     │
              └───────────┘                 └───────────┘
```

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Nginx 1.18+
- OpenSSL 1.1.1+ (for TLS 1.3 support)
- Certbot (for Let's Encrypt certificates)
- Python 3.10+ (for FastAPI backend)
- Node.js 18+ (for Next.js frontend)

## Quick Start

### 1. Install Nginx and Certbot

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# Verify installation
nginx -v
certbot --version
```

### 2. Obtain SSL Certificates with Let's Encrypt

```bash
# Stop nginx temporarily
sudo systemctl stop nginx

# Obtain certificate (standalone mode)
sudo certbot certonly --standalone -d bensley.example.com -d www.bensley.example.com

# Or use nginx plugin (nginx must be running with basic config)
sudo certbot --nginx -d bensley.example.com -d www.bensley.example.com

# Certificates will be saved to:
# /etc/letsencrypt/live/bensley.example.com/fullchain.pem
# /etc/letsencrypt/live/bensley.example.com/privkey.pem
# /etc/letsencrypt/live/bensley.example.com/chain.pem
```

### 3. Generate DH Parameters

```bash
# This takes 5-10 minutes
sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 4096
```

### 4. Install Nginx Configuration

```bash
# Backup existing nginx config
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Copy configuration files
sudo cp deploy/nginx/nginx.conf /etc/nginx/nginx.conf
sudo cp deploy/nginx/ssl.conf /etc/nginx/ssl.conf
sudo mkdir -p /etc/nginx/sites-enabled
sudo cp deploy/nginx/sites/bensley.conf /etc/nginx/sites-enabled/bensley.conf

# Update domain name in site config
sudo sed -i 's/bensley.example.com/YOUR_ACTUAL_DOMAIN/g' /etc/nginx/sites-enabled/bensley.conf

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 5. Set Up Certificate Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot installs a systemd timer automatically
# Verify it's active:
sudo systemctl status certbot.timer
```

## Configuration Files

| File | Purpose |
|------|---------|
| `nginx/nginx.conf` | Main nginx configuration with upstreams |
| `nginx/ssl.conf` | SSL/TLS settings (TLS 1.2+, modern ciphers) |
| `nginx/sites/bensley.conf` | Site-specific server blocks |

## Environment Variables

Create a `.env` file in the project root with these production values:

```bash
# Database
DATABASE_URL=sqlite:///./database/bensley_master.db

# Microsoft Graph API (for email sync)
MS_CLIENT_ID=your_client_id
MS_CLIENT_SECRET=your_client_secret
MS_TENANT_ID=your_tenant_id

# OpenAI (if using AI features)
OPENAI_API_KEY=your_openai_key

# Application
ENV=production
DEBUG=false
ALLOWED_HOSTS=bensley.example.com,www.bensley.example.com

# CORS (frontend origin)
CORS_ORIGINS=https://bensley.example.com,https://www.bensley.example.com
```

## Running the Services

### Backend (FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Production server with gunicorn
pip install gunicorn uvicorn[standard]
gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile - \
    --error-logfile -
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Start production server
npm start  # Runs on port 3002
```

## Using Docker (Optional)

See `docker-compose.prod.yml` for a containerized deployment:

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## Security Checklist

- [ ] SSL certificates installed and valid
- [ ] DH parameters generated (4096-bit)
- [ ] Firewall configured (only 80/443 open)
- [ ] SSH hardened (key-only, non-default port)
- [ ] Fail2ban installed for brute-force protection
- [ ] Environment variables secured (not in version control)
- [ ] Database backed up regularly
- [ ] Rate limiting configured in nginx
- [ ] HSTS enabled (included in ssl.conf)
- [ ] Security headers configured

## Troubleshooting

### Certificate Issues

```bash
# Check certificate expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Check nginx SSL config
openssl s_client -connect bensley.example.com:443 -servername bensley.example.com
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/bensley.error.log

# Reload after config changes
sudo systemctl reload nginx
```

### Backend Connection Issues

```bash
# Check if backend is running
curl http://127.0.0.1:8000/api/health

# Check backend logs
journalctl -u bensley-backend -f  # if using systemd

# Verify upstream in nginx
nginx -T | grep backend_api
```

### Frontend Connection Issues

```bash
# Check if frontend is running
curl http://127.0.0.1:3002

# Check frontend logs
pm2 logs frontend  # if using PM2
```

## SSL Test

After deployment, verify your SSL configuration:

- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/) - Aim for A+ rating
- [Security Headers](https://securityheaders.com/) - Check security headers

## Maintenance

### Certificate Renewal

Certificates auto-renew via certbot's systemd timer. Verify:

```bash
# Check timer status
sudo systemctl list-timers | grep certbot

# Manual renewal test
sudo certbot renew --dry-run
```

### Log Rotation

Nginx logs are rotated automatically by logrotate. Check config:

```bash
cat /etc/logrotate.d/nginx
```

## Support

For issues with this deployment:
1. Check the troubleshooting section above
2. Review nginx and application logs
3. Create a GitHub issue with error messages
