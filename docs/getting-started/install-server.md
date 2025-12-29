# Server Installation

This guide walks you through setting up a WhatsNext server. The server provides the REST API and stores all job data.

!!! info "Who is this for?"
    You need to follow this guide if you're setting up WhatsNext for the first time. If someone else (e.g., your lab admin) already has a server running, skip to [Client Installation](install-client.md).

## What You Need

| Requirement | Why | Notes |
|-------------|-----|-------|
| **Python 3.10+** | Runs the API server | Check with `python --version` |
| **PostgreSQL 12+** | Stores all job data | Can run in Docker |
| **A machine with a static IP or hostname** | Clients need to reach it | Cloud VM, lab server, or your laptop for testing |

## Understanding the Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      YOUR SERVER MACHINE                          │
│         (Cloud VM, lab server, or your computer)                  │
│                                                                  │
│   ┌───────────────────┐      ┌─────────────────────┐             │
│   │  WhatsNext API    │      │     PostgreSQL      │             │
│   │    (FastAPI)      │◄────►│      Database       │             │
│   │                   │      │                     │             │
│   │  Listens on       │      │  Listens on         │             │
│   │  port 8000        │      │  port 5432          │             │
│   └───────────────────┘      └─────────────────────┘             │
│            ▲                                                      │
│            │ HTTP requests                                        │
└────────────┼─────────────────────────────────────────────────────┘
             │
    Clients connect from anywhere
    (your laptop, GPU cluster, etc.)
```

**Key concept:** The server is just a web API. Clients send HTTP requests to it (like visiting a website). The server stores job information in PostgreSQL.

---

## Step 1: Install PostgreSQL

PostgreSQL is the database that stores your jobs. Choose one option:

=== "Docker (Easiest)"

    If you have Docker installed, this is the simplest approach:

    ```bash
    docker run -d \
        --name whatsnext-db \
        -e POSTGRES_USER=whatsnext \
        -e POSTGRES_PASSWORD=changeme123 \
        -e POSTGRES_DB=whatsnext \
        -p 5432:5432 \
        -v whatsnext_data:/var/lib/postgresql/data \
        --restart unless-stopped \
        postgres:16
    ```

    | Part | What it does | Can I change it? |
    |------|--------------|------------------|
    | `--name whatsnext-db` | Names the container | Yes, use any name |
    | `POSTGRES_PASSWORD=changeme123` | Database password | **Yes, change this!** |
    | `-p 5432:5432` | Makes database accessible | Keep as-is unless port conflicts |
    | `-v whatsnext_data:/...` | Keeps data when container restarts | Keep as-is |
    | `--restart unless-stopped` | Auto-restarts after reboot | Recommended |

    Verify it's running:
    ```bash
    docker ps | grep whatsnext-db
    ```

=== "Ubuntu/Debian"

    ```bash
    # Install PostgreSQL
    sudo apt update
    sudo apt install postgresql postgresql-contrib

    # Start and enable (auto-start on boot)
    sudo systemctl start postgresql
    sudo systemctl enable postgresql

    # Create database and user
    sudo -u postgres psql << EOF
    CREATE USER whatsnext WITH PASSWORD 'changeme123';
    CREATE DATABASE whatsnext OWNER whatsnext;
    GRANT ALL PRIVILEGES ON DATABASE whatsnext TO whatsnext;
    EOF
    ```

    !!! warning "Change the password"
        Replace `changeme123` with a secure password. Remember it for Step 3.

=== "macOS (for local testing)"

    ```bash
    # Install with Homebrew
    brew install postgresql@16
    brew services start postgresql@16

    # Create database (uses your system user, no password needed locally)
    createdb whatsnext
    ```

---

## Step 2: Install WhatsNext

On the same machine where PostgreSQL is running:

```bash
# Create a directory for the server
mkdir whatsnext-server
cd whatsnext-server

