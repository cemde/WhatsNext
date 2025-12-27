# Deployment Guide

This guide covers deploying WhatsNext for production use.

## Deployment Options

| Method | Best For | Difficulty |
|--------|----------|------------|
| [systemd](#systemd-deployment) | Linux servers | Easy |
| [Docker](#docker-deployment) | Container environments | Medium |
| [Docker Compose](#docker-compose) | All-in-one setup | Easy |

## Docker Compose

The fastest way to deploy everything:

```yaml title="docker-compose.yml"
version: '3.8'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: whatsnext
      POSTGRES_PASSWORD: change_this_password
      POSTGRES_DB: whatsnext
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U whatsnext"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    image: python:3.12-slim
    depends_on:
      db:
        condition: service_healthy
    environment:
      database_hostname: db
      database_port: 5432
      database_user: whatsnext
      database_password: change_this_password
      database_name: whatsnext
      api_keys: your-secure-api-key-here
      rate_limit_per_minute: 100
    ports:
      - "8000:8000"
    command: >
      bash -c "pip install whatsnext[server] &&
               uvicorn whatsnext.api.server.main:app --host 0.0.0.0 --port 8000"

volumes:
  postgres_data:
```

Run it:

```bash
docker-compose up -d
```

## systemd Deployment

For production Linux servers, use systemd to manage the WhatsNext service.

### Step 1: Install WhatsNext

```bash
# Create a dedicated user
sudo useradd -r -s /bin/false whatsnext

# Create installation directory
sudo mkdir -p /opt/whatsnext
sudo chown whatsnext:whatsnext /opt/whatsnext

# Create virtual environment
sudo -u whatsnext python3 -m venv /opt/whatsnext/venv

# Install WhatsNext
sudo -u whatsnext /opt/whatsnext/venv/bin/pip install whatsnext[server]
```

### Step 2: Create Configuration

```bash title="/opt/whatsnext/.env"
database_hostname=localhost
database_port=5432
database_user=whatsnext
database_password=your_secure_password
database_name=whatsnext

api_keys=production-api-key-here
cors_origins=https://yourdomain.com
rate_limit_per_minute=100
```

Set permissions:

```bash
sudo chown whatsnext:whatsnext /opt/whatsnext/.env
sudo chmod 600 /opt/whatsnext/.env
```

### Step 3: Create systemd Service

```ini title="/etc/systemd/system/whatsnext.service"
[Unit]
Description=WhatsNext Job Queue API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=whatsnext
Group=whatsnext
WorkingDirectory=/opt/whatsnext
Environment="PATH=/opt/whatsnext/venv/bin"
ExecStart=/opt/whatsnext/venv/bin/uvicorn whatsnext.api.server.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/whatsnext

[Install]
WantedBy=multi-user.target
```

### Step 4: Start the Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable whatsnext
sudo systemctl start whatsnext

# Check status
sudo systemctl status whatsnext
```

### Step 5: View Logs

```bash
# View recent logs
sudo journalctl -u whatsnext -n 50

# Follow logs in real-time
sudo journalctl -u whatsnext -f
```

## HTTPS with Nginx

For production, always use HTTPS. Here's how to set up nginx as a reverse proxy.

### Install nginx and certbot

```bash
# Ubuntu/Debian
sudo apt install nginx certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install nginx certbot python3-certbot-nginx
```

### Create nginx Configuration

```nginx title="/etc/nginx/sites-available/whatsnext"
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for future features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/whatsnext /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Get SSL Certificate

```bash
sudo certbot --nginx -d api.yourdomain.com
```

Certbot will automatically:

1. Obtain a free Let's Encrypt certificate
2. Update nginx configuration for HTTPS
3. Set up automatic renewal

### Final nginx Configuration (after certbot)

```nginx title="/etc/nginx/sites-available/whatsnext"
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker Deployment

### Build Custom Image

```dockerfile title="Dockerfile"
FROM python:3.12-slim

WORKDIR /app

# Install WhatsNext
RUN pip install --no-cache-dir whatsnext[server]

# Create non-root user
RUN useradd -r -s /bin/false appuser
USER appuser

# Run the server
CMD ["uvicorn", "whatsnext.api.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t whatsnext:latest .

docker run -d \
  --name whatsnext \
  -p 8000:8000 \
  -e database_hostname=db.example.com \
  -e database_port=5432 \
  -e database_user=whatsnext \
  -e database_password=secret \
  -e database_name=whatsnext \
  -e api_keys=your-api-key \
  whatsnext:latest
```

## Health Checks

WhatsNext provides two health check endpoints:

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /` | Basic connectivity | `{"message": "OK"}` |
| `GET /checkdb` | Database connection | `{"message": "DB is working"}` |

### Using in Docker

```yaml title="docker-compose.yml (health check section)"
services:
  api:
    ...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/checkdb"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Using with Load Balancers

Configure your load balancer to check `/checkdb`:

- **AWS ALB**: Target group health check path: `/checkdb`
- **nginx**: Use `proxy_pass` with health check module
- **HAProxy**: `option httpchk GET /checkdb`

## Scaling

### Multiple Workers

For a single server, increase workers:

```bash
# In systemd service file or command line
uvicorn whatsnext.api.server.main:app --workers 4
```

**Rule of thumb**: `workers = (2 * CPU cores) + 1`

### Multiple Servers

For high availability, run multiple instances behind a load balancer:

```
                    ┌─────────────┐
                    │ Load        │
                    │ Balancer    │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
    │ Server 1│       │ Server 2│       │ Server 3│
    │ :8000   │       │ :8000   │       │ :8000   │
    └────┬────┘       └────┬────┘       └────┬────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    ┌──────▼──────┐
                    │ PostgreSQL  │
                    │ Database    │
                    └─────────────┘
```

All servers share the same PostgreSQL database.

## Backup and Recovery

### Database Backup

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/whatsnext"
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump -h localhost -U whatsnext whatsnext | gzip > "$BACKUP_DIR/whatsnext_$DATE.sql.gz"

# Keep last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### Database Restore

```bash
# Restore from backup
gunzip -c whatsnext_20240101_120000.sql.gz | psql -h localhost -U whatsnext whatsnext
```

## Monitoring

### Log Aggregation

Forward logs to your monitoring system:

```bash
# systemd journal to syslog
sudo journalctl -u whatsnext -f | logger -t whatsnext
```

### Prometheus Metrics (Future)

Prometheus metrics will be available at `/metrics` in a future release.

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u whatsnext -n 100

# Common issues:
# - Database connection failed: check .env credentials
# - Port already in use: check with `lsof -i :8000`
# - Permission denied: check file ownership
```

### High memory usage

```bash
# Limit workers
uvicorn ... --workers 2

# Or add to systemd service:
MemoryMax=512M
```

### Slow responses

1. Check database queries: enable PostgreSQL slow query log
2. Add more workers: `--workers 8`
3. Scale horizontally: add more servers

### Connection timeouts

```nginx
# Increase nginx timeouts
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```
