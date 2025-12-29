# Deployment Guide

This guide explains how to deploy WhatsNext for production use, including the architecture decisions and different deployment strategies.

## Architecture Overview

Before diving into deployment, let's understand how WhatsNext is structured:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Your Infrastructure                             │
│                                                                              │
│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────────────────┐ │
│  │   Clients    │     │  WhatsNext API   │     │      PostgreSQL          │ │
│  │              │     │     Server       │     │       Database           │ │
│  │ - Python     │────>│                  │────>│                          │ │
│  │ - CLI        │     │ (FastAPI/uvicorn)│     │  - Jobs                  │ │
│  │ - Workers    │<────│                  │<────│  - Projects              │ │
│  │              │     │                  │     │  - Tasks                 │ │
│  └──────────────┘     └──────────────────┘     │  - Clients               │ │
│                               │                 └──────────────────────────┘ │
│                               │                                              │
│                        ┌──────▼──────┐                                       │
│                        │   nginx     │ (optional, for HTTPS)                 │
│                        └─────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | What It Does | Technology |
|-----------|--------------|------------|
| **API Server** | Handles all HTTP requests for job management | Python + FastAPI + uvicorn |
| **Database** | Stores all job data persistently | PostgreSQL |
| **Workers** | Fetch and execute jobs from the queue | Python (your code) |
| **CLI/Clients** | Submit jobs and interact with the API | Python library or CLI |

### What Gets Deployed Where?

WhatsNext is **not** a single Docker container that runs everything. Instead, it follows a **client-server architecture**:

1. **The Server** (API + Database) runs centrally - this is what you deploy
2. **Workers** run on your compute nodes (GPU servers, HPC clusters, etc.)
3. **Clients** run wherever you submit jobs from (your laptop, CI/CD, etc.)

This separation is intentional:

- **Workers can be anywhere** - your lab's GPU server, a SLURM cluster, cloud VMs
- **The server is the single source of truth** - all job state lives in PostgreSQL
- **Network requirements are minimal** - workers only need HTTP access to the API

## Deployment Strategies

Choose the right strategy for your situation:

| Strategy | Best For | Complexity | When to Use |
|----------|----------|------------|-------------|
| [Docker Compose](#docker-compose-recommended) | Most users | Low | Starting out, small teams, single server |
| [systemd + nginx](#systemd-with-nginx) | Production Linux | Medium | When you need more control, existing servers |
| [Kubernetes/Helm](#kubernetes) | Large scale | High | Cloud-native environments, auto-scaling |
| [Manual](#manual-installation) | Learning/debugging | Low | Understanding internals, development |

## Docker Compose (Recommended)

Docker Compose bundles the API server and PostgreSQL into a single deployment that's easy to manage.

### What's Included

```
docker-compose.yml
├── db service      → PostgreSQL database
└── api service     → WhatsNext API server
```

!!! note "Workers are NOT in Docker Compose"
    Workers run separately on your compute nodes. They connect to the API over HTTP.

### Step 1: Create the Configuration

Create a directory for your deployment:

```bash
mkdir whatsnext-server
cd whatsnext-server
```

Create `docker-compose.yml`:

```yaml title="docker-compose.yml"
version: '3.8'

services:
  # PostgreSQL database - stores all job data
  db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_USER: whatsnext
      POSTGRES_PASSWORD: change_this_password  # CHANGE THIS!
      POSTGRES_DB: whatsnext
    volumes:
      # Persist data across container restarts
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U whatsnext"]
      interval: 5s
      timeout: 5s
      retries: 5

  # WhatsNext API server
  api:
    image: python:3.12-slim
    restart: always
    depends_on:
      db:
        condition: service_healthy
    environment:
      # Database connection (uses Docker's internal DNS)
      database_hostname: db
      database_port: 5432
      database_user: whatsnext
      database_password: change_this_password  # CHANGE THIS!
      database_name: whatsnext

      # Security settings (optional but recommended)
      api_keys: your-secure-api-key-here  # Generate with: openssl rand -base64 24
      rate_limit_per_minute: 100
    ports:
      - "8000:8000"  # Expose API on host port 8000
    command: >
      bash -c "pip install whatsnext[server] &&
               uvicorn whatsnext.api.server.main:app --host 0.0.0.0 --port 8000"

volumes:
  postgres_data:  # Named volume for database persistence
```

### Step 2: Start the Server

```bash
# Start in the background
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### Step 3: Verify It's Working

```bash
# Check the API is responding
curl http://localhost:8000/

# Check database connection
curl http://localhost:8000/checkdb

# View API documentation
open http://localhost:8000/docs
```

### Step 4: Connect Workers

Now that your server is running, workers can connect from anywhere with network access:

```bash
# On your worker machine
pip install whatsnext[cli]

# Test connection
whatsnext status --server your-server-ip --port 8000

# Start a worker
whatsnext worker --server your-server-ip --port 8000 --project my-project
```

### Updating the Server

```bash
# Pull latest and restart
docker-compose pull
docker-compose up -d
```

### Backing Up

```bash
# Backup database
docker-compose exec db pg_dump -U whatsnext whatsnext > backup.sql

# Restore database
docker-compose exec -T db psql -U whatsnext whatsnext < backup.sql
```

---

## systemd with nginx

For production Linux servers where you want more control, use systemd to manage the WhatsNext service and nginx for HTTPS.

### Architecture

```
                Internet
                    │
                    ▼
            ┌───────────────┐
            │     nginx     │  ← Handles HTTPS, SSL termination
            │  (port 443)   │
            └───────┬───────┘
                    │ (localhost:8000)
                    ▼
            ┌───────────────┐
            │   WhatsNext   │  ← Your application
            │  (uvicorn)    │
            │  (port 8000)  │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │  PostgreSQL   │  ← Database
            │  (port 5432)  │
            └───────────────┘
```

### Step 1: Install PostgreSQL

=== "Ubuntu/Debian"

    ```bash
    # Install PostgreSQL
    sudo apt update
    sudo apt install postgresql postgresql-contrib

    # Start and enable
    sudo systemctl start postgresql
    sudo systemctl enable postgresql

    # Create database and user
    sudo -u postgres psql <<EOF
    CREATE USER whatsnext WITH PASSWORD 'your_secure_password';
    CREATE DATABASE whatsnext OWNER whatsnext;
    GRANT ALL PRIVILEGES ON DATABASE whatsnext TO whatsnext;
    EOF
    ```

=== "CentOS/RHEL"

    ```bash
    # Install PostgreSQL
    sudo dnf install postgresql-server postgresql-contrib

    # Initialize database
    sudo postgresql-setup --initdb

    # Start and enable
    sudo systemctl start postgresql
    sudo systemctl enable postgresql

    # Create database and user
    sudo -u postgres psql <<EOF
    CREATE USER whatsnext WITH PASSWORD 'your_secure_password';
    CREATE DATABASE whatsnext OWNER whatsnext;
    GRANT ALL PRIVILEGES ON DATABASE whatsnext TO whatsnext;
    EOF
    ```

=== "macOS (Homebrew)"

    ```bash
    # Install PostgreSQL
    brew install postgresql@16
    brew services start postgresql@16

    # Create database and user
    psql postgres <<EOF
    CREATE USER whatsnext WITH PASSWORD 'your_secure_password';
    CREATE DATABASE whatsnext OWNER whatsnext;
    GRANT ALL PRIVILEGES ON DATABASE whatsnext TO whatsnext;
    EOF
    ```

### Step 2: Install WhatsNext

```bash
# Create a dedicated user (no login shell for security)
sudo useradd -r -s /bin/false whatsnext

# Create installation directory
sudo mkdir -p /opt/whatsnext
sudo chown whatsnext:whatsnext /opt/whatsnext

# Create virtual environment
sudo -u whatsnext python3 -m venv /opt/whatsnext/venv

# Install WhatsNext
sudo -u whatsnext /opt/whatsnext/venv/bin/pip install whatsnext[server]
```

### Step 3: Configure WhatsNext

Create the environment file:

```bash title="/opt/whatsnext/.env"
# Database connection
database_hostname=localhost
database_port=5432
database_user=whatsnext
database_password=your_secure_password
database_name=whatsnext

# Security (generate with: openssl rand -base64 24)
api_keys=your-production-api-key-here

# CORS (restrict to your domain)
cors_origins=https://yourdomain.com

# Rate limiting
rate_limit_per_minute=100
```

Secure the file:

```bash
sudo chown whatsnext:whatsnext /opt/whatsnext/.env
sudo chmod 600 /opt/whatsnext/.env
```

### Step 4: Create systemd Service

```ini title="/etc/systemd/system/whatsnext.service"
[Unit]
Description=WhatsNext Job Queue API Server
Documentation=https://github.com/cemde/WhatsNext
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=whatsnext
Group=whatsnext
WorkingDirectory=/opt/whatsnext
Environment="PATH=/opt/whatsnext/venv/bin"

# The main command
ExecStart=/opt/whatsnext/venv/bin/uvicorn \
    whatsnext.api.server.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4

# Restart on failure
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/whatsnext

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable whatsnext
sudo systemctl start whatsnext

# Check status
sudo systemctl status whatsnext

# View logs
sudo journalctl -u whatsnext -f
```

### Step 5: Set Up nginx with HTTPS

Install nginx and certbot:

```bash
# Ubuntu/Debian
sudo apt install nginx certbot python3-certbot-nginx
```

Create nginx configuration:

```nginx title="/etc/nginx/sites-available/whatsnext"
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates (will be added by certbot)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Proxy to WhatsNext
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable and get certificate:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/whatsnext /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Get SSL certificate (first time - without SSL)
# Temporarily modify the config to not require SSL, then:
sudo certbot --nginx -d api.yourdomain.com

# Restart nginx
sudo systemctl restart nginx
```

---

## Kubernetes

For cloud-native deployments, you can deploy WhatsNext on Kubernetes.

### Basic Kubernetes Deployment

```yaml title="whatsnext-deployment.yaml"
apiVersion: v1
kind: Namespace
metadata:
  name: whatsnext

---
apiVersion: v1
kind: Secret
metadata:
  name: whatsnext-secrets
  namespace: whatsnext
type: Opaque
stringData:
  database_password: "your-secure-password"
  api_keys: "your-api-key"

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: whatsnext-config
  namespace: whatsnext
data:
  database_hostname: "postgres.whatsnext.svc.cluster.local"
  database_port: "5432"
  database_user: "whatsnext"
  database_name: "whatsnext"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whatsnext-api
  namespace: whatsnext
spec:
  replicas: 2
  selector:
    matchLabels:
      app: whatsnext-api
  template:
    metadata:
      labels:
        app: whatsnext-api
    spec:
      containers:
      - name: api
        image: python:3.12-slim
        command: ["bash", "-c"]
        args:
          - |
            pip install whatsnext[server] &&
            uvicorn whatsnext.api.server.main:app --host 0.0.0.0 --port 8000
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: whatsnext-config
        - secretRef:
            name: whatsnext-secrets
        livenessProbe:
          httpGet:
            path: /checkdb
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## Manual Installation

For development or when you want to understand the internals:

```bash
# 1. Create virtual environment
python -m venv whatsnext-env
source whatsnext-env/bin/activate

# 2. Install WhatsNext
pip install whatsnext[server]

# 3. Create .env file
cat > .env << EOF
database_hostname=localhost
database_port=5432
database_user=postgres
database_password=postgres
database_name=whatsnext
EOF

# 4. Start the server
uvicorn whatsnext.api.server.main:app --reload --port 8000
```

---

## Health Checks

WhatsNext provides two health check endpoints:

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /` | Basic connectivity | `{"message": "OK"}` |
| `GET /checkdb` | Database health | `{"message": "DB is working"}` |

Use these for:

- Load balancer health checks
- Container orchestration liveness probes
- Monitoring systems

---

## Scaling

### Vertical Scaling (Bigger Server)

Increase uvicorn workers:

```bash
# Rule of thumb: workers = (2 × CPU cores) + 1
uvicorn whatsnext.api.server.main:app --workers 9
```

### Horizontal Scaling (More Servers)

Run multiple API server instances behind a load balancer:

```
                 ┌─────────────────┐
                 │  Load Balancer  │
                 └────────┬────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │ API #1  │       │ API #2  │       │ API #3  │
   └────┬────┘       └────┬────┘       └────┬────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                   ┌──────▼──────┐
                   │ PostgreSQL  │
                   └─────────────┘
```

All instances share the same PostgreSQL database - this is safe because:

- PostgreSQL handles concurrent writes with transactions
- Job fetching uses `FOR UPDATE SKIP LOCKED` to prevent double-processing

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u whatsnext -n 100 --no-pager

# Common issues:
# - Wrong database credentials in .env
# - PostgreSQL not running
# - Port already in use
```

### Connection Refused

```bash
# Verify server is listening
curl http://localhost:8000/

# Check firewall
sudo ufw status

# Verify nginx configuration
sudo nginx -t
```

### Database Connection Failed

```bash
# Test database connectivity
psql -h localhost -U whatsnext -d whatsnext

# Check PostgreSQL is running
pg_isready -h localhost -p 5432
```
