# Client Installation

This guide walks you through setting up a WhatsNext client. Clients submit jobs and/or run workers to process them.

!!! info "Who is this for?"
    Follow this guide if you want to submit jobs or run workers. You need a WhatsNext server already running (either set up by you or someone else).

## What You Need

| Requirement | Why | Notes |
|-------------|-----|-------|
| **Python 3.10+** | Runs the client library/CLI | Check with `python --version` |
| **Network access to the server** | Clients send HTTP requests | Server IP/hostname and port |
| **API key (maybe)** | If the server requires authentication | Get this from whoever runs the server |

**You do NOT need:**

- PostgreSQL (that's on the server)
- Docker
- Any special ports open on your machine

## Architecture Reminder

```
┌─────────────────────────────────────────────────────────┐
│               CLIENT SIDE (this guide)                   │
│                                                         │
│   ┌───────────────────┐      ┌─────────────────────┐    │
│   │  Python Scripts   │      │     CLI (wnxt)      │    │
│   │  - Submit jobs    │      │  - Quick commands   │    │
│   │  - Run workers    │      │  - Shell scripts    │    │
│   └───────────────────┘      └─────────────────────┘    │
│            │                          │                  │
│            └──────────┬───────────────┘                  │
│                       │ HTTP                             │
└───────────────────────┼─────────────────────────────────┘
                        ▼
            ┌───────────────────┐
            │  WhatsNext Server │
            │  (see Server      │
            │  Installation)    │
            └───────────────────┘
```

## Step 1: Install WhatsNext Client

=== "Using pip"

    ```bash
    # For Python library only
    pip install whatsnext

    # For Python library + CLI
    pip install whatsnext[cli]

    # For everything (recommended)
    pip install whatsnext[all]
    ```

=== "Using uv"

    ```bash
    # Add to existing project
    uv add whatsnext[cli]

    # Or install globally
    uv tool install whatsnext[cli]
    ```

=== "For Development"

    ```bash
    # Clone and install in development mode
    git clone https://github.com/cemde/WhatsNext.git
    cd WhatsNext
    pip install -e .[all]
    ```

## Step 2: Configure Connection

You need to tell the client where the server is. You can do this several ways:

### Option A: Configuration File (Recommended)

Create a `.whatsnext` file in your project directory:

```yaml title=".whatsnext"
server:
  host: 192.168.1.100    # ← CHANGE THIS to your server's IP or hostname
  port: 8000             # ← Change if your server uses a different port
  api_key: abc123secret  # ← Only needed if server requires authentication

project: my-project      # ← Optional: default project for commands
```

| Field | Required? | What to put |
|-------|-----------|-------------|
| `host` | Yes | Server IP (e.g., `192.168.1.100`) or hostname (e.g., `myserver.example.com`) |
| `port` | Yes | Usually `8000` unless server admin says otherwise |
| `api_key` | Maybe | Get from server admin. Leave out if no auth required |
| `project` | No | Convenience: sets default `--project` for CLI commands |

### Option B: Use the CLI

```bash
# Replace with your actual server address
whatsnext init --server 192.168.1.100 --port 8000
```

This creates a `.whatsnext` file interactively.

### Option C: Environment Variables

```bash
# Replace with your actual values
export WHATSNEXT_SERVER=192.168.1.100
export WHATSNEXT_PORT=8000
export WHATSNEXT_API_KEY=your-api-key-here  # only if required
```

### Option D: Command Line Options

Every command accepts `--server` and `--port`:

```bash
# Replace with your actual server address
whatsnext status --server 192.168.1.100 --port 8000
```

This is useful for one-off commands but tedious for repeated use.

## Step 3: Verify Connection

Test that you can reach the server:

=== "Using CLI"

    ```bash
    # Check server status (uses config from .whatsnext)
    whatsnext status

    # Test authentication (if server requires API key)
    whatsnext test-auth

    # List projects
    whatsnext projects ls
    ```

=== "Using Python"

    ```python
    from whatsnext.api.client import Server

    # Connect to server (replace with your actual address)
    server = Server("192.168.1.100", 8000)

    # List projects
    projects = server.get_projects()
    print(f"Found {len(projects)} projects")
    ```

If it works, you'll see something like:

```
WhatsNext Server Status
━━━━━━━━━━━━━━━━━━━━━━━━

Server: http://192.168.1.100:8000
Status: Online

Projects: 0
Connected Clients: 0
```

If it doesn't work, see [Troubleshooting](#troubleshooting) below.

## Step 4: Submit Your First Job

=== "Using CLI"

    ```bash
    # Create a project
    whatsnext projects create my-project --description "My first project"

    # Create a task
    whatsnext tasks create process-data --project my-project

    # Add a job
    whatsnext jobs add process-data \
        --project my-project \
        --name "First job" \
        --param input=data.csv \
        --param output=result.json

    # Check the queue
    whatsnext queue ls --project my-project
    ```

=== "Using Python"

    ```python
    from whatsnext.api.client import Server, Job

    # Connect (replace with your server address)
    server = Server("192.168.1.100", 8000)

    # Create or get project
    project = server.get_project("my-project")
    if project is None:
        project = server.append_project(
            name="my-project",
            description="My first project"
        )

    # Create task (only needed once per task type)
    project.create_task("process-data")

    # Add a job
    job = Job(
        name="First job",
        task="process-data",
        parameters={"input": "data.csv", "output": "result.json"}
    )
    project.append_queue(job)
    print(f"Queued job: {job.name}")
    ```

## Step 5: Run a Worker (Optional)

If this machine will also process jobs:

=== "Using CLI"

    ```bash
    whatsnext worker \
        --project my-project \
        --script your_processing_script.py \
        --entity your-team \
        --name worker-1
    ```

=== "Using Python"

    ```python
    from whatsnext.api.client import Client, CLIFormatter

    # Create formatter for your script
    formatter = CLIFormatter(
        executable="python",
        script="your_processing_script.py"
    )

    # Create worker
    client = Client(
        entity="your-team",
        name="worker-1",
        project=project,
        formatter=formatter
    )

    # Process jobs until queue is empty
    jobs_completed = client.work()
    print(f"Completed {jobs_completed} jobs")
    ```

## What's Next?

Your client is set up! Next steps:

- **[Read the CLI reference](../reference/client/cli.md)** for all available commands
- **[Learn about formatters](formatters.md)** to run jobs on SLURM or RunAI
- **[See the Python API reference](../reference/client/server.md)** for programmatic control

## Troubleshooting

### "Connection refused" error

The server isn't reachable:

```bash
# Test basic connectivity
curl http://your-server-hostname:8000/

# Check hostname resolution
ping your-server-hostname

# Check if port is open
nc -zv your-server-hostname 8000
```

### "401 Unauthorized" error

Authentication is required but not configured:

```bash
# Test with API key
whatsnext test-auth --api-key your-api-key

# Add to config file
echo "  api_key: your-api-key" >> .whatsnext
```

### "Project not found" error

The project doesn't exist yet:

```bash
# List existing projects
whatsnext projects ls

# Create the project
whatsnext projects create my-project
```

### Worker not finding jobs

Check that:

1. Jobs are queued: `whatsnext queue ls --project my-project`
2. Task names match: jobs have a task that exists
3. Worker is using correct project: `--project my-project`

### CLI command not found

The CLI wasn't installed or isn't in PATH:

```bash
# Reinstall with CLI
pip install whatsnext[cli]

# Or use with Python module syntax
python -m whatsnext.cli status
```
