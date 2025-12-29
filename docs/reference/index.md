# Reference

Complete reference documentation for WhatsNext.

## Architecture Overview

WhatsNext follows a client-server architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Setup                           │
│                                                             │
│   ┌─────────────────┐          ┌─────────────────────────┐  │
│   │  Client Side    │          │      Server Side        │  │
│   │                 │   HTTP   │                         │  │
│   │  - Python lib   │ ◄──────► │  - REST API (FastAPI)   │  │
│   │  - CLI (wnxt)   │          │  - PostgreSQL database  │  │
│   │  - Workers      │          │                         │  │
│   └─────────────────┘          └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

Choose the documentation you need:

---

## Server Reference

Documentation for running and configuring the WhatsNext server.

| Section | Description |
|---------|-------------|
| [REST API](server/api.md) | HTTP endpoints for all operations |
| [Models](server/models.md) | SQLAlchemy ORM models (database tables) |
| [Schemas](server/schemas.md) | Pydantic request/response schemas |
| [Routers](server/routers.md) | FastAPI endpoint definitions |
| [Database](server/database.md) | Database connection and sessions |
| [Configuration](server/config.md) | Server settings and environment |
| [Main App](server/main.md) | FastAPI application setup |

---

## Client Reference

Documentation for interacting with WhatsNext as a client.

### Python Library

Use the Python library for programmatic access:

| Class | Purpose |
|-------|---------|
| [Server](client/server.md) | Connect to the API and manage projects |
| [Project](client/project.md) | Manage tasks and job queues |
| [Job](client/job.md) | Create and track jobs |
| [Client](client/client.md) | Worker that executes jobs |
| [Formatters](client/formatters.md) | Convert parameters to commands |

### Command Line Interface

Use the CLI for shell scripts and interactive use:

| Command | Purpose |
|---------|---------|
| [CLI Reference](client/cli.md) | Complete CLI command reference |

Quick CLI examples:

```bash
# Check server status
whatsnext status

# List projects
whatsnext projects ls

# Add a job
whatsnext jobs add my-task --param input=data.csv

# Start a worker
whatsnext worker --project my-project --script process.py
```

---

## Common Patterns

### Submitting Jobs (Python)

```python
from whatsnext.api.client import Server, Job

# Connect
server = Server("localhost", 8000)
project = server.get_project("my-project")

# Queue a job
job = Job(
    name="process-data",
    task="data-pipeline",
    parameters={"input": "file.csv", "format": "json"}
)
project.append_queue(job)
```

### Submitting Jobs (CLI)

```bash
whatsnext jobs add data-pipeline \
    --project my-project \
    --name "process-data" \
    --param input=file.csv \
    --param format=json
```

### Running Jobs (Python)

```python
from whatsnext.api.client import Client, CLIFormatter

# Create worker
formatter = CLIFormatter(executable="python", script="process.py")
client = Client(
    entity="team",
    name="worker-1",
    project=project,
    formatter=formatter
)

# Process jobs
client.work()
```

### Running Jobs (CLI)

```bash
whatsnext worker \
    --project my-project \
    --script process.py \
    --entity team \
    --name worker-1
```

---

## Job Dependencies

Jobs can depend on other jobs. A job won't run until all its dependencies complete successfully.

```python
# Job B depends on Job A
job_a = Job(name="job-a", task="step1", parameters={})
project.append_queue(job_a)

job_b = Job(
    name="job-b",
    task="step2",
    parameters={},
    depends={job_a.id: "job-a"}  # Wait for job_a
)
project.append_queue(job_b)
```

The `depends` parameter is a dictionary mapping job IDs to job names. When job A completes, job B becomes eligible for execution.

---

## Resource Requirements

Tasks can specify required resources. Workers only fetch jobs they can handle.

```python
import requests

# Create a task with resource requirements
requests.post("http://localhost:8000/tasks/", json={
    "name": "gpu-training",
    "project_id": 1,
    "required_cpu": 8,
    "required_accelerators": 4
})

# Worker specifies available resources
client = Client(
    ...,
    available_cpu=16,
    available_accelerators=4
)
```