# Create a Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install WhatsNext with server components
pip install whatsnext[server]
```

!!! tip "Using uv instead of pip?"
    If you prefer uv (a faster package manager), use:
    ```bash
    uv init
    uv add whatsnext[server]
    ```

---

## Step 3: Configure the Server

Create a file named `.env` in your `whatsnext-server` directory:

```bash title=".env"
# DATABASE CONNECTION (required)
# These must match what you set up in Step 1
database_hostname=localhost
database_port=5432
database_user=whatsnext
database_password=changeme123
database_name=whatsnext

# AUTHENTICATION (optional but recommended)
# If set, clients must provide this key to access the API
# You can have multiple keys, separated by commas
api_keys=my-secret-key-abc123

# RATE LIMITING (optional)
# Limits requests per minute per client (prevents abuse)
rate_limit_per_minute=100
```

### Understanding Each Setting

| Setting | Required? | What it does |
|---------|-----------|--------------|
| `database_hostname` | Yes | Where PostgreSQL is running. Use `localhost` if on same machine |
| `database_port` | Yes | PostgreSQL port (almost always `5432`) |
| `database_user` | Yes | Database username from Step 1 |
| `database_password` | Yes | Database password from Step 1 |
| `database_name` | Yes | Database name from Step 1 |
| `api_keys` | No | If set, clients need this key. Leave empty for open access |
| `rate_limit_per_minute` | No | Prevents one client from overwhelming the server |

### About API Keys

API keys are simple passwords that clients must provide to use your server:

- **You create them** - just make up a random string (e.g., `openssl rand -base64 24`)
- **Share them** with people who should access your server
- **Multiple keys** can be comma-separated: `api_keys=key1,key2,key3`
- **If not set**, anyone who can reach your server can use it

---

## Step 4: Initialize the Database

Before starting the server, create the database tables:

```bash
# Run database migrations
whatsnext db upgrade
```

You should see:
```
Upgrading database to revision: head

INFO  [alembic.runtime.migration] Running upgrade  -> 0001, Initial schema
Database upgraded successfully.
```

!!! tip "For existing databases"
    If your database already has tables (from a previous installation), stamp it instead:
    ```bash
    whatsnext db init --stamp
    ```

## Step 5: Start the Server

Now start the WhatsNext API server:

```bash
# Make sure you're in the whatsnext-server directory with .env file
# and your virtual environment is activated

uvicorn whatsnext.api.server.main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### What `--host 0.0.0.0` means

| Option | What it does | When to use |
|--------|--------------|-------------|
| `--host 127.0.0.1` | Only accessible from this machine | Local testing only |
| `--host 0.0.0.0` | Accessible from other machines | **Use this for remote clients** |
| `--port 8000` | Which port to listen on | Change if 8000 is taken |

!!! danger "Server stops when you close your terminal!"
    If you're connected via SSH and close the connection, the server will stop. See [Keeping the Server Running](#keeping-the-server-running) below.

---

## Step 6: Verify It Works

Test from the server machine:

```bash
# Basic connectivity
curl http://localhost:8000/
# Expected: {"message":"OK"}

# Database connection
curl http://localhost:8000/checkdb
# Expected: {"message":"DB is working"}
```

