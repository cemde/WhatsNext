# API Reference

Complete reference documentation for WhatsNext.

## Overview

WhatsNext has two main components:

- **Server**: REST API that manages projects, tasks, jobs, and clients
- **Client Library**: Python classes for interacting with the server

## Quick Links

### Client Library

| Class | Purpose |
|-------|---------|
| [Server](client/server.md) | Connect to the API and manage projects |
| [Project](client/project.md) | Manage tasks and job queues |
| [Job](client/job.md) | Create and track jobs |
| [Client](client/client.md) | Worker that executes jobs |
| [Formatters](client/formatters.md) | Convert parameters to commands |

### REST API

| Endpoint Group | Purpose |
|----------------|---------|
| [Projects](server/api.md#projects) | Create, list, update, delete projects |
| [Tasks](server/api.md#tasks) | Define job types with resource requirements |
| [Jobs](server/api.md#jobs) | Queue and manage jobs |
| [Clients](server/api.md#clients) | Register and monitor workers |

### Server Internals

| Module | Purpose |
|--------|---------|
| [Models](server/models.md) | SQLAlchemy ORM models |
| [Schemas](server/schemas.md) | Pydantic request/response schemas |
| [Routers](server/routers.md) | FastAPI endpoint definitions |
| [Database](server/database.md) | Database connection and sessions |
| [Configuration](server/config.md) | Server settings |
| [Main App](server/main.md) | FastAPI application setup |

## Common Patterns

### Submitting Jobs

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

### Running Jobs

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

### Resource Requirements

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
