# Deployment Guide

This directory contains example configuration files for deploying WhatsNext.

## Quick Start (Development/Internal Use)

```bash
# Install dependencies
uv sync --all-extras --all-groups

# Run the server
uv run uvicorn whatsnext.api.server.main:app --host 0.0.0.0 --port 8000
```

## Production Deployment

### 1. Set up the service (systemd)

```bash
# Copy and edit the service file
sudo cp whatsnext.service /etc/systemd/system/
sudo nano /etc/systemd/system/whatsnext.service
# Replace YOUR_USERNAME and paths

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable whatsnext
sudo systemctl start whatsnext

# Check status
sudo systemctl status whatsnext
sudo journalctl -u whatsnext -f  # view logs
```

### 2. Set up HTTPS (for external access)

Option A: **Caddy** (simplest, auto-HTTPS)
```bash
sudo apt install caddy
echo "your-domain.com { reverse_proxy localhost:8000 }" | sudo tee /etc/caddy/Caddyfile
sudo systemctl restart caddy
```

Option B: **Nginx + Let's Encrypt**
```bash
# Install
sudo apt install nginx certbot python3-certbot-nginx

# Copy config
sudo cp nginx.conf /etc/nginx/sites-available/whatsnext
sudo ln -s /etc/nginx/sites-available/whatsnext /etc/nginx/sites-enabled/
# Edit server_name in the config

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Restart
sudo systemctl restart nginx
```

### 3. Environment variables

Create `/home/YOUR_USERNAME/WhatsNext/.env`:
```
database_hostname=localhost
database_port=5432
database_user=whatsnext
database_password=your_secure_password
database_name=whatsnext
```

### 4. PostgreSQL setup

```bash
sudo -u postgres psql
```

```sql
CREATE USER whatsnext WITH PASSWORD 'your_secure_password';
CREATE DATABASE whatsnext OWNER whatsnext;
\q
```

## Security Considerations

For external-facing servers:

1. **Use HTTPS** - Never expose HTTP to the internet
2. **Firewall** - Only open ports 80, 443, and SSH
3. **API Authentication** - Coming in Phase 8.3 (not yet implemented)
4. **Database** - Don't expose PostgreSQL externally (bind to localhost)

## Useful Commands

```bash
# Restart after code changes
sudo systemctl restart whatsnext

# View logs
sudo journalctl -u whatsnext -f

# Check if running
curl http://localhost:8000/

# Check nginx config
sudo nginx -t
```
