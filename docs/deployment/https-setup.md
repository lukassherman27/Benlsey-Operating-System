# HTTPS/TLS Configuration Guide

This guide covers setting up HTTPS for the Bensley Operations Platform using Caddy.

## Why Caddy?

Caddy is recommended because:
- **Automatic HTTPS** - Obtains and renews Let's Encrypt certificates automatically
- **Simple Configuration** - Much simpler than Nginx + Certbot
- **Modern Defaults** - TLS 1.3, HSTS headers, secure by default
- **Zero Downtime** - Hot config reload without dropping connections

## Quick Setup

### 1. Install Caddy

```bash
# Ubuntu/Debian
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### 2. Configure DNS

Before Caddy can obtain certificates, your domain must point to the server:

```bash
# Verify DNS
dig your-domain.com +short
# Should return your server IP

# Or use nslookup
nslookup your-domain.com
```

### 3. Configure Caddyfile

```bash
# Copy the Caddyfile from the repository
sudo cp /home/bensley/bensley-operating-system/Caddyfile /etc/caddy/Caddyfile

# Edit with your domain
sudo nano /etc/caddy/Caddyfile
# Replace 'your-domain.com' with your actual domain
```

### 4. Create Log Directory

```bash
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy
```

### 5. Start Caddy

```bash
# Validate configuration
sudo caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy
sudo systemctl reload caddy

# Check status
sudo systemctl status caddy
```

### 6. Verify HTTPS

```bash
# Test HTTPS
curl -I https://your-domain.com

# Should return 200 OK and security headers

# Test certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null 2>/dev/null | openssl x509 -text | grep -A2 "Validity"
```

## Caddyfile Reference

### Basic Configuration

```caddyfile
your-domain.com {
    # API routes -> Backend
    handle /api/* {
        reverse_proxy localhost:8000
    }

    # Everything else -> Frontend
    handle {
        reverse_proxy localhost:3000
    }
}
```

### With Security Headers (Recommended)

```caddyfile
your-domain.com {
    # HSTS - Force HTTPS
    header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"

    # Prevent MIME sniffing
    header X-Content-Type-Options "nosniff"

    # Prevent clickjacking
    header X-Frame-Options "DENY"

    # Control referrer information
    header Referrer-Policy "strict-origin-when-cross-origin"

    # Routes...
    handle /api/* {
        reverse_proxy localhost:8000
    }
    handle {
        reverse_proxy localhost:3000
    }
}
```

### With Health Checks

```caddyfile
your-domain.com {
    handle /api/* {
        reverse_proxy localhost:8000 {
            health_uri /api/health
            health_interval 30s
            health_timeout 5s
            # Remove unhealthy backends from rotation
            fail_duration 30s
        }
    }

    handle {
        reverse_proxy localhost:3000 {
            health_uri /
            health_interval 30s
            health_timeout 5s
        }
    }
}
```

### With Rate Limiting (Optional)

```caddyfile
{
    order rate_limit before basicauth
}

your-domain.com {
    # Rate limit API endpoints
    rate_limit {
        zone api {
            match {
                path /api/*
            }
            key {remote_host}
            events 100
            window 1m
        }
    }

    # Routes...
}
```

## Development/Local HTTPS

For local development with self-signed certificates:

```caddyfile
# Local development Caddyfile
localhost:3443 {
    tls internal  # Use self-signed cert

    handle /api/* {
        reverse_proxy localhost:8000
    }
    handle {
        reverse_proxy localhost:3002
    }
}
```

Run locally:
```bash
caddy run --config Caddyfile.local
```

## Certificate Management

Caddy handles certificates automatically, but here are useful commands:

```bash
# View certificates
sudo caddy cert list

# Force certificate renewal
sudo caddy reload --config /etc/caddy/Caddyfile

# View certificate details
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null 2>/dev/null | openssl x509 -text -noout

# Check certificate expiry
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null 2>/dev/null | openssl x509 -enddate -noout
```

## Troubleshooting

### Certificate Not Obtained

```bash
# Check Caddy logs
sudo journalctl -u caddy -n 50

# Common issues:
# - DNS not pointing to server
# - Port 80/443 blocked by firewall
# - Rate limited by Let's Encrypt

# Verify ports are open
sudo netstat -tlnp | grep -E ':(80|443)'
sudo ufw status
```

### 502 Bad Gateway

```bash
# Backend not running
sudo systemctl status bensley-backend

# Check backend is listening
curl http://localhost:8000/api/health
```

### 504 Gateway Timeout

```bash
# Backend taking too long
# Check backend logs
sudo journalctl -u bensley-backend -n 50

# Consider increasing timeout in Caddyfile
reverse_proxy localhost:8000 {
    transport http {
        response_header_timeout 60s
    }
}
```

### CORS Errors

If you see CORS errors in browser console:

1. Check `CORS_ORIGINS` in `.env` includes your domain:
   ```env
   CORS_ORIGINS=https://your-domain.com
   ```

2. Restart backend:
   ```bash
   sudo systemctl restart bensley-backend
   ```

## Security Considerations

### TLS Version

Caddy uses TLS 1.2+ by default. To enforce TLS 1.3 only:

```caddyfile
your-domain.com {
    tls {
        protocols tls1.3
    }
    # ...
}
```

### HSTS Preload

To submit to the HSTS preload list:

1. Ensure HSTS header includes `preload`:
   ```
   Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
   ```

2. Submit at https://hstspreload.org/

### Content Security Policy (Optional)

Add if needed for extra security:

```caddyfile
header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
```

## Alternative: Cloudflare Tunnel

If you can't open ports 80/443 or want DDoS protection:

```bash
# Install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create bensley

# Configure
cat > ~/.cloudflared/config.yml <<EOF
tunnel: your-tunnel-id
credentials-file: /home/bensley/.cloudflared/your-tunnel-id.json

ingress:
  - hostname: your-domain.com
    path: /api/*
    service: http://localhost:8000
  - hostname: your-domain.com
    service: http://localhost:3000
  - service: http_status:404
EOF

# Run as service
sudo cloudflared service install
sudo systemctl start cloudflared
```

## Related Documentation

- [Production Deployment Guide](./production-guide.md)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [Let's Encrypt Rate Limits](https://letsencrypt.org/docs/rate-limits/)
