#!/bin/bash
#
# Bensley Operations Platform - SSL Initialization Script
#
# This script helps with initial SSL certificate setup using Let's Encrypt.
# Run this on a fresh server before starting the full production stack.
#
# Usage:
#   ./init-ssl.sh YOUR_DOMAIN YOUR_EMAIL
#
# Example:
#   ./init-ssl.sh bensley.example.com admin@bensley.example.com
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo -e "${RED}Error: Missing arguments${NC}"
    echo "Usage: $0 DOMAIN EMAIL"
    echo "Example: $0 bensley.example.com admin@bensley.example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Bensley SSL Initialization${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Create directories
echo -e "${YELLOW}Creating certificate directories...${NC}"
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Generate DH parameters if not exists
if [ ! -f "./certbot/conf/ssl-dhparams.pem" ]; then
    echo -e "${YELLOW}Generating DH parameters (this takes a few minutes)...${NC}"
    openssl dhparam -out ./certbot/conf/ssl-dhparams.pem 2048
    echo -e "${GREEN}DH parameters generated.${NC}"
else
    echo -e "${GREEN}DH parameters already exist.${NC}"
fi

# Create temporary nginx config for certificate validation
echo -e "${YELLOW}Creating temporary nginx config...${NC}"
cat > ./nginx/sites/bensley-temp.conf << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'Bensley SSL initialization in progress...';
        add_header Content-Type text/plain;
    }
}
EOF

# Start nginx only
echo -e "${YELLOW}Starting nginx for certificate validation...${NC}"
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx to start
sleep 5

# Request certificate
echo -e "${YELLOW}Requesting SSL certificate from Let's Encrypt...${NC}"
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email

# Check if certificate was obtained
if [ -f "./certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${GREEN}Certificate obtained successfully!${NC}"

    # Remove temporary config
    rm -f ./nginx/sites/bensley-temp.conf

    # Update the main config with the actual domain
    echo -e "${YELLOW}Updating nginx config with domain...${NC}"
    sed -i "s/bensley.example.com/$DOMAIN/g" ./nginx/sites/bensley.conf

    # Restart nginx with full config
    echo -e "${YELLOW}Restarting nginx with SSL...${NC}"
    docker-compose -f docker-compose.prod.yml restart nginx

    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}SSL Setup Complete!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo "Your site should now be accessible at:"
    echo "  https://$DOMAIN"
    echo ""
    echo "Next steps:"
    echo "  1. Start all services: docker-compose -f docker-compose.prod.yml up -d"
    echo "  2. Set up auto-renewal cron job:"
    echo "     0 12 * * * cd $(pwd) && docker-compose -f docker-compose.prod.yml run --rm certbot renew --quiet"
    echo ""
else
    echo -e "${RED}Certificate was not obtained. Check the output above for errors.${NC}"
    exit 1
fi