Test from a client machine (replace with your server's IP or hostname):

```bash
curl http://YOUR_SERVER_IP:8000/
```

Open the API documentation in a browser: `http://YOUR_SERVER_IP:8000/docs`

---

## Keeping the Server Running

By default, the server stops when you close your terminal or SSH session. Here are ways to keep it running:

### Option A: Screen or tmux (Quick & Easy)

Good for testing or temporary use:

```bash
# Start a screen session
screen -S whatsnext

# Start the server (inside screen)
cd whatsnext-server
source .venv/bin/activate
uvicorn whatsnext.api.server.main:app --host 0.0.0.0 --port 8000

# Detach from screen: press Ctrl+A, then D
# The server keeps running!

# To reconnect later:
screen -r whatsnext
```

### Option B: systemd Service (Recommended for Production)

This makes the server start automatically on boot and restart if it crashes:

1. Create the service file:

```bash
sudo nano /etc/systemd/system/whatsnext.service
```

2. Paste this content (adjust paths to match your setup):

```ini title="/etc/systemd/system/whatsnext.service"
[Unit]
Description=WhatsNext Job Queue API
After=network.target postgresql.service

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/whatsnext-server
Environment="PATH=/home/YOUR_USERNAME/whatsnext-server/.venv/bin"
ExecStart=/home/YOUR_USERNAME/whatsnext-server/.venv/bin/uvicorn \
    whatsnext.api.server.main:app \
    --host 0.0.0.0 \
    --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable whatsnext  # Start on boot
sudo systemctl start whatsnext   # Start now

# Check status
sudo systemctl status whatsnext

# View logs
sudo journalctl -u whatsnext -f
```

### Option C: Docker Compose (If Using Docker)

See the [Deployment Guide](deployment.md#docker-compose-recommended) for a complete Docker setup.

---

## Running on a Cloud VM

If your server is on a cloud provider (AWS, GCP, Azure, etc.):

### 1. Open the Firewall

You need to allow incoming connections on port 8000:

| Provider | How to open port |
|----------|-----------------|
| **AWS EC2** | Security Groups → Add inbound rule → TCP 8000 |
| **Google Cloud** | VPC Network → Firewall → Create rule → tcp:8000 |
| **Azure** | Network Security Group → Add inbound rule → Port 8000 |
| **DigitalOcean** | Networking → Firewalls → Add rule |

### 2. Find Your Server's Address

Clients will connect using either:

- **Public IP**: e.g., `203.0.113.42` (find in cloud console)
- **Hostname**: e.g., `myserver.example.com` (if you set up DNS)

### 3. Test from Outside

From your laptop (not the server):

```bash
curl http://YOUR_SERVER_IP:8000/
```

---

## Security Considerations

### For Testing/Development

- API keys optional
- Fine to use `--host 0.0.0.0` on trusted networks

### For Production

| Recommendation | Why |
|----------------|-----|
| **Set `api_keys`** | Prevents unauthorized access |
| **Use HTTPS** | Encrypts traffic (see [Deployment Guide](deployment.md#systemd-with-nginx)) |
| **Firewall rules** | Only allow known client IPs if possible |
| **Strong database password** | Prevents database access if compromised |

---

## Troubleshooting

### "Connection refused" when starting

PostgreSQL isn't running:

```bash
# Docker
docker ps | grep postgres
docker start whatsnext-db

# systemd
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### "Authentication failed" for database

Your `.env` credentials don't match PostgreSQL:

```bash
# Test database connection directly
psql -h localhost -U whatsnext -d whatsnext
# Enter the password from your .env file
```

### Clients can't connect

1. **Check the server is running**: `curl http://localhost:8000/` on the server
2. **Check firewall**: Port 8000 must be open
3. **Check `--host`**: Must be `0.0.0.0`, not `127.0.0.1`
4. **Check IP/hostname**: Clients must use the server's external IP

### Server stops when I close SSH

Use screen, tmux, or systemd. See [Keeping the Server Running](#keeping-the-server-running).

---

## Updating WhatsNext

When updating to a new version:

```bash
# 1. Stop the server
sudo systemctl stop whatsnext  # or Ctrl+C if running manually

# 2. Update the package
pip install --upgrade whatsnext[server]

# 3. Run database migrations
whatsnext db upgrade

# 4. Restart the server
sudo systemctl start whatsnext
```

!!! warning "Always run migrations after updating"
    New versions may include database schema changes. Running `whatsnext db upgrade` applies any pending migrations safely.

---

## Next Steps

Your server is running! Now:

1. **[Set up clients](install-client.md)** on machines that will submit/process jobs
2. **[Configure for production](deployment.md)** with HTTPS and proper process management
